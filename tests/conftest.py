"""Unit tests must not discover or repair the developer's installed AI packs."""

import pytest


@pytest.fixture(autouse=True)
def isolated_user_data(tmp_path, monkeypatch, request):
    if not request.node.get_closest_marker("integration"):
        monkeypatch.setenv("MUSIC_WORKBENCH_DATA", str(tmp_path / "isolated-user-data"))
