import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from music_studio.desktop import find_instance, probe, workspace_id
from music_studio.io import write_json


def test_local_identity_probe_ignores_version_but_rejects_wrong_workspace(tmp_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            import json

            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "product": "music-workbench",
                        "workspace": workspace_id(tmp_path),
                        "version": "fixture",
                    }
                ).encode()
            )

        def log_message(self, *_):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        assert probe(url, tmp_path)["version"] == "fixture"
        assert probe(url, tmp_path / "other") is None
        assert probe("https://example.com", tmp_path) is None
        assert probe("http://127.0.0.1:1234@example.com", tmp_path) is None
        assert probe("http://127.0.0.1:1234/wrong-path", tmp_path) is None
        write_json(tmp_path / ".workbench-instance.json", {"url": url})
        assert find_instance(tmp_path) == {"url": url}
    finally:
        server.shutdown()
        server.server_close()
    assert find_instance(tmp_path) is None


def test_workspace_fingerprint_is_resolved_not_a_user_visible_absolute_path(tmp_path):
    assert workspace_id(tmp_path) == workspace_id(tmp_path / "x" / "..")
    assert len(workspace_id(tmp_path)) == 64
    assert workspace_id(tmp_path) != workspace_id(Path(tmp_path) / "another")
