"""Check file links in tracked Markdown and prevent internal media/QA links."""

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse


def check(root: Path) -> tuple[int, list[str]]:
    if (root / ".git").exists():
        tracked = (
            subprocess.check_output(["git", "ls-files", "-z", "--", "*.md"], cwd=root)
            .decode("utf-8")
            .split("\0")
        )
    else:
        tracked = [str(p.relative_to(root)) for p in root.glob("*.md")]
        for directory in ("benchmarks", ".github"):
            tracked.extend(str(p.relative_to(root)) for p in (root / directory).rglob("*.md"))
    paths = {root / name for name in tracked if name and (root / name).exists()}
    paths.update((root / "docs").rglob("*.md"))
    errors = []
    for path in sorted(paths):
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```|~~~.*?~~~", "", text, flags=re.S)
        for match in re.finditer(r"!?\[[^\]]*\]\((<?[^\n)]+>?)\)", text):
            raw = match.group(1).strip().strip("<>")
            parsed = urlparse(raw)
            if parsed.scheme:
                prefix = "/Hydr0g3ngz/music-workbench/blob/main/"
                release_prefix = "/Hydr0g3ngz/music-workbench/releases/download/"
                if parsed.netloc == "github.com" and parsed.path.startswith(release_prefix):
                    tag, name = parsed.path[len(release_prefix) :].split("/", 1)
                    installer = re.fullmatch(r"Music-Workbench-[\w.]+-Setup-x64\.exe", name)
                    source = tag in ("v0.2.0.dev6", "v0.2.0.dev7") and name.endswith("-Windows.zip")
                    if not (
                        installer
                        or source
                        or name in ("SHA256SUMS.txt", "Music-Workbench-Examples.zip")
                    ):
                        errors.append(
                            f"{path.relative_to(root)}: retired release attachment {name}"
                        )
                if parsed.netloc == "github.com" and parsed.path.startswith(prefix):
                    target = root / unquote(parsed.path[len(prefix) :])
                else:
                    continue
            else:
                if not parsed.path:
                    continue
                target = path.parent / unquote(parsed.path)
            if not target.exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{path.relative_to(root)}:{line}: missing {raw}")
        if re.search(r"Media-Kit|Promo-1080p|Promo-Cover|Promo\.zh\.srt|launch-kit\.md", text):
            errors.append(f"{path.relative_to(root)}: promotional production asset link")
    return len(paths), errors


if __name__ == "__main__":
    count, failures = check(Path(__file__).resolve().parents[1])
    print(f"Checked {count} Markdown documents")
    for failure in failures:
        print(failure)
    raise SystemExit(bool(failures))
