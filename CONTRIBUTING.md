# Contributing to Music Workbench

[中文](CONTRIBUTING.zh-CN.md) · [Roadmap](docs/workbench-roadmap.md)

Issues and pull requests are welcome in English or Chinese. Describe the musical task, what currently blocks it and the behavior you want. Discuss large engine/model changes in an issue before implementation; small fixes can go straight to a PR. Use shareable synthetic or licensed audio for reproduction.

## Development setup

Use Python 3.11/3.12 and Node 22. Static HTML/CSS/JavaScript needs no frontend build or external CDN. Basic development does not require Torch or downloaded models.

```sh
python -m venv .venv
# Windows: .venv/Scripts/activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[workstation,benchmark,agent,dev]"
music-workbench
```

The source launcher uses `outputs/workbench` and an available port starting at 8920. Use a separate workspace for destructive fixtures, never personal project data. Windows can also use `Start-Music-Workbench.cmd`.

## Locate the implementation

| Area | Location |
| --- | --- |
| Entrypoint | `src/music_studio/workbench_cli.py` |
| Projects, revisions and assets | `src/music_studio/studio/service.py`, `arrangement.py`, `models.py`, `project_pack.py` |
| Creation and model adapters | `creation.py`, `tasks.py`, `registry.py`, `ace_worker.py`, `separation.py`, `ai_setup.py` in `studio/` |
| Audio render, instruments and effects | `studio/dsp.py`, `effects.py`, `library.py`; `ui/static/station-engine.js`, `effects-dsp.js` and worklets |
| Workstation UI | `src/music_studio/ui/static/station*`, `welcome*`, `learn*`, `ai-setup*` |
| Desktop and packaging | `desktop/`, `scripts/package_*.py`, `scripts/build-desktop.ps1` |

The internal `music_studio` namespace retains import/project compatibility. This repository's product and entrypoint are Music Workbench. Classic analysis and the Next single-asset editor are compatibility components; [Music Studio](https://github.com/Hydr0g3ngz/music-studio) maintains the separate song-analysis product.

## Validate changes

```sh
python -m ruff check .
python -m pytest -q
node --test tests/ui_playback.test.cjs tests/ui_i18n.test.cjs tests/ui_transport.test.cjs tests/ui_comparison.test.cjs tests/ui_station.test.cjs tests/ui_creation.test.cjs tests/ui_recording.test.cjs tests/ui_timing.test.cjs tests/ui_workflow.test.cjs tests/ui_composition.test.cjs tests/ui_material.test.cjs tests/ui_envelope.test.cjs tests/ui_desktop.test.cjs tests/ui_setup.test.cjs tests/ui_tutorial.test.cjs
```

These are the regression commands in [CI](.github/workflows/tests.yml). Core tests use deterministic adapters; passing them does not measure model quality. For packaging changes, also run `python scripts/package_release.py`, install the resulting wheel in a separate environment with `[ui,audio,agent]` and `httpx`, then run `python scripts/verify_release.py --no-models`.

UI/audio changes need actual browser checks: import, continuous playback, rapid seek, mute/solo, editing, undo, reopen and export. Polling, language changes and panel redraws must retain active audio sources and one transport clock. Compare exported audio when changing DSP. For UI changes, include screenshots in both languages and inspect narrow layouts and keyboard access.

## Translation

Workstation modules use paired Chinese/English messages and local translation helpers; `station.js` stores `station-language`. Home, lessons and AI setup have their own message definitions. The classic UI uses `i18n.js`; updating that file alone does not translate the workstation.

Follow the surrounding module's convention and check both languages. Never translate project names, lyrics, prompts or model output. Language switching must preserve playback, project state and pending work.

## Models and project integrity

Keep model runtimes isolated, pin code/weight revisions and hashes, and record their licenses separately. Results become typed candidates with source metadata; completion must not silently replace the arrangement. Adoption must support undo, save/reopen and export. Expose failures and cancellation with actionable diagnostics.

For model changes, use licensed frozen inputs and report hardware, versions, parameters, failures, quality and resource use. Reproduction and dataset rules are in [technical reference](docs/technical-reference.md) and [benchmarks](benchmarks/README.md). Keep confirmation assignments fixed and report regressions and training overlap. Do not commit private audio, reference lyric text, transcripts, credentials or weights.

Preserve timing units, immutable sources and optimistic revisions. Incompatible project-format changes require explicit schema/migration work; include history and portable-project checks. Never manufacture missing note/word times or present model scores as correctness probabilities.

## Releases and documentation

Write documentation for users or contributors who have not seen development discussions. Put current instructions in guides, future work in the roadmap, versioned measurements in technical reports and user-visible changes in release notes. Keep Chinese and English guides consistent.

Update the package version, changelog and `docs/releases/vX.Y.Z.md`. Validate the wheel and intended desktop/installer package, including a clean installation and project retention, before tagging. The [release workflow](.github/workflows/release.yml) validates tags and builds ZIP/wheel/sdist/checksums. It creates a prerelease **draft** when no release exists and preserves existing reviewed assets. Desktop installers and media require their separate packaging steps; review the final draft and checksums before publishing.
