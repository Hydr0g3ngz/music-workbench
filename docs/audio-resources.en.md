# Local audio models, assets and database choices

[中文](audio-resources.md) · [Full model index](local-model-candidates.en.md) · [Platform plan](workbench-plan.en.md)

Researched 2026-10-16 using official repositories, model cards and dataset releases.
This is a research snapshot scoped to its date, rather than an installation list or local performance report. See [model support](models.en.md) for current integrations.
Track code, weight, voicebank and content licenses separately.

## Models worth validating first

Priority reflects creative value, project integration cost and license clarity, not a universal quality ranking.

| Capability | Candidate and primary sources | User benefit | Integration assessment |
| --- | --- | --- | --- |
| Music creation/editing | [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5), [weights](https://huggingface.co/ACE-Step/Ace-Step1.5) | Prompt/lyrics generation, references and repainting as new audio clips | First pilot; MIT code/card. Start with 2B turbo; base-only layer features must not be advertised for turbo |
| Vocal/backing separation | [MelBand RoFormer KJ](https://huggingface.co/KimberleyJSN/melbandroformer), [MSST configs](https://github.com/ZFTurbo/Music-Source-Separation-Training/blob/main/docs/pretrained_models.md) | Aligned stems for remixing/transcription | Compare against existing Demucs; KJ card says MIT. Select separate BS-RoFormer/SCNet checkpoints for other stem sets; terms/results are not interchangeable |
| Beat/bar grid | [Beat This!](https://github.com/CPJKU/beat_this) | Reviewable beats and downbeats | MIT code and published weights; check reference/training overlap; this is not an audio time-stretch engine |
| Piano to MIDI | [Transkun V2](https://github.com/Yujia-Yan/Transkun) | Polyphonic piano notes, velocities and boundaries | MIT code; pin packaged checkpoint/terms and evaluate piano references; not complete transcription of arbitrary mixes |
| Joint lead-sheet analysis | [SheetSage2](https://huggingface.co/m-a-p/SheetSage2) | Melody/chord MIDI, ABC and timed structure | Optional CC BY-NC 4.0 weights with MERT2; lead sheets, not individual transcription of every instrument |
| Controllable singing | [OpenVPI DiffSinger](https://github.com/openvpi/DiffSinger) | Notes/lyrics to singing with expression | Second batch; Apache-2.0 code, separate voicebank/vocoder terms; needs MIDI, phoneme and duration interfaces |
| Chinese/English sound effects | [MOSS-SoundEffect v2.0](https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0), [implementation](https://github.com/OpenMOSS/MOSS-TTS/tree/main/moss_soundeffect_v2) | Up to 30-second, 48kHz effect assets | Second-batch pilot; Apache-2.0 card. 1.3B DiT plus Qwen3 encoder/VAE; count the entire pipeline's memory |
| Semantic asset search | [LAION CLAP](https://github.com/LAION-AI/CLAP), [linked weights](https://huggingface.co/lukewys/laion_clap) | Text-to-audio and similar-sound retrieval | First asset-library pilot; repository/weight library marked CC0, separate dependencies. Compare music/SFX checkpoints and evaluate Chinese queries explicitly |
| Speech/voice design | [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS), [0.6B Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base) | Narration and reference-conditioned speech | Second batch; Apache-2.0 code and selected Base card. Base, CustomVoice and VoiceDesign expose different capabilities; TTS is not singing synthesis |
| Compressed music restoration | [Apollo](https://github.com/JusperLee/Apollo), [weights](https://huggingface.co/JusperLee/Apollo) | A/B restoration candidates | Second-batch experiment; CC BY-SA 4.0 work/weights. Measure artifacts; do not promise recovery of original lossless information |
| Interactive music | [Magenta RealTime 2](https://github.com/magenta/magenta-realtime), [model card](https://github.com/magenta/magenta-realtime/blob/main/MODEL.md) | Continuous music controlled by text, audio and MIDI | Later extension; Apache-2.0 code, CC BY 4.0 weights. Small 230M/base 2.4B; current realtime path targets Apple Silicon. NVIDIA offline and Windows need separate validation |
| Guitar amp modeling | [Neural Amp Modeler](https://github.com/sdatkinson/neural-amp-modeler), [inference core](https://github.com/sdatkinson/NeuralAmpModelerCore) | Process recorded guitar DI through modeled tones | Later recording/effects feature; MIT code/core, separate .nam/IR terms. Not a MIDI guitar instrument; low-latency device integration is still required |

Existing Qwen3-ASR, Whisper, Demucs, CREPE and speech cleanup remain useful tools and baselines;
see [actual support](next-models.en.md). Generated WAV files should become project assets that users
can audition, insert, move, undo and export. MIDI should support instrument replacement and composition.
MIDI import and sampled instruments are available for continued editing; see the [instrument guide](creation-library.en.md).

## Additional candidates with resource or usage constraints

| Candidate | Value | Current position |
| --- | --- | --- |
| [YuE2](https://huggingface.co/m-a-p/YuE2-3B), [repository terms](https://github.com/multimodal-art-projection/YuE#license) | Editable melody/chord plans to complete songs | Official Linux/24GB GPU setup. HF says CC BY-NC; GitHub adds creator permission and separate company licensing. Match terms to downloaded revisions. Score edits rerender audio rather than preserving untouched waveforms |
| [SAM Audio](https://github.com/facebookresearch/sam-audio) | Text/time/visual target isolation | Custom SAM License, gated checkpoints and unmeasured Windows/resources; not a default 8GB plugin |
| [Sony Woosh](https://github.com/SonyResearch/Woosh) | Text effects and video-to-audio | Mostly MIT/some Apache-2.0 code, CC BY-NC released weights; optional research backend |
| [Stable Audio Open Small](https://huggingface.co/stabilityai/stable-audio-open-small) | Up to 11-second, 44.1kHz stereo assets | Community License; retain as lightweight candidate, not MIT/Apache weights |

HeartMuLa, instrument transcription, voice conversion and music understanding remain in the
[full index](local-model-candidates.en.md). Upstream claims are not shared-condition local benchmarks.

## Databases should first help users create

Open assets, open server software, online services and evaluation datasets are different resources.
Their contents do not all belong in an application download.

| Source | Purpose | Content/terms | Recommendation |
| --- | --- | --- | --- |
| [VCSL](https://github.com/sgossner/VCSL) | Factory sampling instruments | CC0 instrument samples with SFZ; upstream typical instrument about 20–75MB | Highest priority; small curated, auditioned downloads rather than the whole raw library |
| [Salamander Grand Piano](https://github.com/sfzinstruments/SalamanderGrandPiano) | More realistic piano playback | Sampled piano/SFZ, CC BY 3.0; preserve Alexander Holm/source credits and changes | Optional piano pack; requires a sample player |
| [Groove MIDI Dataset](https://magenta.withgoogle.com/datasets/groove) | Editable drum patterns/fills | 1,150 human-performed MIDI files, CC BY 4.0; MIDI-only 3.11MB versus 4.76GB with audio | Highest priority; derive short templates with credits, tempo/style and drum mappings |
| [Freesound](https://freesound.org/help/faq/), [API](https://freesound.org/docs/api/overview.html) | Discover/import effects and one-shots | Per-item CC0/BY/BY-NC etc.; API credentials differ from original-file OAuth2 | Optional online source, filter licenses and preserve attribution; not one unrestricted library |
| [MusicBrainz](https://musicbrainz.org/doc/About/Data_License) | Artist/title/release/recording IDs | Core CC0; supplementary/live feed CC BY-NC-SA 3.0; no song audio or lyric rights | Start with core metadata; match recording versions rather than titles alone |
| [LRCLIB](https://github.com/tranxuanthang/lrclib) | Plain/synchronized lyric candidates | MIT self-hosted server/API; code license does not license lyric contents | Optional retrieval with version/duration matching and user review; not ground truth or bundled lyrics |

Freesound's 2026 FAQ separately describes uploader GenAI training preferences. Record creative,
evaluation and training purposes separately; bulk training access should use its Data Packs process.
Lyric retrieval does not replace separate ASR/alignment evaluation.

## Existing annotations for evaluation

Keep the existing [benchmark protocol](benchmark-protocol.md), extending references per new task.

| Dataset | References/tasks | Conditions and intended use |
| --- | --- | --- |
| [MUSDB18 / HQ](https://sigsep.github.io/datasets/musdb.html) | Four-stem separation | Complete data has academic/access and per-track terms. Keep existing preview regression; pin authorized full-HQ evaluation. Not factory samples |
| [MAESTRO](https://magenta.withgoogle.com/datasets/maestro) | Aligned real piano/MIDI, notes, velocity, pedals | CC BY-NC-SA 4.0; use official test splits and document model overlap. Piano findings do not generalize to other instruments |
| [Slakh](https://www.slakh.com/), [redux](https://zenodo.org/records/4599666), [tools](https://github.com/ethman/slakh-utils) | Aligned multitrack synthesis/MIDI and separation-to-transcription | Publisher states CC BY 4.0. Redux removes MIDI duplicates: 1710 tracks/151 test tracks. About 104GB archive; validate a small subset first. Synthetic domain |
| [GuitarSet](https://guitarset.weebly.com/) | Guitar notes, string pitch, chords and beats | Reuse existing references, distinguishing instructed/performed chords; document player/song splits, license revision and training overlap |
| [FSD50K](https://zenodo.org/records/4060432) | 51,197 clips/200 sound classes | Curated dataset CC BY plus per-file CC0/BY/NC/Sampling+; curators request contact for commercial use. Evaluation candidate with per-file filtering |

Class-label retrieval is not natural-language search satisfaction. Effects generation needs fixed prompts,
blind listening and retained failures. Synthetic references do not replace real mixes. Unknown training
overlap must stay visible; these are not automatically blind tests.

## Storage: keep SQLite and add a derived index when needed

Current `StudioService` uses `.studio.sqlite3` with WAL; workstation arrangement records share it.
That is the current code state. The following is a proposal, not a completed migration.

| Component | Role | Decision |
| --- | --- | --- |
| [SQLite](https://sqlite.org/copyright.html) + [FTS5](https://sqlite.org/fts5.html) | Projects, metadata, jobs, history, tags/text search | Public-domain SQLite remains the source of truth. Chinese needs explicit tokenization/substring handling |
| [sqlite-vec](https://github.com/asg017/sqlite-vec) | CLAP similarity search | MIT/Apache-2.0 dual license, C extension, Windows support. First pilot; pre-v1 means pin versions and support index rebuilding |
| [LanceDB OSS](https://github.com/lancedb/lancedb) | Alternative vector/metadata index at larger scale | Apache-2.0 and embedded/local. Compare memory, filters, latency and backup before selecting; do not install both by default |

Keep large audio on disk. SQLite records hashes, relative paths, duration/rate, provenance, licenses,
tags and model versions. Vector indices are rebuildable derivatives keyed by asset IDs; deletion and
license filters must also apply to search. Separate embedding versions/dimensions/preprocessing;
CLAP and MERT vectors cannot share a similarity space. Back up projects and source assets first.
Revisit server databases when multiuser/cloud work becomes a concrete requirement.

## Integration order for this workstation

1. **Assets/instruments:** a VCSL starter pack, Groove MIDI, MIDI import, sampler and usable basic effects. Audition and drag assets into the arrangement.
2. **AI creation:** isolated ACE-Step 2B runtime, short generation, candidate audition, project insertion and continued mixing. Validate repaint/base extensions afterward; GPU jobs must not occupy the playback thread.
3. **Rework recordings:** RoFormer stems, Beat This grids and Transkun piano MIDI; optional restricted SheetSage2 profile with one shared time base.
4. **Discovery/sound production:** CLAP and a rebuildable vector index; MOSS effects, DiffSinger and Qwen speech as task-specific providers.
5. **Broader models and Agent:** extend the same project/asset/task contracts to YuE2, MRT2 and NAM after basic production becomes usable.

Stable playback, EQ, compression, reverb, buses and automation remain platform fundamentals.
[Pedalboard](https://github.com/spotify/pedalboard) and [DawDreamer](https://github.com/DBraun/DawDreamer)
are useful DSP/host references with GPL-3.0 considerations for this MIT application; separate processes
do not automatically remove distribution obligations.

For each provider freeze inputs, model hashes, cold/warm times, peak VRAM/RAM, quality baselines,
long-input behavior, cancellation and recovery. Test CPU, 8GB, 12–16GB and 24GB+ profiles.
ACE-Step's [official 6–8GB configuration](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/GPU_COMPATIBILITY.md)
uses quantization/offload. It does not establish an 8GB minimum for every model or the full pipeline.
