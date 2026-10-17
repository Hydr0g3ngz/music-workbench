# v0.1 architecture

> Historical Studio analysis architecture. Current workstation design is documented in [Platform design](workbench-plan.en.md); users should start with [Workbench documentation](README.en.md). The analysis product is maintained in [Music Studio](https://github.com/Hydr0g3ngz/music-studio).

Music Studio is a local batch analysis engine with an optional local web workbench. It has no account system or hosted inference dependency. Initial package/model downloads require a network connection. Once installed and cached, `--offline` prevents model downloads.

## Pipeline

1. PyAV decodes the first audio stream into stereo float32 WAV at 44.1 kHz. The first decoded sample defines time zero. Container timestamps are not preserved. The master waveform is never silence-trimmed or time-stretched.
2. Demucs estimates vocals and the other source tracks. The other tracks are summed into an instrumental. Both output WAV files retain the master's length, sample rate and gain convention. They are estimates, not the original studio stems.
3. The selected Whisper or optional Qwen/Heart backend transcribes isolated vocals or the source mix. It runs without speech VAD because speech-only filtering can discard sung vowels. Recognition text and alignment are separate choices. Chinese acoustic tokens may contain several characters: the engine does not invent individual character boundaries.
4. CREPE extracts a monophonic vocal pitch contour in overlapping 20-second windows; pYIN is an explicitly selected CPU alternative. Periodicity and amplitude thresholds reject unvoiced frames. Median filtering, short-gap repair and onset-aware note segmentation produce MIDI notes. The original pitch contour is retained.
5. Librosa estimates beat locations from the original mix. It does not supply downbeats or time signatures in this release. The reported BPM is a global estimate; the beat timestamps are retained individually.
6. Harmonic chroma from the instrumental is averaged between beats (or half-second windows when no beat grid is available). A temporal decoder selects among 24 major/minor triads and `N` (no confident estimate). Scores are cosine similarities, not probabilities.
7. Words and notes are linked by temporal overlap, including one word spanning several notes. MIDI stores an estimated tempo map without moving the performed notes to the beat grid. LRC/SRT use line times; word times are retained in JSON.

## Process and memory ownership

The parent process owns the project and cache. It launches one disposable Python worker per analysis stage. Each worker lazily imports its models, executes and exits, releasing PyTorch and CTranslate2 allocations before the next stage. GPU stages are not run concurrently. Demucs reduces its segment length on CUDA out-of-memory down to two seconds; further failure is explicit. CPU mode must be selected explicitly if the user requests CUDA but it is unavailable.

Audio files are decoded/resampled on CPU. Audio length still increases CPU memory and disk usage; this release is intended for individual songs, not day-long recordings. CPU/library startup and model loading are included in stage wall times. PyTorch allocator metrics do not include CTranslate2 memory, so they are not a complete VRAM benchmark.

## Integrity and resume

`run.json` records the source SHA-256, settings, stage signatures, output SHA-256 values, metrics and the current run status. A project directory is protected by an OS file lock. Unrecognized nonempty folders and a different input file are rejected. `--resume` reuses an output only when its dependency signature and every recorded artifact hash match. Changing ASR language invalidates transcription without redoing separation.

Incomplete workers are not cached. Ctrl+C terminates the child and records a cancelled run. Restart with the same arguments plus `--resume`. A previously completed `project.json` may remain after a later failed run; `run.json` is authoritative and `validate` rejects a project whose latest run did not complete.

JSON writes use temporary files followed by replace. `project.json` is written only after all stages, schema validation and exports succeed. All times are in seconds from decoded sample zero; audio duration is computed from the actual sample count. Numerical rounding after analysis resampling is clamped back to the master duration.

## Local workbench

`music-studio ui` serves bundled HTML, CSS and JavaScript through FastAPI on `127.0.0.1`. It requires no Node build, CDN or remote inference. Each import creates a separate directory containing the input, job metadata and the engine's result folder. Model files remain in the configured model cache. The API validates project IDs and resolved asset paths, restricts host/origin, and serves audio with byte-range support.

The manager permits one active analysis at a time and runs the existing pipeline in a background thread. Each neural stage still belongs to a disposable child process. A cancellation event terminates the active worker and retains completed stages; restarting analysis reuses validated stage caches. Server shutdown requests cancellation. A new server marks previously running jobs as interrupted so they can be resumed. A single server should own a workspace at a time.

The browser renders actual peak envelopes, pitch, notes, chords, beats and lyrics from the saved project. Three decoded audio buffers start from the same offset on one Web Audio context; track switching changes gains without changing the clock. MIDI preview uses oscillators scheduled from the extracted notes. The player decodes a whole song into browser memory; long recordings are outside the first UI's target. Downloads expose the same validated exports as the CLI. Lyric text edits are stored separately from raw recognition and are included in all lyric exports. Edited sentences omit stale word timing until realignment. Note editing is outside this release.

UI code is excluded from inference cache fingerprints. Changes to the browser or local API do not force expensive audio stages to run again.

## Extension points

Backends are small functions under `backends/`. New separators, singing aligners, RMVPE and neural beat/chord backends can return the same typed records. The public contract is in `schema.py`; `worker.py` handles isolation and `pipeline.py` handles dependency signatures. The workbench operates on the same project without embedding inference logic.

No note editor, simplified/staff notation, complete instrumental MIDI, cloud service or GitHub publishing automation is included in v0.1.

## Analysis revisions and lyric inference

The first analysis remains in `result/`; later analyses live in `revisions/<id>/` with sibling metadata. `current_version` is an atomic pointer in the job record. Starting a new analysis never rewrites the selected result. Completed revisions can be selected again, including their version-bound edits. A failed/cancelled revision cannot replace the current result. APIs accept explicit version parameters so audio, lyrics, exports and the editor refer to the same snapshot. Edits require both the analysis version and an optimistic edit revision; line IDs from a new recognition cannot accidentally receive corrections from an older editor.

Full analysis reruns every required module in a fresh result. Lyric-only analysis reuses original decoded/stem audio and musical predictions, then rebuilds lyric-word links and exports. Only lyric configuration is updated; inherited melody/beat/chord settings and provenance are retained. Re-aligning corrected or supplied text records that text source instead of relabelling it as new ASR. Reference text never enters automatic-recognition benchmark inference.

The optional lyric runtime uses qwen-asr 0.0.6 / Transformers 4.57.6 in a separate environment, with pinned Qwen3-ASR 1.7B, Qwen3-ForcedAligner 0.6B and HeartTranscriptor weights. The parent launches that environment only for lyric work. Source mix and separated vocals are selectable. Qwen recognition uses bounded audio chunks, HeartTranscriptor follows the upstream Whisper pipeline; neither uses a speech-only VAD. Independent alignment is separately selectable, including an experimental cross-attention alignment adapter using cached Whisper small weights. Missing/zero-length or nonmonotonic times trigger explicit fallbacks or failure; no equal-duration character timing is manufactured. Python/NumPy/PyTorch and CTranslate2 random seeds are set explicitly.

The conservative `anchors` option transfers only exact monotonic token matches from a measured Whisper small vocal guide. Unmatched text stays in the sentence but has no word timestamp. The UI reconstructs the entire sentence, including untimed gaps, and marks those gaps for sentence-level seeking. MIDI falls back to a full-sentence lyric event when word coverage is incomplete. Guide reuse checks audio hash, language, seed and model revision. This is a text-to-guide match, not acoustic forced alignment of unknown words; repeated phrases can still be matched incorrectly.

Benchmark-only batch workers explicitly opt into model reuse, clear ASR models before loading aligners, freeze the engine and hash inherited predictions. Their warm per-case elapsed times are not cold-process timings. A separate alignment ablation can reuse verified native acoustic guides without rerunning a neural model. These optimizations do not enable shared persistent model objects in the product's ordinary one-stage workers.
