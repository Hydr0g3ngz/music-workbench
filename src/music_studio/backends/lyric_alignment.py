"""Align supplied text acoustically; never distribute word times uniformly."""

import os
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

from ..audio import load_mono
from ..lyric_models import MODELS, model_path
from ..schema import LyricLine, Lyrics, Word

LANGUAGES = {
    "zh": "Chinese",
    "en": "English",
    "yue": "Cantonese",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "pt": "Portuguese",
    "ru": "Russian",
    "es": "Spanish",
}
_ALIGNERS = {}


def language_name(language: str | None) -> str:
    if language in LANGUAGES:
        return LANGUAGES[language]
    if language and language.lower() in {s.lower() for s in LANGUAGES.values()}:
        return language.title()
    raise ValueError("请为歌词时间对齐指定语言；目前支持中、英、粤、日、韩等11种语言。")


def tokens(text: str) -> list[tuple[str, int, int]]:
    """Character offsets preserve punctuation and spacing in the user's original text."""
    result = []
    left = None
    for index, character in enumerate(text + " "):
        cjk = "\u3400" <= character <= "\u9fff"
        keep = unicodedata.category(character)[0] in "LN" or character in "'’"
        if left is not None and (not keep or cjk):
            result.append((text[left:index].replace("’", "'"), left, index))
            left = None
        if cjk:
            result.append((character, index, index + 1))
        elif keep and left is None:
            left = index
    return [item for item in result if any(c.isalnum() for c in item[0])]


def load_aligner(config):
    if os.environ.get("MUSIC_STUDIO_REUSE_ALIGNER") == "1":
        key = (
            config.get("lyrics_alignment"),
            config["model_dir"],
            config["device"],
            config["offline"],
        )
        if key not in _ALIGNERS:
            _ALIGNERS[key] = _load_aligner(config)
        return _ALIGNERS[key]
    return _load_aligner(config)


def _load_aligner(config):
    if config.get("lyrics_alignment") == "whisper":
        return WhisperTextAligner(config)
    import torch
    from qwen_asr import Qwen3ForcedAligner

    return Qwen3ForcedAligner.from_pretrained(
        model_path("aligner", config),
        dtype=torch.bfloat16 if config["device"] == "cuda" else torch.float32,
        device_map="cuda:0" if config["device"] == "cuda" else "cpu",
        attn_implementation="sdpa",
        local_files_only=True,
    )


class WhisperTextAligner:
    """Cross-attention alignment of supplied text, without re-recognizing it."""

    def __init__(self, config):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(
            "small",
            device=config["device"],
            compute_type="int8_float16" if config["device"] == "cuda" else "int8",
            download_root=str(Path(config["model_dir"]) / "whisper"),
            local_files_only=config["offline"],
            cpu_threads=config["threads"],
            revision="536b0662742c02347bc0e980a01041f333bce120",
        )

    def align(self, *, audio, text, language):
        from types import SimpleNamespace

        from faster_whisper.audio import pad_or_trim
        from faster_whisper.tokenizer import Tokenizer

        waveform, rate = audio
        if rate != 16000 or len(waveform) > 30 * rate:
            raise ValueError("Whisper文字对齐需要不超过30秒的音频区间")
        code = next(key for key, name in LANGUAGES.items() if name == language)
        tokenizer = Tokenizer(
            self.model.hf_tokenizer,
            self.model.model.is_multilingual,
            task="transcribe",
            language=code,
        )
        features = self.model.feature_extractor(waveform)
        encoded = self.model.encode(pad_or_trim(features, 3000))
        out = self.model.find_alignment(
            tokenizer,
            [tokenizer.encode(text)],
            encoded,
            num_frames=[min(3000, round(len(waveform) / 160))],
        )[0]
        result = []
        for word in out:
            pieces = tokens(word["word"])
            if len(pieces) != 1:
                continue
            result.append(
                SimpleNamespace(text=pieces[0][0], start_time=word["start"], end_time=word["end"])
            )
        return [result]


