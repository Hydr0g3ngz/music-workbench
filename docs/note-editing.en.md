# Turn estimated notes into your own part

[中文](note-editing.md) · [Model choices](models.en.md)

Select an audio clip and run **Basic Pitch** (single-instrument polyphony, CPU) or **Transkun** (piano only). Audition the synthesized result, then choose **Add notes to instrument track**. The recording stays intact. Change the new track's instrument and edit pitch, duration and velocity.

## When the notes are too dense

Double-click a MIDI clip, then choose **Simplify part**. Set a MIDI pitch range and minimum velocity. You can also keep only the highest or lowest note at nearby onsets. The grouping tolerance is in beats; this does not quantize onsets or shorten sustained notes.

**Upper echoes preset** starts with MIDI 60–108, minimum velocity 45 and highest note at nearby onsets. Narrow the register for your material, for example to 60–84. **Audition simplified part** before applying. Adjust or close to discard, or apply and undo afterward.

These are editorial rules, not AI error correction. A retained note may be wrong; a removed note may be real. Model velocities are estimates. Check recordings for accurate transcription. Separate complex mixes first; Transkun is not a mixed-instrument model.

## Adjust transitions together

Shift-click clips and open **Arrange / route → Clip groups** to apply gain or fades to the selection. Each clip receives the value. If any clip is too short or the fades are invalid, the entire operation is rejected. Each operation has its own undo step.

Copies of a group can develop independently. Start sparse, add a response, change the third section's texture, and lower/fade the return. See [After the Rain](creations/after-the-rain.md).
