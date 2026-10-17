"""One-level mix buses: post-fader sends and no feedback paths."""

from pydantic import Field

from .effects import Effects
from .models import StrictModel


class Send(StrictModel):
    bus: str = Field(pattern=r"^[a-f0-9]{16}$")
    gain_db: float = Field(default=-12, ge=-60, le=6)
    enabled: bool = True


class Bus(StrictModel):
    id: str = Field(pattern=r"^[a-f0-9]{16}$")
    name: str = Field(min_length=1, max_length=150)
    gain_db: float = Field(default=0, ge=-60, le=12)
    pan: float = Field(default=0, ge=-1, le=1)
    mute: bool = False
    solo: bool = False
    effects: Effects = Field(default_factory=Effects)


def validate(tracks, buses):
    identities = [b.id for b in buses]
    if len(set(identities)) != len(identities):
        raise ValueError("Bus identifiers must be unique")
    for track in tracks:
        if track.output is not None and track.output not in identities:
            raise ValueError("Track output bus does not exist")
        targets = [s.bus for s in track.sends]
        if len(set(targets)) != len(targets) or any(s not in identities for s in targets):
            raise ValueError("Sends need distinct existing buses")


def audible(track, tracks):
    return not track.mute and (not any(t.solo for t in tracks) or track.solo)


def bus_audible(bus, buses):
    return not bus.mute and (not any(b.solo for b in buses) or bus.solo)


def tail(track, buses):
    from .effects import tail as effect_tail

    destinations = {track.output, *(s.bus for s in track.sends if s.enabled)}
    return effect_tail(track.effects) + max(
        (effect_tail(b.effects) for b in buses if b.id in destinations and bus_audible(b, buses)),
        default=0,
    )
