# Turn instrument audio into editable notes

[中文](polyphonic-notes.md) · [Models](models.en.md)

dev20 adds **Basic Pitch 0.4.0 ONNX**, a lightweight baseline for overlapping notes from one instrument. It produces MIDI that you can replay, change and arrange. It does not separate instruments or provide guaranteed full-score transcription of a mixed song.

## Install and use

1. Install **Polyphonic notes** in **AI tools**. Windows x64, CPU only; estimated download 150–350 MB, keep 2 GB free. No system Python or GPU is needed.
2. Import solo piano, guitar or another instrument and select an audio clip. Separate complex mixtures first. Only the selected source crop is processed.
3. Run **AI models → Solo instrument → polyphonic MIDI**.
4. Audition the synthesized result and choose **Add notes to instrument track**. In the piano roll, edit pitch, timing, length and velocity, quantize or change instruments. Double-click a note to delete it.
5. Export MIDI for notes, WAV for the current instruments/mix, or `.mwb` to retain editable notes and audio.

The original audio is retained and adoption is undoable. Velocity comes from estimated amplitude and is not an accurate performance-dynamics measurement. Pitch bends are not imported into the piano roll. For dense results, process a short phrase first.

## Controls

| Control | Default | Trade-off |
| --- | --- | --- |
| Onset threshold | 0.50 | Higher often removes false notes but can miss quiet notes |
| Frame threshold | 0.30 | Higher can shorten sustained notes; listen and compare |
| Minimum note length | 127.7 ms | Higher removes short noise but can miss fast playing |

Lower thresholds do not necessarily improve accuracy. On five frozen GuitarSet accompaniment recordings, default onset F1 was **0.672**, onset+offset F1 **0.333**; conservative settings scored 0.656 / 0.315, sensitive settings 0.604 / 0.323. Defaults are retained. GuitarSet was used in Basic Pitch training, so dataset overlap is possible. This is a development comparison, not an independent leaderboard; velocity accuracy was not measured. See the [protocol and numerical report](polyphony-benchmark.md).

A 16-second AI piano clip took **6.63 s** in task inference and **11.59 s** for the full invocation on the tested machine; CPU speeds vary. The ONNX checkpoint is about 225 KiB; its environment also contains audio/scientific dependencies. The pack installs neither TensorFlow nor Torch and makes no CUDA claim. First use may include import/JIT overhead.

## Implementation and licensing

Source and ONNX weights are extracted from a hash-verified official wheel without its TensorFlow-dependent distribution metadata. The isolated environment is checked with actual offline inference. Use AI tools' check/repair actions for missing or corrupt files.

[Spotify Basic Pitch](https://github.com/spotify/basic-pitch) source/weights use Apache-2.0; ONNX Runtime uses MIT. Versions, hashes and the benchmark script are in the repository. Weights download separately from the installer. Transkun remains an unintegrated research candidate.
