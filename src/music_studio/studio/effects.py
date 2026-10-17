"""Streaming mix DSP. The AudioWorklet implements the same equations and signal order."""

import math

import numpy as np
from pydantic import Field
from scipy.signal import lfilter, sosfilt

from .models import StrictModel


class Equalizer(StrictModel):
    enabled: bool = False
    low_db: float = Field(default=0, ge=-12, le=12)
    mid_db: float = Field(default=0, ge=-12, le=12)
    high_db: float = Field(default=0, ge=-12, le=12)


class Compressor(StrictModel):
    enabled: bool = False
    threshold_db: float = Field(default=-18, ge=-48, le=0)
    ratio: float = Field(default=3, ge=1, le=12)
    attack_ms: float = Field(default=10, ge=1, le=100)
    release_ms: float = Field(default=150, ge=20, le=1000)
    makeup_db: float = Field(default=0, ge=0, le=12)


class Reverb(StrictModel):
    enabled: bool = False
    mix: float = Field(default=0.15, ge=0, le=1)
    decay: float = Field(default=1.2, ge=0.2, le=3)


class Effects(StrictModel):
    bypass: bool = False
    eq: Equalizer = Field(default_factory=Equalizer)
    compressor: Compressor = Field(default_factory=Compressor)
    reverb: Reverb = Field(default_factory=Reverb)


class Limiter(StrictModel):
    enabled: bool = False
    ceiling_db: float = Field(default=-1, ge=-12, le=-0.1)
    release_ms: float = Field(default=80, ge=20, le=500)


def tail(settings):
    if settings.bypass:
        return 0
    return max(
        0.15 if settings.eq.enabled else 0,
        settings.reverb.decay + 0.1 if settings.reverb.enabled and settings.reverb.mix > 0 else 0,
    )


def coefficients(kind, db, rate):
    """RBJ shelf (slope 1) and bell (Q=sqrt(1/2)), normalized a0=1."""
    frequency = {"low": 150, "mid": 1000, "high": 4000}[kind]
    a = 10 ** (db / 40)
    w = 2 * math.pi * frequency / rate
    c, s = math.cos(w), math.sin(w)
    alpha = s / math.sqrt(2)
    beta = 2 * math.sqrt(a) * alpha
    if kind == "mid":
        b = [1 + alpha * a, -2 * c, 1 - alpha * a]
        denominator = [1 + alpha / a, -2 * c, 1 - alpha / a]
    elif kind == "low":
        b = [
            a * (a + 1 - (a - 1) * c + beta),
            2 * a * (a - 1 - (a + 1) * c),
            a * (a + 1 - (a - 1) * c - beta),
        ]
        denominator = [
            a + 1 + (a - 1) * c + beta,
            -2 * (a - 1 + (a + 1) * c),
            a + 1 + (a - 1) * c - beta,
        ]
    else:
        b = [
            a * (a + 1 + (a - 1) * c + beta),
            -2 * a * (a - 1 + (a + 1) * c),
            a * (a + 1 + (a - 1) * c - beta),
        ]
        denominator = [
            a + 1 - (a - 1) * c + beta,
            2 * (a - 1 - (a + 1) * c),
            a + 1 - (a - 1) * c - beta,
        ]
    return np.array([*b, *denominator]) / denominator[0]


class PeakEnvelope:
    def __init__(self, rate, release_ms):
        self.rate, self.release_ms, self.value = rate, release_ms, 0.0

    def process(self, values):
        result = np.empty(len(values))
        # Bounded exponent range, independent of export block size.
        for start in range(0, len(values), 1024):
            block = values[start : start + 1024]
            weight = np.exp(np.arange(1, len(block) + 1) / (self.rate * self.release_ms / 1000))
            held = np.maximum.accumulate(np.maximum(block * weight, self.value)) / weight
            result[start : start + len(block)] = held
            self.value = held[-1]
        return result


class Delay:
    def __init__(self, length):
        self.buffer = np.zeros(length)
        self.position = 0

    def process(self, data, feedback, allpass=False):
        output = np.empty_like(data)
        for start in range(0, len(data), len(self.buffer)):
            block = data[start : start + len(self.buffer)]
            indexes = (np.arange(len(block)) + self.position) % len(self.buffer)
            old = self.buffer[indexes].copy()
            out = old - feedback * block if allpass else old
            self.buffer[indexes] = block + feedback * (out if allpass else old)
            output[start : start + len(block)] = out
            self.position = (self.position + len(block)) % len(self.buffer)
        return output


class Rack:
    def __init__(self, settings, rate=44100):
        self.settings, self.rate = settings, rate
        self.sos = np.array(
            [coefficients(k, getattr(settings.eq, k + "_db"), rate) for k in ("low", "mid", "high")]
        )
        self.eq_state = np.zeros((3, 2, 2))
        self.envelope = PeakEnvelope(rate, settings.compressor.release_ms)
        self.attack_state = np.zeros(1)
        self.combs = [
            [
                Delay(math.floor((d + channel * 0.0011) * rate + 0.5))
                for d in (0.0297, 0.0371, 0.0411, 0.0437)
            ]
            for channel in range(2)
        ]
        self.allpasses = [
            [Delay(math.floor(d * rate + 0.5)) for d in (0.005, 0.0017)] for _ in range(2)
        ]

    def process(self, data):
        settings = self.settings
        dry = data
        if settings.eq.enabled:
            data, self.eq_state = sosfilt(self.sos, data, axis=0, zi=self.eq_state)
        comp = settings.compressor
        if comp.enabled:
            held = self.envelope.process(np.max(np.abs(data), axis=1))
            alpha = math.exp(-1 / (self.rate * comp.attack_ms / 1000))
            smooth, self.attack_state = lfilter(
                [1 - alpha], [1, -alpha], held, zi=self.attack_state
            )
            over = np.maximum(0, 20 * np.log10(np.maximum(smooth, 1e-12)) - comp.threshold_db)
            data = data * (10 ** ((comp.makeup_db - over * (1 - 1 / comp.ratio)) / 20))[:, None]
        rev = settings.reverb
        if rev.enabled and rev.mix > 0:
            wet = np.zeros_like(data)
            for channel in range(2):
                for delay in self.combs[channel]:
                    feedback = 10 ** (-3 * len(delay.buffer) / (self.rate * rev.decay))
                    wet[:, channel] += delay.process(data[:, channel], feedback) * 0.25
                for delay in self.allpasses[channel]:
                    wet[:, channel] = delay.process(wet[:, channel], 0.5, allpass=True)
            data = data * (1 - rev.mix) + wet * rev.mix
        return dry if settings.bypass else data


class OutputLimiter:
    """Stereo linked, instantaneous sample-peak attack, exponential release; no lookahead."""

    def __init__(self, settings, rate=44100):
        self.settings = settings
        self.envelope = PeakEnvelope(rate, settings.release_ms)

    def process(self, data):
        if not self.settings.enabled:
            return data
        held = self.envelope.process(np.max(np.abs(data), axis=1))
        gain = np.minimum(1, 10 ** (self.settings.ceiling_db / 20) / np.maximum(held, 1e-12))
        return data * gain[:, None]
