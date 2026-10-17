from pathlib import Path

import numpy as np

from ..audio import load_mono
from ..inference_cache import inference_model
from ..progress import report_progress
from ..schema import LyricLine, Lyrics, Word


def vocal_regions(audio: np.ndarray, rate=16000) -> list[tuple[int, int]]:
    """Energy-based singing regions, without speech VAD or changing the master clock."""
    import librosa

    regions = librosa.effects.split(audio, top_db=32, frame_length=1024, hop_length=256)
    merged = []
    for start, end in regions:
        left, right = max(0, int(start) - rate // 4), min(len(audio), int(end) + rate // 4)
        if merged and left - merged[-1][1] < rate:
            merged[-1][1] = right
        else:
            merged.append([left, right])
    chunks = []
    for left, right in merged:
        while right - left > 28 * rate:
            # Prefer a quiet boundary with enough context on either side.
            first, last = left + 18 * rate, min(left + 26 * rate, right - 3 * rate)
            rms = librosa.feature.rms(y=audio[first:last], frame_length=1024, hop_length=256)[0]
            cut = first + int(np.argmin(rms)) * 256
            chunks.append((left, cut))
            left = cut
        if right - left >= rate // 4:
            chunks.append((left, right))
    return chunks


def transcribe(source: Path, config: dict) -> Lyrics:
    backend = config.get("asr_backend", "whisper")
    if backend != "whisper":
        from .lyrics_advanced import transcribe_advanced

        return transcribe_advanced(source, config)
    lyrics = transcribe_whisper(source, config)
    if (
        config.get("lyrics_alignment", "native") in ("qwen", "whisper", "anchors")
        and lyrics.segments
    ):
        from .lyric_alignment import align_lyrics

        aligned_source = Path(config.get("_anchor_audio", source))
        lyrics = align_lyrics(aligned_source, lyrics, config)
    return lyrics


def transcribe_whisper(source: Path, config: dict) -> Lyrics:
    import ctranslate2
    from faster_whisper import WhisperModel

    ctranslate2.set_random_seed(config.get("seed", 0))
    audio = load_mono(source, 16000)
    if np.max(np.abs(audio), initial=0) < 1e-5:
        return Lyrics(
            language=config["language"],
            timing_method="whisper_word_timestamps",
            segments=[],
            warnings=["No audible vocal signal; lyrics left empty."],
        )
    device = config["device"]
    precision = "int8_float16" if device == "cuda" else "int8"
    config["_compute_type"] = precision
    key = (
        "whisper",
        config["asr_model"],
        config["asr_revision"],
        config["model_dir"],
        device,
        precision,
        config["threads"],
    )
    model = inference_model(
        key,
        lambda: WhisperModel(
            config["asr_model"],
            device=device,
            compute_type=precision,
            download_root=str(Path(config["model_dir"]) / "whisper"),
            local_files_only=config["offline"],
            cpu_threads=config["threads"],
            revision=config["asr_revision"],
        ),
    )
    regions = (
        vocal_regions(audio) if config.get("asr_segmentation") == "vocal" else [(0, len(audio))]
    )

    def transcribed_segments():
        for left, right in regions:
            segments, info = model.transcribe(
                audio[left:right],
                language=config["language"],
                beam_size=5,
                word_timestamps=True,
                vad_filter=False,
                condition_on_previous_text=False,
                hallucination_silence_threshold=2.0,
            )
            for segment in segments:
                report_progress(
                    config,
                    config.get("_progress_label", "识别歌词"),
                    min(len(audio) / 16000, segment.end + left / 16000),
                    len(audio) / 16000,
                    unit="秒",
                )
                yield segment, left / 16000, right / 16000, info.language

    lines = []
    word_count = 0
    warnings = [
        "Lyrics and word times are automatic estimates; singing may require correction. "
        "Tokens can contain multiple Chinese characters; no fabricated character timings."
    ]
    language = config["language"]
    for segment, offset, chunk_end, detected in transcribed_segments():
        language = language or detected
        start, end = max(offset, segment.start + offset), min(chunk_end, segment.end + offset)
        if end <= start or not segment.text.strip():
            continue
        region = audio[int(start * 16000) : int(end * 16000)]
        if len(region) == 0 or np.sqrt(np.mean(region**2)) < 1e-5:
            continue
        words = []
        for word in segment.words or []:
            ws, we = max(offset, word.start + offset), min(chunk_end, word.end + offset)
            if we <= ws or not word.word.strip():
                continue
            words.append(
                Word(
                    id=f"w{word_count:05d}",
                    text=word.word,
                    start=ws,
                    end=we,
                    score=float(np.clip(word.probability, 0, 1)),
                )
            )
            word_count += 1
        if words:
            start = min(start, min(w.start for w in words))
            end = max(end, max(w.end for w in words))
        lines.append(
            LyricLine(
                id=f"l{len(lines):04d}",
                text=segment.text.strip(),
                start=start,
                end=end,
                words=words,
                review_reasons=(
                    ["部分字词的识别分数偏低，建议试听核对"]
                    if words and sum((w.score or 0) < 0.45 for w in words) / len(words) > 0.25
                    else []
                ),
            )
        )
    return Lyrics(
        language=language,
        timing_method="whisper_word_timestamps",
        segments=lines,
        warnings=warnings,
    )
