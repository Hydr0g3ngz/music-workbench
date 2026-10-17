"""Editable musical intentions and deterministic context for local generation.

These are creative requests, never a claim that a model complied or a quality score.
"""

import hashlib
import json
from typing import Literal

from pydantic import Field

from .models import StrictModel
from .service import StudioError

Role = Literal["free", "intro", "theme", "build", "peak", "contrast", "return", "outro"]
Development = Literal["establish", "repeat", "develop", "contrast", "resolve", "transition"]


class Blueprint(StrictModel):
    brief: str = Field(default="", max_length=320)
    palette: str = Field(default="", max_length=240)
    motif: str = Field(default="", max_length=240)
    harmony: str = Field(default="", max_length=240)


class ContextRequest(StrictModel):
    use_blueprint: bool = False
    section_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{16}$")
    development: Development = "establish"


ROLE_DIRECTIONS = {
    "intro": "Introduce the sound palette with space; foreshadow the motif.",
    "theme": "State the main motif clearly with a stable supporting groove.",
    "build": "Develop the established material and gradually build tension.",
    "peak": "Deliver the intended high point with a clear foreground motif.",
    "contrast": "Create contrast in texture or rhythm while retaining a musical connection.",
    "return": "Bring back the established motif with a recognizable variation.",
    "outro": "Resolve the musical tension and reduce layers toward the ending.",
}
DEVELOPMENTS = {
    "establish": "Introduce a concise, memorable motif; leave space between phrases.",
    "repeat": "Keep the main motif and groove recognizable; use restrained changes.",
    "develop": "Retain the motif identity; vary rhythm, register or instrumentation.",
    "contrast": "Contrast the previous texture using space, rhythm or a different register.",
    "resolve": "Restate or resolve the motif and gradually simplify the texture.",
    "transition": "Create a short connective gesture leading into the next section.",
}


def compile_context(state, prompt, options):
    """Resolve only server-stored state; preview and queue use this exact compiler."""
    if not options.use_blueprint:
        if options.section_id:
            raise StudioError("Enable project context before selecting a section")
        return {"prompt": prompt, "context": None}
    content = state["content"]
    sections = sorted(content.get("sections", []), key=lambda item: (item["start"], item["id"]))
    section = next((s for s in sections if s["id"] == options.section_id), None)
    if options.section_id and section is None:
        raise StudioError("Section no longer exists; choose a section again", 409)
    blueprint = Blueprint.model_validate(content.get("blueprint", {})).model_dump()
    context = {
        "compiler_version": 1,
        "project": state["id"],
        "revision": state["revision"],
        "bpm": content["bpm"],
        "key": content.get("key", ""),
        "blueprint": blueprint,
        "section": dict(section) if section else None,
        "development": options.development,
        "neighbors": {},
    }
    parts = [prompt, "Project musical intentions (requested, not verified):"]
    for field, label in (
        ("brief", "Creative brief"),
        ("palette", "Instrument palette"),
        ("motif", "Motif to preserve"),
        ("harmony", "Harmonic direction"),
    ):
        if blueprint[field].strip():
            parts.append(f"{label}: {blueprint[field].strip()}")
    parts.append(f"Target tempo: {content['bpm']:g} BPM; meter: 4/4.")
    if context["key"]:
        parts.append("Requested key: " + context["key"] + ".")
    if section:
        i = sections.index(section)
        for label, j in (("previous", i - 1), ("next", i + 1)):
            if 0 <= j < len(sections):
                neighbor = sections[j]
                context["neighbors"][label] = {
                    key: neighbor.get(key) for key in ("name", "role", "energy", "intention")
                }
                parts.append(
                    f"{label.capitalize()} section: {neighbor['name']} "
                    f"({neighbor.get('role', 'free')})."
                )
        seconds = (section["end"] - section["start"]) * 60 / content["bpm"]
        context["section_seconds"] = seconds
        parts.append(f"Target section: {section['name']}; planned length: {seconds:g} seconds.")
        if direction := ROLE_DIRECTIONS.get(section.get("role")):
            parts.append(direction)
        if section.get("energy") is not None:
            parts.append(
                f"Intended relative energy: {section['energy']}/5 "
                "(within this piece, not a loudness target)."
            )
        if section.get("intention", "").strip():
            parts.append("Section intention: " + section["intention"].strip())
    parts.append(DEVELOPMENTS[options.development])
    # Hash the pinned context, including revision and uncompiled structured intentions.
    context["sha256"] = hashlib.sha256(
        json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {"prompt": "\n".join(parts), "context": context}
