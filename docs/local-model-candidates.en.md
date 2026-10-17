# Local music model candidates and integration policy

[中文](local-model-candidates.md) · [Platform plan](workbench-plan.en.md) · Researched 2026-10-16

See [audio resources research](audio-resources.en.md) for updated priorities, open assets,
evaluation datasets and storage choices.

This research index uses upstream repositories and official model cards. It is not an installed
or working-provider list. See [current support](models.en.md); subsequent integrations such as ACE-Step and RoFormer are documented in their user guides. Hardware figures below are upstream guidance, not a shared local benchmark.

## Candidates by capability

| Area | Candidate and primary source | Intended use and assessment | Conditions to verify |
| --- | --- | --- | --- |
| Music generation/editing | [ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5) | Upstream lists text/lyrics generation, references, repainting, added parts and vocal accompaniment; prioritize its creation interface | Upstream 6–8GB profile: 2B turbo + 0.6B LM. MIT code; verify selected weights/dependencies separately |
| Score-conditioned creation | [YuE2](https://github.com/multimodal-art-projection/YuE), [model card](https://huggingface.co/m-a-p/YuE2-3B) | September 2026 candidate: melody/chord plan → song, retaining ABC. Score edits regenerate the recording; they do not preserve untouched waveforms | Official Linux/24GB GPU setup. Apache-2.0 code; CC BY-NC 4.0 weights with additional creator permission; optional profile |
| Lyrics to songs | [HeartMuLa](https://github.com/HeartMuLa/heartlib) | Evaluate the released 3B generator on shared prompts | Apache-2.0 code; pin codec/weights and measure peak memory. Reference-conditioning TODOs are not released capabilities |
| Music source separation | [BSRoFormer / MelBand RoFormer inference framework](https://github.com/ZFTurbo/Music-Source-Separation-Training) | Vocal, backing and instrument separation candidates against the existing Demucs baseline | Families are not checkpoints: select target stems, exact weight hashes/licenses, windows, alignment and memory |
| Prompted sound isolation | [SAM Audio](https://github.com/facebookresearch/sam-audio) | Extract a target with text/temporal conditions; retain target and residual | Custom SAM License; resources/dependencies unmeasured, not a permissively licensed default bundle |
| Joint music transcription | [SheetSage2](https://huggingface.co/m-a-p/SheetSage2) | Melody, chords, beats, key and sections → ABC/MIDI/events, suitable for project structure | CC BY-NC 4.0 weights; MERT2 dependency. Isolated runtime and timing/pitch/score round trips required |
| Piano transcription | [Transkun](https://github.com/Yujia-Yan/Transkun) | Specialist candidate for polyphonic piano, velocities and note boundaries | MIT code; pin model/license and evaluate reference piano; do not generalize piano results to full mixes |
| Multi-instrument transcription | [YourMT3+](https://github.com/mimbres/YourMT3) | Instrument-aware multitrack MIDI | GPL-3.0 repository linking to prerelease code; first verify reproducibility, weights and licenses |
| Lightweight audio to MIDI | [Basic Pitch](https://github.com/spotify/basic-pitch) | Integrated in dev20 with ONNX CPU, audition and editable instrument-track notes | Older baseline, no SOTA claim; [benchmark](polyphony-benchmark.md) and [limits](polyphonic-notes.en.md); pitch bends are not imported into the piano roll |
| Controllable singing | [OpenVPI DiffSinger](https://github.com/openvpi/DiffSinger) | Notes/lyrics → singing, with pitch and expression controls | Apache-2.0 code; voicebank/vocoder terms are separate. Test phonemes, duration and controls |
| Singing/voice conversion | [Seed-VC](https://github.com/Plachtaa/seed-vc) | Reference-conditioned speech/singing conversion | GPL-3.0, archived repository; a replaceable candidate/baseline, not an assertion of current best quality |
| Speech/voice design | [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) | 0.6B/1.7B speech, voice design and reference cloning variants | Apache-2.0 code; distinguish variant capabilities, weight terms, long text and latency |
| Multilingual speech | [CosyVoice 3](https://github.com/QwenAudio/CosyVoice) | Fun-CosyVoice3-0.5B family as an alternative speech backend | Pin base/RL weights and licenses; evaluate streaming, language and acceleration configurations separately |
| Chinese/English effects | [MOSS-SoundEffect v2.0](https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0) | Up-to-30-second, 48kHz effects with a 1.3B DiT | Apache-2.0 card; Qwen3 encoder/VAE also consume memory. Isolate Python 3.12; validate Windows compilation and full pipeline resources |
| Interactive music | [Magenta RealTime 2](https://github.com/magenta/magenta-realtime) | Continuous text/audio/MIDI-controlled generation | Apache-2.0 code, CC BY 4.0 weights; 230M/2.4B, realtime targets Apple Silicon; Windows/NVIDIA realtime unverified |
| Music restoration | [Apollo](https://github.com/JusperLee/Apollo), [weights](https://huggingface.co/JusperLee/Apollo) | Low-bitrate music restoration candidate | CC BY-SA 4.0 work/weights; A/B artifacts and timbre damage; no promise of recovering original lossless audio |
| Video/text effects | [Sony Woosh](https://github.com/SonyResearch/Woosh) | Text/video-conditioned sound effects | Mostly MIT/some Apache-2.0 code; CC BY-NC released weights, optional research profile |
| Short effects/loops | [Stable Audio Open Small](https://huggingface.co/stabilityai/stable-audio-open-small) | Text to up-to-11-second, 44.1kHz stereo assets | Stability AI Community License; show applicable usage terms. Generated loops still need beat/seam checks |
| Alternative effects generation | [TangoFlux](https://github.com/declare-lab/TangoFlux) | Research candidate for text-conditioned effects | Upstream research/academic and noncommercial restrictions, including Stability/WavCaps terms; restricted optional experiment |
| Beat/downbeat tracking | [Beat This!](https://github.com/CPJKU/beat_this) | Beat and bar-grid candidate | MIT code/published weights; pin settings and inspect training overlap; retain librosa as a baseline |
| Song structure | [All-In-One](https://github.com/mir-aidj/all-in-one) | Tempo, beats/downbeats and intro/verse/chorus markers | Verify Windows NATTEN/native dependencies, training folds and resources; labels remain predictions |
| Semantic asset search | [CLAP](https://github.com/LAION-AI/CLAP), [linked weights](https://huggingface.co/lukewys/laion_clap) | Local audio/text embeddings for retrieval and similar sounds | Repository/linked weight library marked CC0, dependencies separate; pin weights and evaluate Chinese/English, effects and index cost. Not a generator |
| Music representations | [MERT2](https://huggingface.co/m-a-p/MERT-v2-FullSong) | Music representations, asset classification/similarity and transcription encoder | CC BY-NC 4.0 weights. Compare against CLAP per task; similarity thresholds are not interchangeable |
| Music understanding | [MusicFlamingo / Audio Flamingo](https://github.com/NVIDIA/audio-flamingo) | Timbre/structure descriptions and questions for assets/project inspection | MIT code; noncommercial weights with base-model conditions. Resources unmeasured; optional understanding backend |

Upstream SOTA claims identify candidates; platform defaults require comparable task-specific
quality/resource evaluation. Keep recent candidates, mature specialists and lighter baselines
without describing every entry as the current leader.

## Mixing, instruments and effects

A production workstation also needs a dependable non-neural engine: EQ, compression, reverb,
delay, routing, sampling, MIDI rendering, audio devices and plugin hosting.

| Reference | Capabilities to investigate | Constraints |
| --- | --- | --- |
| [Spotify Pedalboard](https://github.com/spotify/pedalboard) | Common DSP, VST3 instruments/effects and MIDI rendering | GPL-3.0; plugins/dependencies have separate terms. Researched, not integrated |
| [DawDreamer](https://github.com/DBraun/DawDreamer) | Instrument/effect graphs, MIDI, automation and time stretching | GPL-3.0; validate Windows, state persistence, plugin scanning/crash isolation and audio consistency |
| [Neural Amp Modeler Core](https://github.com/sdatkinson/NeuralAmpModelerCore) | Guitar amp/effect model inference for DI recordings | MIT core; separate .nam tone/cabinet IR terms. Not a MIDI instrument; device/latency integration still required |

The application is currently MIT. Establish an appropriate integration/distribution license
plan before adopting GPL components; a separate process does not automatically remove obligations.
Do not advertise researched GPL libraries as existing MIT built-ins.

## Promotion from research to supported provider

1. Register task scope, primary sources, code/weight/voicebank terms, maintenance, OS and runtime.
2. Freeze checkpoints, code revisions, configuration, dependencies and hashes; record download/disk sizes.
3. Run fixed short examples in isolation; retain failures/diagnostics and reproduce offline.
4. Measure quality, time, peak memory, long input, cancellation/recovery and regressions; separate upstream figures from local measurements.
5. Insert typed outputs into the project with timing/provenance; support audition, placement, undo and export.
6. Choose task-specific recommended, lightweight, quality and experimental profiles; upgrades preserve existing results.

Measure CPU, 8GB, 12–16GB and 24GB+ profiles with hardware, precision, offload and input lengths.
ACE-Step's upstream near-8GB configuration and YuE2's official 24GB setup do not establish local
verification. Label restricted open weights separately from permissively licensed open-source models.

Community adapters can add models, parameters and hardware optimizations. Keep the base install
useful and install/switch models on demand. Allow configured local model services to avoid
duplicating weights. See the [roadmap](workbench-plan.en.md) for the first implementation order.