def aligned_lines(
    model,
    audio,
    lines,
    language,
    left,
    right,
    first_word=0,
    native_fallback=False,
    sentence_fallback=False,
):
    duration = len(audio) / 16000
    left, right = max(0, left), min(duration, right)
    if right <= left or right - left > 299:
        raise ValueError("歌词对齐区间应小于5分钟，请检查歌词版本与录音是否一致。")
    per_line = [tokens(line.text) for line in lines]
    flat = [item for items in per_line for item in items]
    if not flat:
        raise ValueError("歌词中没有可以对齐的字词")
    aligned = list(
        model.align(
            audio=(audio[round(left * 16000) : round(right * 16000)], 16000),
            text=" ".join(item[0] for item in flat),
            language=language,
        )[0]
    )
    expected = [t[0].casefold() for t in flat]
    actual = [item.text.casefold() for item in aligned]
    if actual != expected:
        raise ValueError("对齐模型返回的字词与输入不一致，未保存不完整的对齐结果。")
    output = []
    at = 0
    for line, items in zip(lines, per_line, strict=True):
        words = []
        native = []
        for word in line.words:
            pieces = tokens(word.text)
            native.extend(
                [(item[0].casefold(), word if len(pieces) == 1 else None) for item in pieces]
            )
        if [item[0] for item in native] != [item[0].casefold() for item in items]:
            native = []
        used_native = False
        missing = False
        for index, (_, begin, _) in enumerate(items):
            item = aligned[at]
            at += 1
            start, end = (
                float(item.start_time) + left,
                float(item.end_time) + left,
            )
            if np.isfinite(start + end):
                start, end = max(left, start), min(right, end)
            if not np.isfinite(start + end) or end <= start:
                if native_fallback and native and native[index][1] is not None:
                    start, end = native[index][1].start, native[index][1].end
                    used_native = True
                elif sentence_fallback:
                    # An invalid token must not erase other valid acoustic spans.
                    # Retain the complete line text; unknown tokens get no word time.
                    missing = True
                    continue
                else:
                    raise ValueError("对齐模型返回了零长度或无效时间，保留之前的结果。")
            stop = items[index + 1][1] if index + 1 < len(items) else len(line.text)
            # Retain the exact supplied text, including punctuation, in word-level exports.
            text = line.text[0 if index == 0 else begin : stop]
            words.append(Word(id=f"w{first_word:05d}", text=text, start=start, end=end))
            first_word += 1
        if words:
            if any(b.start < a.start for a, b in zip(words, words[1:], strict=False)):
                raise ValueError("对齐时间顺序异常，保留之前的结果。")
            output.append(
                LyricLine(
                    id=line.id,
                    text=line.text,
                    start=min(w.start for w in words),
                    end=max(w.end for w in words),
                    words=words,
                    review_reasons=(
                        (["部分字词保留原时间，请试听核对"] if used_native else [])
                        + (["部分字词尚无可靠时间，灰色文字按句定位"] if missing else [])
                    ),
                )
            )
        elif items:
            raise ValueError("这句歌词无法可靠定位，请核对实际演唱内容。")
    return output, first_word


