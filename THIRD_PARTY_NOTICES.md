# Third-party components and model sources

The optional [Beat This!](https://github.com/CPJKU/beat_this) implementation and authors' checkpoints use MIT terms. small0 is pinned by SHA-256; relevant fold checkpoints use the authors' official-cloud `OC-Checksum` SHA-1 metadata (2026-10-15). Models stay outside Git. small0/final0 training includes GuitarSet, so their diagnostic results do not establish held-out accuracy.

Music Workbench's application code is MIT licensed; shared engine code retains its original attribution. Dependencies and model weights retain their own licenses. Models are downloaded from upstream sources; they are not committed or relicensed by this repository. This list identifies the principal components, not a replacement for their license files or the transitive dependency notices shipped with their packages.

| Component | Use | Upstream license/source |
| --- | --- | --- |
| Demucs 4.0.1 | Vocal/instrumental separation | [MIT, Meta / Alexandre Défossez](https://github.com/facebookresearch/demucs/blob/main/LICENSE) |
| htdemucs / htdemucs_ft | Separation weights | [Official Demucs model documentation](https://github.com/facebookresearch/demucs), downloaded from `dl.fbaipublicfiles.com/demucs/` with upstream hash checks |
| faster-whisper 1.2.1 | Local ASR and word timestamps | [MIT, SYSTRAN](https://github.com/SYSTRAN/faster-whisper/blob/master/LICENSE) |
| CTranslate2 4.6.0 | ASR inference runtime | [MIT, OpenNMT](https://github.com/OpenNMT/CTranslate2/blob/master/LICENSE) |
| Converted Whisper checkpoints | ASR weights | [SYSTRAN model collection](https://huggingface.co/Systran); consult the selected checkpoint's model card, e.g. [small](https://huggingface.co/Systran/faster-whisper-small) |
| Qwen3-ASR / Qwen3-ForcedAligner | Optional lyric recognition and forced alignment | [Apache-2.0, official Qwen repository](https://github.com/QwenLM/Qwen3-ASR); weights and commits in `src/music_studio/lyric_models.py` |
| HeartTranscriptor-oss | Optional singing-tuned Whisper recognition | [Apache-2.0, HeartMuLa](https://huggingface.co/HeartMuLa/HeartTranscriptor-oss); [official inference](https://github.com/HeartMuLa/heartlib/tree/main/examples) |
| torchcrepe 0.0.24 | Vocal pitch | [MIT, Max Morrison](https://github.com/maxrmorrison/torchcrepe/blob/master/LICENSE); the package contains converted [CREPE](https://github.com/marl/crepe) weights |
| PyTorch / torchaudio | Tensor/audio runtime | [PyTorch license](https://github.com/pytorch/pytorch/blob/main/LICENSE), [torchaudio license](https://github.com/pytorch/audio/blob/main/LICENSE) |
| librosa | Resampling, pYIN, chroma and beat baseline | [ISC](https://github.com/librosa/librosa/blob/main/LICENSE.md) |
| PyAV / FFmpeg | Audio decoding | [PyAV license](https://github.com/PyAV-Org/PyAV/blob/main/LICENSE.txt); FFmpeg and binary build terms remain applicable to the upstream distribution |
| python-soundfile / libsndfile | Float WAV export | [SoundFile licensing](https://github.com/bastibe/python-soundfile#license) |
| mido | MIDI export | [MIT](https://github.com/mido/mido/blob/main/LICENSE) |
| Basic Pitch 0.4.0 | Optional polyphonic note extraction; source and ONNX from the hash-pinned official wheel | [Apache-2.0, Spotify](https://github.com/spotify/basic-pitch/blob/main/LICENSE); upstream LICENSE is retained in the managed pack |
| ONNX Runtime 1.23.2 | Basic Pitch CPU inference | [MIT, Microsoft](https://github.com/microsoft/onnxruntime/blob/main/LICENSE) |
| pretty_midi 0.2.11 | Basic Pitch note/MIDI processing | [MIT](https://github.com/craffel/pretty-midi/blob/main/LICENSE.txt) |
| Sherpa-ONNX 1.13.8 | CPU speech enhancement runtime | [Apache-2.0](https://github.com/k2-fsa/sherpa-onnx/blob/master/LICENSE) |
| DPDFNet2 48 kHz HR | Optional speech cleanup weights | [Apache-2.0, Ceva](https://github.com/ceva-ip/DPDFNet); official Sherpa export pinned by SHA-256, not bundled |
| GTCRN | Experimental optional speech cleanup weights | [MIT, Xiaobin Rong](https://github.com/Xiaobin-Rong/gtcrn); official Sherpa export pinned by SHA-256, not bundled |
| pyebur128 / libebur128 | Gated loudness and true-peak metering | [MIT, pyebur128](https://github.com/jodhus/pyebur128), [MIT, libebur128](https://github.com/jiixyj/libebur128) |
| pystoi | Optional objective benchmark metric | [MIT](https://github.com/mpariente/pystoi) |

The Demucs upstream repository is archived. Its version is intentionally pinned for the initial backend. Replacement backends are isolated behind the same project schema.

The Windows runtime also pins CTranslate2 4.6.0 and setuptools <81. This combination was selected during local inference verification; CTranslate2 4.6.0 still imports `pkg_resources`.

The optional benchmark tools use [mir_eval](https://github.com/mir-evaluation/mir_eval) (MIT) and [remotezip](https://github.com/gtsystem/python-remotezip) (MIT). The fixed audio/reference subset reuses Jam-ALT, JamendoLyrics, GTSinger, GuitarSet and MUSDB preview material under their original dataset/per-track terms. Source credits, dataset versions, per-file hashes and use limits are recorded in [benchmarks/README.md](benchmarks/README.md) and [suite-v1.json](benchmarks/suite-v1.json). These datasets and derived audio are optional local evaluation assets and are not included in this repository's MIT grant.

The v4 extension uses 17 manually aligned MIR-1K recordings and character boundaries from the [ASRU 2023 author repository](https://github.com/navi0105/LyricAlignment), pinned at `1c39cd0369ce7dc55fa45277b59215b333d3a817`. Audio is retrieved from a version-pinned public mirror when the original host is unavailable. The mirror's license metadata is not treated as a replacement for the original source terms; the annotation repository has no explicit license grant. Only source metadata, hashes, code and numerical measurements are included here. Audio, mixed derivatives, annotation text and recognition transcripts remain ignored local assets. See [the v4 manifest](benchmarks/suite-v2-mir1k.json).

Development smoke tests may download `facebookresearch/demucs/test.mp3` into the ignored `.artifacts` directory. That audio is used only for local interoperability checks and is not redistributed as a Music Workbench sample or claimed to be owned by this project. The synthetic tone/chord/click tests are generated by the test code itself.

The singing smoke test uses a 30-second excerpt (20–50 s) of **Let's Go Fishin' — Karissa Hobbs**, obtained via librosa's `fishin` example. The source is [Creative Commons Attribution 3.0](https://creativecommons.org/licenses/by/3.0/), according to [librosa's attribution file](https://librosa.org/data/audio/Karissa_Hobbs_-_Lets_Go_Fishin.txt), with the [original Free Music Archive page](https://freemusicarchive.org/music/Karissa_Hobbs/Age_of_Flowers/09_Lets_Go_Fishin). Local tests crop, separate and analyze the recording; generated transcriptions and notes are machine estimates, not author-supplied notation. Full recordings and private test outputs remain ignored.

The workbench now bundles a **45-second precomputed preview** in
`src/music_studio/ui/demo/`: a crop from the start, original/vocal/backing Ogg
previews, machine-estimated lyrics/timing/notes/chords/beats and exports. Changes
are identified in its [attribution](src/music_studio/ui/demo/ATTRIBUTION.md) and
hash manifest. These audio derivatives retain **CC BY 3.0**, are not relicensed
under MIT and are not benchmark references. The UI retains artist/license/source
metadata in every imported demo copy. No endorsement by the artist is implied.

中文：代码采用 MIT，依赖和模型遵守各自许可。随包提供的 45 秒示例是 Karissa Hobbs
的 CC BY 3.0 授权录音的截取、分离与压缩衍生物，包含机器估计结果，不属于 MIT 音频资产，
也不是人工标注。完整署名、改动说明和文件哈希随示例保留；其他测试音频、标注正文和权重不随仓库发布。

Next also bundles a 23.11-second **CC BY 4.0** noisy speech demonstration derived from
Cassia Valentini-Botinhao (2017), [VoiceBank-DEMAND](https://doi.org/10.7488/ds/2117).
Eight utterances are concatenated with edge fades and gaps, then encoded as PCM16 FLAC.
The file list, original WAV hashes and changes are retained in
[the attribution](src/music_studio/ui/speech_demo/ATTRIBUTION.md) and its manifest.
This edited demonstration was chosen after the pilot evaluation; it is not a blind benchmark
or an MIT audio asset. The full paired dataset and enhanced audio remain outside Git.

Next 另含 VoiceBank-DEMAND 的 CC BY 4.0 带噪语音演示，保留署名和改动说明；
代码许可不替代录音许可。官方 EBU 响度测试音频未再分发。

## Transkun piano transcription / 钢琴转录

The optional Piano notes pack uses unchanged official Transkun 2.0.1 Python source and the V2 checkpoint/configuration from its hash-pinned wheel, under MIT. Its LICENSE is retained with the extracted files. Inference dependencies are isolated; training-only ncls and the upstream package metadata are not installed. No user-supplied pickle checkpoint is loaded.

- Official project and license: https://github.com/Yujia-Yan/Transkun
- Runtime: PyTorch / torchaudio (BSD-style), NumPy (BSD), SciPy (BSD), PrettyMIDI (MIT), mir_eval (MIT), SoundFile (BSD). These are downloaded separately, not part of the basic installer.
- SMD v2 evaluation: https://zenodo.org/records/13753319 and https://www.audiolabs-erlangen.de/resources/MIR/SMD/ . CC BY-NC-SA 3.0. Local noncommercial evaluation only; recordings and reference MIDI are not redistributed in this repository or used as promotional music. Public manifests contain provenance and hashes only.
