# Vocal separation, transcription and word timing

[中文](qwen-and-separation.md) · [Model management](models.en.md)

Open **AI tools** from Home or the workstation. dev17 adds automatic RoFormer and Qwen packs without system Python, a terminal or administrator access. Models download separately from the base installer. Initial setup needs internet; processing afterwards works offline.

| Pack | Purpose | Windows x64 automatic setup requirements | Free disk |
| --- | --- | --- | --- |
| Vocals & backing · RoFormer | Two aligned vocal/backing stems | NVIDIA Turing or newer, at least 4 GB VRAM | 12 GB |
| Speech, lyrics & word timing · Qwen | Qwen3-ASR-1.7B transcription and ForcedAligner-0.6B word timing | NVIDIA Ampere or newer, at least 8 GB VRAM | 24 GB |

Both use CUDA 12.8 and require NVIDIA driver 570 or newer. Inference checks at least 3 GB free VRAM for RoFormer and 6 GB for Qwen. Audio length and other GPU applications affect resource use. Advanced users can select CPU in a configured runtime, but CPU speed is outside these packs' validation scope.

## Suggested workflow

1. Click **Download and install**. Setup verifies pinned revisions, weights and configuration, then runs inference on bundled audio offline before enabling a pack. Pause/resume retains downloads. Verified official Torch wheel caches from other packs can be reused.
2. Import audio, select a clip and open **AI Models**. Run RoFormer, audition, then replace the clip or add stems as tracks. Source material is retained and adoption can be undone.
3. For songs, try transcribing the separated vocal with Qwen. Separation does not guarantee better recognition on every song; audition first. Specify the language or detect it automatically.
4. **Word timing** defaults to the pack recommendation: transcribe, then align words. Choose **Coarse paragraphs** for a faster text result. Open **Details and editing**, save corrected text and download TXT, LRC or SRT.

From dev18, only the selected timeline clip is processed. Audio, lyric and MIDI exports start at zero within that clip; adopting stems or melody retains its session position. Detailed text correction opens the single-asset editor.

RoFormer, Demucs and Whisper reuse their model across consecutive tasks with identical tool settings. Memory is released after 30 idle seconds, a tool change, cancellation, shutdown or a waiting music-generation task. Qwen keeps sequential recognizer/aligner loading.

## What alignment means

The independent acoustic model locates recognized words. It **does not correct recognition mistakes or recover missing text**, and it does not divide paragraph time evenly across words. The recognizer is released before loading the aligner to reduce VRAM use.

Unsupported languages or wholly invalid spans retain original timing. Partial alignment retains valid word times, displays other text with line timing, and adds review markers. Singing, sustained notes, overlapping voices and complex mixtures can remain difficult. Correcting a line clears its old word times so they cannot be paired incorrectly with the new text. Corrections do not trigger automatic realignment.

Explicitly configured interpreters and separation configurations retain priority. Automatic timing in a manual Qwen environment preserves its previous coarse behavior; explicitly selecting word timing requires installed ForcedAligner weights as well.

## Validation scope

Setup checks actual device execution, output structure, waveform alignment and valid word times. Importing dependencies alone does not enable the Qwen pack. These checks do not establish better transcription or singing alignment accuracy; that requires separate labeled evaluation.

See [hardware and workflow evidence](model-hardware.en.md) and [tool validation](model-tools-validation.md).