def align_lyrics(source: Path, lyrics: Lyrics, config: dict) -> Lyrics:
    """Coarse ASR line times guide crops; word times come only from model inference."""
    if config.get("lyrics_alignment") == "anchors":
        from .lyric_anchors import align_anchors

        return align_anchors(source, lyrics, config)
    if not lyrics.segments:
        return lyrics.model_copy(deep=True)
    guide_warning = None
    if config.get("lyrics_alignment") == "whisper" and any(
        not line.words and line.end - line.start > 28 for line in lyrics.segments
    ):
        from .lyrics import transcribe_whisper

        try:
            guide = transcribe_whisper(
                source,
                {
                    **config,
                    "language": config.get("language") or lyrics.language,
                    "asr_model": "small",
                    "asr_revision": "536b0662742c02347bc0e980a01041f333bce120",
                    "asr_segmentation": "whole",
                },
            )
            phrases = []
            for line in lyrics.segments:
                units = tokens(line.text)
                for start in range(0, len(units), 12):
                    begin = units[start][1] if start else 0
                    end = units[start + 12][1] if start + 12 < len(units) else len(line.text)
                    phrases.append(line.text[begin:end].strip())
            guided = reference_lyrics(
                "\n".join(phrases), guide, source_duration(source), pad_seconds=0.75
            )
            if guided.timing_method == "reference_guided_pending_alignment":
                guided.warnings = lyrics.warnings.copy()
                lyrics = guided
                guide_warning = "Whisper small provides acoustic crop hints only; "
                guide_warning += "the stronger recognizer's text was preserved unchanged."
        except (ValueError, RuntimeError):
            guide_warning = "Coarse acoustic guide unavailable; original recognition retained."
    try:
        language = language_name(config.get("language") or lyrics.language)
    except ValueError:
        result = lyrics.model_copy(deep=True)
        result.warnings.append(
            "Independent alignment unavailable for the detected language; "
            "recognition and original timing retained."
        )
        for line in result.segments:
            line.review_reasons.append("当前语言不支持独立对齐，保留原时间")
        return result
    audio = load_mono(source, 16000)
    model = load_aligner(config)
    result = lyrics.model_copy(deep=True)
    if guide_warning:
        result.warnings.append(guide_warning)
    result.segments = []
    first_word = 0
    failed = 0
    for line in lyrics.segments:
        if not tokens(line.text):
            continue
        candidates = [line]
        # Recognition-only backends can return a whole audio chunk as one paragraph.
        # Split display text before one joint acoustic alignment; never align each phrase
        # independently against the same minute of audio (which misplaces repeated words).
        if not line.words and len(tokens(line.text)) > 12:
            units = tokens(line.text)
            candidates = []
            for index, start in enumerate(range(0, len(units), 12)):
                stop = units[start + 12][1] if start + 12 < len(units) else len(line.text)
                begin = units[start][1] if start else 0
                text = line.text[begin:stop].strip()
                candidates.append(
                    LyricLine(id=f"{line.id}-p{index}", text=text, start=line.start, end=line.end)
                )
        try:
            lines, first_word = aligned_lines(
                model,
                audio,
                candidates,
                language,
                line.start - 0.8,
                line.end + 0.8,
                first_word,
                native_fallback=True,
                sentence_fallback=not line.words,
            )
            result.segments.extend(lines)
            failed += sum(bool(item.review_reasons) for item in lines)
        except ValueError:
            # Keep valid native times on difficult melismas instead of silently inventing times.
            fallback = line.model_copy(deep=True)
            for word in fallback.words:
                word.id = f"w{first_word:05d}"
                first_word += 1
            fallback.review_reasons.append("独立对齐未通过校验，保留原时间，请试听核对")
            result.segments.append(fallback)
            failed += 1
    backend = config.get("lyrics_alignment", "qwen")
    result.timing_method = (
        f"{backend}_forced_alignment" if not failed else f"{backend}_with_native_fallback"
    )
    alignment_model = (
        MODELS["aligner"]
        if backend == "qwen"
        else ("Systran/faster-whisper-small", "536b0662742c02347bc0e980a01041f333bce120")
    )
    result.warnings.append(
        f"Alignment: {alignment_model[0]}@{alignment_model[1]}; "
        f"{failed} lines need timing review (partial or original timings). "
        "Singing alignment needs listening verification."
    )
    return Lyrics.model_validate(result.model_dump())


def source_duration(source: Path) -> float:
    import soundfile as sf

    return sf.info(source).duration


