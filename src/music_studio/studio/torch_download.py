"""Resume large official Windows wheels and verify the SHA256 from PyTorch's index."""

import hashlib
import html
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def windows_wheel(package, python_tag, directory, *, version="2.10.0", flavor="cu128"):
    if (version, flavor) not in (("2.10.0", "cu128"), ("2.5.1", "cpu")):
        raise ValueError("Unsupported fixed Torch profile")
    name = f"{package}-{version}+{flavor}-{python_tag}-{python_tag}-win_amd64.whl"
    with urllib.request.urlopen(
        f"https://download.pytorch.org/whl/{flavor}/{package}/", timeout=30
    ) as response:
        index = response.read().decode("utf-8")
    matches = [
        html.unescape(link)
        for link in re.findall(r'href="([^"]+)"', index)
        if urllib.parse.unquote(link.split("#")[0]).endswith("/" + name)
    ]
    if not matches:
        raise RuntimeError("Official CUDA wheel not found: " + name)
    link = urllib.parse.urlsplit(matches[0])
    expected = urllib.parse.parse_qs(link.fragment)["sha256"][0]
    if not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise RuntimeError("The official wheel link has no valid checksum")
    # Avoid the large-file mirror which timed out on the first Windows test machine.
    url = urllib.parse.urlunsplit(("https", "download.pytorch.org", link.path, "", ""))
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    if target.is_file() and file_hash(target) == expected:
        return target
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as response:
        size = int(response.headers["Content-Length"])
    if not 0 < size < 5 * 1024**3:
        raise RuntimeError("Unexpected official wheel size")
    chunk = 16 * 1024**2
    parts = directory / (expected[:16] + ".parts")
    parts.mkdir(exist_ok=True)

    def fetch(index):
        first, last = index * chunk, min(size, (index + 1) * chunk) - 1
        part = parts / f"{index:04d}.part"
        if part.is_file() and part.stat().st_size == last - first + 1:
            return
        for attempt in range(4):
            try:
                request = urllib.request.Request(url, headers={"Range": f"bytes={first}-{last}"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    if (
                        response.status != 206
                        or response.headers.get("Content-Range") != f"bytes {first}-{last}/{size}"
                    ):
                        raise RuntimeError("Invalid HTTP range from official wheel server")
                    raw = response.read(last - first + 2)
                if len(raw) != last - first + 1:
                    raise RuntimeError("Incomplete wheel chunk")
                part.with_suffix(".tmp").write_bytes(raw)
                part.with_suffix(".tmp").replace(part)
                return
            except (OSError, ValueError, RuntimeError):
                if attempt == 3:
                    raise

    count = (size + chunk - 1) // chunk
    print(f"Downloading {name}: {size / 1024**3:.2f} GiB (resumable)", flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch, i) for i in range(count)]
        for done, future in enumerate(as_completed(futures), 1):
            future.result()
            if done % 10 == 0 or done == count:
                print(f"  {done}/{count} chunks", flush=True)
    assembled = target.with_suffix(".partial")
    with assembled.open("wb") as output:
        for index in range(count):
            output.write((parts / f"{index:04d}.part").read_bytes())
    if file_hash(assembled) != expected:
        raise RuntimeError(f"Wheel checksum mismatch; inspect the retained cache at {parts}")
    assembled.replace(target)
    print("Official SHA256 verified:", expected, flush=True)
    return target
