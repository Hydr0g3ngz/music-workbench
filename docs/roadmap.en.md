# Product and open-source roadmap

> Historical reference for the Studio analysis workflow or a pre-split build. Start with [current Workbench documentation](README.en.md). The analysis product is maintained in [Music Studio](https://github.com/Hydr0g3ngz/music-studio). Commands and measurements below apply to the stated historical version.

[中文](roadmap.md) · [Contributing](../CONTRIBUTING.md)

Music Studio helps people listen to a song's layers, correct lyrics and export
usable results. This archived plan covers the analysis product.

## Included in 0.1.1 preview

- Local timeline, stems, lyric correction, version comparison and explicit candidate acceptance.
- Stable lazy-loaded playback, sing-along mode and recoverable song deletion.
- Chinese/English UI, saved language preference, bilingual onboarding and repository guides.
- Credited precomputed 45-second demo, usable without neural-model downloads.
- Windows launcher, preview/full setup modes, wheel/source/ZIP/checksums and a release workflow.
- Frozen 43-case evaluation with language/domain splits, provenance and disclosed regressions.

The Windows ZIP requires Python and first-time dependency installation. A bundled
standalone runtime and a full GUI model manager are still future work.

## Next priorities

| Priority | Work | Acceptance |
| --- | --- | --- |
| P0 | Clean-machine CPU/CUDA installation | Record first install, model download, startup and recovery on independent Windows machines; distinguish this from local clean-venv tests |
| P0 | Model manager and standalone Windows runtime | Show installed/missing models, exact sizes, download/resume/hash status; no silent multi-GB downloads; validate worker processes in a bundled runtime |
| P1 | Pitch-preserving slow practice and A/B loops | 0.75x/1x playback without pitch drift; all stems/lyrics stay synchronized across seeking and loops |
| P1 | Export selection and project backup | Show actually available formats; round-trip a backup including edits, versions and attribution |
| P1 | Keyboard help and accessibility | Discoverable shortcuts; no playback shortcuts while typing; both languages and narrow screens verified |
| P2 | Singing-specific alignment | Compare SOFA-style candidates with the same inputs; report coverage, end-to-end 200ms and timing tails on a new confirmation split |
| P2 | Better vocal-melody backend | Compare ROSVOT-style candidates to CREPE on the same suite; onset/pitch/offset F1, octave errors and resource use |
| P2 | ASS sing-along subtitles | Animate only reliably timed acoustic units; preserve sentence-only text and provide licensed font/sample attribution |

Keep lyric editing focused on text correction. Full notation editing and a DAW
would expand scope beyond the current use case. No background telemetry is planned;
start with voluntary, reproducible issues about installation and real workflows.

Useful upstream references: [UVR](https://github.com/Anjok07/ultimatevocalremovergui)
for distribution, [ASRU annotations](https://github.com/navi0105/LyricAlignment)
for traceable evaluation, [SOFA](https://github.com/qiuqiao/SOFA) and
[ROSVOT](https://github.com/RickyL-2000/ROSVOT) as future algorithm candidates.
SOFA and ROSVOT have not been evaluated in this project yet.
