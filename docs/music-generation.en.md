# Local music generation: ACE-Step 1.5

[中文](music-generation.md) · [Create workbench](create-preview.en.md)

Open **Models → Generate music draft**, describe the instruments, style and mood, then run.
Audition the result before choosing **Add track**. Generation, failure and cancellation do not
change the arrangement. Adopted audio can be moved, trimmed, faded and mixed with sampled
instruments, grooves and imported MIDI, then exported as WAV. Adoption supports undo;
the original draft and its parameters remain available.

## Setup

Installed Windows users can use **AI setup** on Home without a separate Python installation. Requirements: compatible NVIDIA GPU, at least 8 GB VRAM, 35 GB free space and roughly 8–12 GB initial downloads. Verified hardware is Windows 11, RTX 4070 Laptop 8 GB and 32 GB RAM; other systems can differ in compatibility and speed. [Model support](models.en.md).

Source users with Python 3.11/3.12 can run from the repository root:

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

[技术验证 / Technical verification](feature-validation.md)。

## Diagnostics and recovery

Enable **Use saved blueprint & section intentions** to include the creative brief, palette,
motif, harmony and section purpose. Tempo/key follow the saved project. Preview the actual
prompt before queuing. Rules assemble it; local ACE-Step generates the audio. Audition to
judge whether the result fits your intention. [Methods and workflow](arranging-methods.md).

**Details** shows errors and resource counters. Full logs live in the workspace under
`.creation-tasks/<id>/worker.log`; stage measurements are in `output/resources.jsonl`.
Windows commit exhaustion can cause CUDA allocation errors while physical VRAM is free.
Cancellation stops only the task's owned subprocess. Reopening keeps completed drafts and
does not silently rerun interrupted jobs. Each task currently starts a fresh process;
warm caching and lower-RAM loading remain future optimizations.
