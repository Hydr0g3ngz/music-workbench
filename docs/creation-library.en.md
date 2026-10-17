# Sampled instruments, grooves and MIDI

[中文](creation-library.md) · [Start the workstation](create-preview.en.md)

Audition a sound or groove, then add it to the multitrack project. The starter instruments
ship with the application alongside three synth sounds and need no model download, GPU or connection.

## Start arranging

1. Open Instruments, audition the sampled grand piano, marimba or acoustic kit, then click
   the instrument card to add a track.
2. Audition one of eight grooves in Assets. Click `＋` or drag it into the arrangement.
   Each two-bar performance follows the session tempo.
3. Double-click a MIDI clip to open the piano roll. Double-click to add/remove notes;
   select a note and edit pitch, beat position, duration or velocity in the Inspector.
   Kit keys show kick, snare, hat and cymbal names.
4. Import `.mid` / `.midi` through Import audio / MIDI. The confirmation shows parts,
   notes, duration, initial tempo and conversion details.
5. Save, undo, reopen, change instruments, mix and export WAV/MIDI within the same session.

Narrow windows retain the session/new controls and rail buttons for the library and Inspector.
Auditioning does not add tracks. Task polling does not reload playing audio or samples.

## Included assets

| Asset | Implementation | Source / license |
| --- | --- | --- |
| Piano | 9 root samples, transposed from the nearest root | VCSL, CC0 |
| Marimba | 5 root samples, nearest-root transposition | VCSL, CC0 |
| Drum kit | 9 one-shots with common GM mappings; subsequent hats choke previous hats | VCSL, CC0 |
| Grooves | Two bars each: pop, rock, funk, hip-hop, soul, jazz, Latin and Afrobeat | Groove MIDI Dataset, CC BY 4.0 |

The 23 FLAC files total approximately 3.6 MB. This is a compact, single-velocity selection,
not the complete VCSL, an SFZ player, a professional drum library or a VST host. Unmapped
percussion uses a closed-hat approximation; original notes survive and the importer warns.
Velocity changes level. Multilayer sampling, sympathetic pedal resonance and round robins
are not implemented.

Browser audition and offline WAV export use the same assets and note semantics, including
attack, note-off release and hat choking. Browser sample rate and interpolation can differ;
bit-identical playback/export is not claimed. MIDI export includes programs and drum channel 10.

## MIDI conversion limits

- Standard MIDI File 0/1; at most 8 MiB, 128 MIDI tracks, 8192 notes, 32 parts and 10 minutes.
- Pitch, velocity and performance times survive. Tempo maps become positions on a fixed
  session grid; CC64 sustain extends note durations.
- Only an empty session can adopt the initial BPM. Non-4/4 note times survive on a 4/4 display.
- Dense parts are split across clips without dropping notes.
- Some programs are approximated by piano, marimba, bass or drums. Pitch bends, other
  controllers and automation are not imported yet.
- SMF 2, SMPTE timebases and oversized inputs are rejected explicitly.
- Original MIDI bytes are archived by SHA256 under `.midi-originals`; conversion never overwrites them.

## Sources and attribution

Samples come from [VCSL](https://github.com/sgossner/VCSL), pinned to
`c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e`. Changes include onset trimming,
normalization, duration trimming/fades and format conversion.

Grooves are eight two-bar excerpts from the training split of
[Groove MIDI Dataset](https://magenta.withgoogle.com/datasets/groove) v1.0.0.
Human microtiming/velocity survive; note gates and a few drum aliases are adjusted.
Credit Jon Gillick, Adam Roberts, Jesse Engel, Douglas Eck, David Bamman, Google LLC
and the drummers identified in the manifest. These training assets do not establish test-set scores.

Export → Sources and attribution produces credits for templates actually used in the session.
See `src/music_studio/data/creation/NOTICE.md` and `manifest.json` for licenses, modifications,
source/derived hashes and exact filenames. `python scripts/build_creation_library.py` explicitly
rebuilds the pack over the network; normal application startup never invokes it.

[技术验证 / Technical verification](feature-validation.md)。