def reference_lyrics(text: str, guide: Lyrics, duration: float, pad_seconds=3.0) -> Lyrics:
    """Build coarse windows only; these are never exposed as finished word timestamps."""
    raw = [line.strip() for line in text.splitlines() if line.strip()]
    if not raw or len(raw) > 1000 or len(text) > 50000:
        raise ValueError("请输入1到1000句歌词，总长度最多50000字。")
    if any(not tokens(line) for line in raw):
        raise ValueError("每行应包含歌词文字，请移除仅有标点或符号的行。")
    guide_tokens = []
    guide_times = []
    for line in guide.segments:
        for word in line.words:
            for item in tokens(word.text):
                guide_tokens.append(item[0].casefold())
                guide_times.append((word.start, word.end))
    expected = [item[0].casefold() for line in raw for item in tokens(line)]
    anchors = {}
    for block in SequenceMatcher(
        None, expected, guide_tokens, autojunk=False
    ).get_matching_blocks():
        for i in range(block.size):
            anchors[block.a + i] = guide_times[block.b + i]
    if len(anchors) / max(1, len(expected)) < 0.35:
        if duration <= 240:
            return Lyrics(
                language=guide.language,
                timing_method="reference_pending_alignment",
                segments=[
                    LyricLine(id=f"l{i:04d}", text=line, start=0, end=duration)
                    for i, line in enumerate(raw)
                ],
            )
        raise ValueError("歌词与当前识别匹配不足，无法可靠定位长曲。请检查歌曲版本或先识别歌词。")
    indices = sorted(anchors)
    lines = []
    at = 0
    for i, line in enumerate(raw):
        count = len(tokens(line))
        selected = [anchors[j] for j in range(at, at + count) if j in anchors]
        if selected:
            start, end = min(t[0] for t in selected), max(t[1] for t in selected)
        else:
            before = [j for j in indices if j < at]
            after = [j for j in indices if j >= at + count]
            start = anchors[before[-1]][1] if before else 0
            end = anchors[after[0]][0] if after else duration
        start, end = max(0, start - pad_seconds), min(duration, end + pad_seconds)
        if end <= start or end - start > 240:
            raise ValueError("长曲中有歌词无法定位，请检查漏句、重复副歌和版本差异。")
        lines.append(LyricLine(id=f"l{i:04d}", text=line, start=start, end=end))
        at += count
    return Lyrics(
        language=guide.language, timing_method="reference_guided_pending_alignment", segments=lines
    )


def align_reference(source: Path, lyrics: Lyrics, config: dict) -> Lyrics:
    audio = load_mono(source, 16000)
    guide_notes = []
    language = language_name(config.get("language") or lyrics.language)
    if (
        len(lyrics.segments) > 1
        and lyrics.timing_method != "reference_guided_pending_alignment"
        and all(line.start == 0 for line in lyrics.segments)
    ):
        # When the existing recognizer supplied no usable word anchors, obtain an acoustic
        # coarse guide. The supplied text is still aligned, never replaced by this ASR.
        from .lyrics import transcribe_whisper

        try:
            guide = transcribe_whisper(
                source,
                {
                    **config,
                    "asr_model": "small",
                    "asr_revision": "536b0662742c02347bc0e980a01041f333bce120",
                },
            )
            lyrics = reference_lyrics(
                "\n".join(line.text for line in lyrics.segments), guide, len(audio) / 16000
            )
            guide_notes.append(
                "Coarse acoustic guide: Whisper small@536b0662742c02347bc0e980a01041f333bce120; "
                "the supplied text was preserved."
            )
        except RuntimeError:
            guide_notes.append(
                "Coarse guide unavailable; whole-clip reference alignment attempted."
            )
    model = load_aligner(config)
    if len(audio) / 16000 <= 240 and lyrics.timing_method != "reference_guided_pending_alignment":
        lines, _ = aligned_lines(
            model, audio, lyrics.segments, language, 0, len(audio) / 16000, sentence_fallback=True
        )
    else:
        lines, first_word = [], 0
        for line in lyrics.segments:
            found, first_word = aligned_lines(
                model,
                audio,
                [line],
                language,
                line.start,
                line.end,
                first_word,
                sentence_fallback=True,
            )
            lines.extend(found)
    return Lyrics(
        language=lyrics.language,
        timing_method="qwen_reference_alignment",
        segments=lines,
        warnings=guide_notes
        + ["Text supplied by user; forced alignment does not verify whether words were sung."],
    )
