import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.frontend import mount_frontend


def make_client(tmp_path):
    (tmp_path / "index.html").write_text("<h1>baf-home</h1>", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / ".secret").write_text("hidden", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("hidden", encoding="utf-8")

    app = FastAPI()

    @app.get("/api/ping")
    def ping():
        return {"ok": True}

    mount_frontend(app, str(tmp_path))
    return TestClient(app)


def test_index_and_assets_are_served(tmp_path):
    client = make_client(tmp_path)
    assert "baf-home" in client.get("/").text
    assert client.get("/app.js").status_code == 200


def test_api_routes_win_over_static_files(tmp_path):
    assert make_client(tmp_path).get("/api/ping").json() == {"ok": True}


def test_missing_file_is_404(tmp_path):
    assert make_client(tmp_path).get("/missing.js").status_code == 404


def test_hidden_files_are_not_served(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/.secret").status_code == 404
    assert client.get("/.git/config").status_code == 404


def test_missing_index_html_fails_fast(tmp_path):
    with pytest.raises(RuntimeError):
        mount_frontend(FastAPI(), str(tmp_path))


def test_empty_setting_mounts_nothing():
    app = FastAPI()
    before = len(app.routes)
    mount_frontend(app, "")
    assert len(app.routes) == before