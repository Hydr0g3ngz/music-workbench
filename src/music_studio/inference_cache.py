"""Opt-in model reuse inside a single, serially owned capability worker."""

import gc
import os

_MODELS = {}
_HITS = 0


def inference_model(key, factory):
    global _HITS
    if not (
        os.environ.get("MUSIC_STUDIO_REUSE_RECOGNIZER") == "1"
        or os.environ.get("MUSIC_WORKBENCH_REUSE_MODEL") == "1"
    ):
        return factory()
    if key not in _MODELS:
        _MODELS[key] = factory()
    else:
        _HITS += 1
    return _MODELS[key]


def cache_hits():
    return _HITS


def clear_models():
    _MODELS.clear()
    gc.collect()
