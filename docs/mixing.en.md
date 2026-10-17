# From draft to mix

[中文](mixing.md) · [Create workstation](create-preview.en.md)

Shape a mix with live track effects and optional master sample-peak limiting. No neural weights are needed; source audio stays immutable.

![Effects and multitrack arrangement](images/create-effects-en.png)

## Finish a small mix

1. Open a session and click a track's **FX** button, or choose **Effects** in the lower dock and select a track.
2. Try Clear voice, Warm keys, Tight drums or Ambient space, then play.
3. Enable or bypass individual EQ, compression and reverb modules. Track level and balance follow the effects.
4. Compare with **A/B dry**. Track bypass keeps the fader and master limiter active. Settings, bypass and reset autosave and support undo.
5. Enable master limiting if needed. Prefer small gain reductions; heavy limiting will not repair an overloaded mix.
6. Export a 24-bit/44.1 kHz stereo WAV with effects and tails. MIDI exports contain note data, not audio effects.

A/B does not loudness-match automatically; louder does not necessarily sound better. Added effects default off in existing sessions.
Presets are editable starting points, not automatic AI mastering.

## Signal path and controls

`clip/instrument → clip gain/fades → EQ → compressor → reverb → track fader/balance → sum → master fader → limiter`

| Module | Current implementation |
| --- | --- |
| EQ | RBJ biquads: 150 Hz low shelf, 1 kHz bell, 4 kHz high shelf; ±12 dB per band, bell Q=√½ |
| Compressor | Stereo-linked peak detector, hard knee; threshold, ratio, attack, release and manual makeup; no auto makeup or external sidechain |
| Reverb | Four parallel feedback combs and two series allpasses, with slightly different channel delays; wet mix 0–50%, nominal feedback decay 0.2–3 s |
| Master limiter | Optional stereo-linked instantaneous sample-peak attack with exponential release; ceiling −12 to −0.1 dBFS, default −1 dBFS |

The limiter is **not a true-peak limiter**. There is no oversampling or lookahead; heavy reduction distorts.
Reverb tails extend the export by nominal decay plus 0.1 s; EQ reserves at least 0.15 s.
Built-in processors use a fixed order. Reorderable chains, buses/sends, effect-parameter automation, VST and full mastering remain planned. For clip volume curves, see [Volume & transitions](volume-and-repaint.md).

## Playback, export and boundaries

AudioWorklet runs the browser effects on the audio thread. NumPy/SciPy renders export blocks with the same equations, delay lengths and order.
Live updates message existing processors rather than fetching, decoding or rebuilding sources. A/B transitions over 15 ms.
Pause explicitly disposes worklets, so disconnected processors do not keep processing.

Numerical parity is verified for playback from the start with fixed parameters; WAV adds 24-bit quantization and the browser graph uses Float32.
**Seek and resume rebuild filter, compressor and reverb state** without pre-rendering earlier material. The beginning can differ from uninterrupted playback; seeking into a tail alone can be silent.
Loops reuse effect graphs and retain tails across cycles. Discontinuous source boundaries can still click; see [Loop and metronome](timing.en.md). Live effect tweaks are not recorded as automation or exported as a time curve.
Effects need a modern browser and localhost/HTTPS. A worklet failure stops playback with an error instead of silently dropping effects.
The 32-track project limit is not a guarantee of real-time full-effects performance on every device.

With limiting disabled, the existing export overload guard still rejects WAV clipping and requests a lower master fader.
The master card displays actual sample peaks and overload warnings. Reduction readings represent recent audio blocks, not long-term maxima.

[技术验证 / Technical verification](feature-validation.md)。

Algorithm reference: RBJ formulas in the [W3C Audio EQ Cookbook](https://webaudio.github.io/Audio-EQ-Cookbook/audio-eq-cookbook.html), and the classic Schroeder reverb structure. Implementations: `studio/effects.py` and `ui/static/effects-dsp.js`; cross-language regression: `tests/test_mix_effects.py`.
