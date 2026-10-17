import io
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from music_studio import workbench_cli
from music_studio.config import Settings
from music_studio.ui import server


def test_old_bookmarks_preserve_asset_and_arrangement_as_distinct_objects(tmp_path):
    with TestClient(server.create_app(tmp_path), base_url="http://127.0.0.1") as client:
        data = io.BytesIO()
        sf.write(data, np.zeros(4410), 44100, format="WAV")
        asset = client.post("/api/projects", files={"file": ("take.wav", data.getvalue())}).json()
        session = client.post("/api/workstation/projects", json={"title": "My music"}).json()
        asset_before = client.get(f"/api/projects/{asset['id']}/studio").json()
        session_before = client.get(f"/api/workstation/projects/{session['id']}").json()
        for path in ("/", "/index.html"):
            response = client.get(path, follow_redirects=False)
            assert response.status_code == 307
            assert response.headers["location"] == "/welcome.html"
            assert "Music Workbench" in client.get(path).text
            response = client.get(path, params={"project": asset["id"]}, follow_redirects=False)
            assert response.headers["location"] == f"/next.html?project={asset['id']}"
            response = client.get(path, params={"session": session["id"]}, follow_redirects=False)
            assert response.headers["location"] == f"/station.html?session={session['id']}"
        assert client.get(f"/api/projects/{asset['id']}/studio").json() == asset_before
        assert client.get(f"/api/workstation/projects/{session['id']}").json() == session_before
        assert client.get("/api/workstation/projects").json() == [session_before]
        assert client.app.title == "Music Workbench"
        assert client.get("/api/workstation/instance").json()["product"] == "music-workbench"


@pytest.mark.parametrize("query", [
    {"project": "//evil.example"}, {"session": "https://evil.example"},
    {"project": "../../other"}, {"next": "https://evil.example"},
    {"project": "1234567890abcdef<script>"},
])
def test_entry_never_redirects_to_supplied_paths(tmp_path, query):
    with TestClient(server.create_app(tmp_path), base_url="http://127.0.0.1") as client:
        response = client.get("/", params=query, follow_redirects=False)
        assert response.headers["location"] == "/welcome.html"


def test_public_cli_opens_creation_and_keeps_explicit_runtime_configuration(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(server, "serve", lambda *args: calls.append(args))
    assert workbench_cli.main([]) == 0
    workspace, settings, port, open_browser, interface = calls.pop()
    assert workspace == Path("outputs/workbench")
    assert settings.offline and port == 8920 and open_browser and interface == "create"
    assert "MusicWorkbench" in Settings().model_dir and "music-studio" not in Settings().model_dir
    assert workbench_cli.main([
        "ui", "--workspace", str(tmp_path), "--port", "8933", "--interface", "next",
        "--model-dir", str(tmp_path / "existing-models"), "--online",
        "--inference-python", str(tmp_path / "python.exe"),
    ]) == 0
    workspace, settings, port, open_browser, interface = calls.pop()
    assert workspace == tmp_path and port == 8933 and not open_browser and interface == "next"
    assert settings.model_dir == str(tmp_path / "existing-models")
    assert settings.inference_python == str(tmp_path / "python.exe") and not settings.offline


def test_public_cli_help_and_commands_describe_workbench(capsys):
    with pytest.raises(SystemExit) as result:
        workbench_cli.main(["--help"])
    assert result.value.code == 0
    help_text = capsys.readouterr().out
    assert "music-workbench" in help_text and "composition" in help_text
    assert "analyze" not in help_text and "song-analysis" not in help_text
    for arguments in (["analyze", "song.wav"], ["ui", "--interface", "classic"]):
        with pytest.raises(SystemExit) as result:
            workbench_cli.main(arguments)
        assert result.value.code == 2
