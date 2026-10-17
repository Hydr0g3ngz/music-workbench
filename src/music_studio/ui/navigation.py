"""Resolve old local bookmarks without treating an audio asset as an arrangement."""

import re
from urllib.parse import urlencode


def entry_url(query) -> str:
    def identity(name):
        value = query.get(name, "")
        return value if re.fullmatch(r"[a-f0-9]{16}", value) else None

    project, session = identity("project"), identity("session")
    if project:
        values = {"project": project}
        if session:
            values["session"] = session
        return "/next.html?" + urlencode(values)
    if session:
        return "/station.html?" + urlencode({"session": session})
    return "/welcome.html"
