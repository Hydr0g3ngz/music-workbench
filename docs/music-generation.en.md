# Local music generation: ACE-Step 1.5

[中文](music-generation.md) · [Create workbench](create-preview.en.md)

Open **Models → Generate music draft**, describe the instruments, style and mood, then run.
Audition the result before choosing **Add track**. Generation, failure and cancellation do not
change the arrangement. Adopted audio can be moved, trimmed, faded and mixed with sampled
instruments, grooves and imported MIDI, then exported as WAV. Adoption supports undo;
the original draft and its parameters remain available.

## Setup

Basic arrangement and factory instruments do not need this optional model. This profile needs
an NVIDIA CUDA GPU and Python 3.11/3.12. Actual inference was tested only on Windows 11,
an RTX 4070 Laptop 8GB and 32GB RAM. Allow at least roughly 20GB of disk space; downloads,
the separate environment and installation temporaries may require more. These test conditions
do not establish compatibility with every 8GB GPU or low-memory computer.

Run explicitly from the repository root:

```powershell
py -3.12 scripts/setup_ace.py
.\Start-Music-Workbench.cmd
```

On Linux use `python3.12 scripts/setup_ace.py`; the Linux path has not received real inference
acceptance testing. Setup downloads from official PyTorch, PyPI, GitHub and Hugging Face
sources into an isolated environment. It does not upgrade the UI or other model environments.
App startup never downloads these weights. Configuration defaults to
`.artifacts/acestep-runtime.json`; override with `MUSIC_STUDIO_ACE_CONFIG` if needed.
Once cached, the worker enforces offline inference.

The profile uses Turbo, INT8 linear weights, BF16, SDPA, CPU offload, eight steps and one
candidate. It does not load the 5Hz language model, compile the model or use Flash Attention.
Start with a 12–20 second instrumental. Requests allow 10–60 seconds; actual 12/20/32-second
instrumentals ran successfully. Sixty-second and vocal/lyric quality remain unverified. BPM is a target;
generated audio may not align precisely and is not automatically stretched.

For reference variation, select a 10–60 second audio clip and choose reference mode.
The worker receives an immutable copy of the actual crop, with reference/source hashes and parameters.
Project key and loop length can supply context; conditioning is not verified musical compliance.
See the [32-second creation walkthrough](creations/radio-through-the-clouds.md) and
[workflow guide](ai-production-workflow.md) for real inference and adoption.

## Pinned sources

| Component | Revision |
| --- | --- |
| [ACE-Step source](https://github.com/ACE-Step/ACE-Step-1.5) | `ca1e85fe9430179831e6bc6be790c332190a3866`, MIT |
| [Ace-Step1.5 weights](https://huggingface.co/ACE-Step/Ace-Step1.5) | `19671f406d603126926c1b7e2adc169acbcade22`, repository declares MIT |
| Downloads | Turbo DiT, VAE, Qwen3-Embedding-0.6B; 17 files, 6,336,686,268 bytes |
| Runtime | Torch/Torchaudio 2.10.0 CUDA 12.8, Transformers 4.57.6, TorchAO 0.16.0, safetensors 0.8.0; see `requirements/acestep.txt` |

Setup verifies the source archive SHA256, HF LFS SHA256 and small-file Git blob hashes.
Upstream synchronizes model code from its source; a separate resolved view pins that code
without changing the downloaded snapshot. Workers check manifest/file SHA256 again.
Tasks record revisions, worker hash, profile, seed, prompt, duration, BPM, steps, audio hashes
and resource measurements. Model licensing does not guarantee rights to any particular output.

## Local run, 2026-10-16

Prompt: `Warm jazz trio, soft grand piano, brushed acoustic drums and upright bass, intimate late-night room, instrumental`.
Duration 12s, BPM 108, seed 42, eight steps. This is an integration/resource check, not a music
quality benchmark or a selected best seed.

| Measurement | Successful run |
| --- | --- |
| Profile | `cuda-int8-offload-v3-pread` |
| Cold-process total | 112.453s, including checksum verification and loading |
| Loading / subsequent generation | 80.906 / 31.547s; diffusion itself ~3.90s; remaining work includes offload, encoding and decoding |
| CUDA allocated / reserved peaks | 3150 / 3222 MiB, PyTorch counters rather than total system VRAM |
| Peak resident RAM | 9821.3 MiB |
| Peak Windows private commit | 17941.6 MiB, includes page-backed memory and is not resident RAM |
| Original output | Stereo 48kHz WAV, 12.0s; SHA256 `bb108bf1c3900e2d346ff091ab9631ee059c38c856ddd71dcb02e6730472fc0e` |
| Arrangement copy | Stereo 44.1kHz, 12.0s, sample peak −0.979 dBFS, zero full-scale samples |

All three earlier attempts remain recorded: BF16/offload failed on GPU transfer; INT8 v1
failed at the text encoder despite ~5.9GiB of free VRAM; INT8 v2 failed transferring DiT and
was subsequently marked interrupted when its owner stopped. Windows copy-on-write mmap
reserved commit for the entire 4.79GB checkpoint. Switching the isolated worker to the official
safetensors `pread` backend allowed attempt four to complete. Other applications remained open;
no system pagefile settings were changed. Available system commit affects this result.

More styles, Chinese/English prompts, seeds, longer audio, vocals/lyrics, blind listening,
tempo adherence and other RAM/GPU configurations remain to be evaluated. One successful
draft establishes neither broad stability nor music quality.

A subsequent 20s request with the same prompt and seed completed in 66.500s: loading
49.641s, generation 16.859s, CUDA allocated/reserved peaks 3152.1/3226 MiB, resident RAM
peak 10936.1 MiB and private commit peak 17997.4 MiB. It used a fresh worker but warm OS
file caches; the timing difference does not establish a duration/performance relationship.
Original WAV SHA256: `bb5339c690b4a8e4e56fbf783dd866029c8fbf8f6d0a60285e975881a720a3de`.
The canonical copy peaks at −1.144 dBFS with zero full-scale samples. API checks verified
real-draft adoption, undo/redo, provenance and export. A sampled two-bar groove and imported
piano MIDI intro were also arranged before the draft and exported as a 24.444s, 44.1kHz,
24-bit three-track mix. These are integration checks, not full mixing or listening acceptance.

## Diagnostics and recovery

Enable **Use saved blueprint & section intentions** to include the creative brief, palette,
motif, harmony and section purpose. Tempo/key follow the saved project. Preview the actual
prompt before queuing. Rules assemble it; local ACE-Step generates the audio. This adds no
language model and does not guarantee compliance. [Methods and workflow](arranging-methods.md).

**Details** shows errors and resource counters. Full logs live in the workspace under
`.creation-tasks/<id>/worker.log`; stage measurements are in `output/resources.jsonl`.
Windows commit exhaustion can cause CUDA allocation errors while physical VRAM is free.
Cancellation stops only the task's owned subprocess. Reopening keeps completed drafts and
does not silently rerun interrupted jobs. Each task currently starts a fresh process;
warm caching and lower-RAM loading remain future optimizations.
