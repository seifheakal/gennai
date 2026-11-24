"""Web UI: a real local server running a demo run end to end, plus its request guards."""

import http.client
import json
import threading
import time

import pytest

from gennai.web import App, make_server


@pytest.fixture
def ui(tmp_path, monkeypatch):
    for name in ("GENNAI_LLM_PROVIDERS", "GENNAI_SLACK_WEBHOOK_URL", "GENNAI_SMTP_HOST",
                 "GENNAI_LOGIN_URL", "GENNAI_LOGIN_USER", "GENNAI_LOGIN_PASSWORD"):  # fmt: skip
        monkeypatch.setenv(name, "none" if name == "GENNAI_LLM_PROVIDERS" else "")
    monkeypatch.setenv("GENNAI_HISTORY_DIR", str(tmp_path / "history"))
    server = make_server(0, App(tmp_path / "runs"))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]

    def call(method, path, body=None, **headers):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        headers.setdefault("Host", f"127.0.0.1:{port}")
        conn.request(method, path, body, headers)
        resp = conn.getresponse()
        return resp.status, resp.getheader("Content-Security-Policy"), resp.read()

    yield call
    server.shutdown()
    server.server_close()


def test_demo_run_through_the_ui(ui, tmp_path):
    status, csp, page = ui("GET", "/")
    assert status == 200 and b"GenNAI" in page and "connect-src 'self'" in csp
    run = json.dumps({"url": "demo", "max_pages": 2})
    status, _, body = ui("POST", "/api/run", run, **{"Content-Type": "application/json"})
    assert status == 200
    run_id = json.loads(body)["id"]
    busy = ui("POST", "/api/run", run, **{"Content-Type": "application/json"})
    assert busy[0] == 409  # one run at a time
    for _ in range(240):
        state = json.loads(ui("GET", f"/api/run/{run_id}")[2])
        if state["done"]:
            break
        time.sleep(0.5)
    messages = state["messages"]
    assert [m.split(":")[0] for m in messages[1:5]] == ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
    assert "on 2 page(s)" in messages[1]
    assert messages[-1].startswith("GenNAI finished") and state["report"] == f"/report/{run_id}"
    status, csp, report = ui("GET", state["report"])
    assert status == 200 and b"GenNAI report" in report and "connect-src" not in csp
    assert list((tmp_path / "runs").glob("demo_*/report.html"))
    assert (tmp_path / "history" / "demo.jsonl").exists()


@pytest.mark.parametrize(
    ("method", "path", "headers", "code"),
    [
        ("GET", "/", {"Host": "evil.test"}, 403),  # DNS rebinding
        ("POST", "/api/run", {"Content-Type": "text/plain"}, 415),  # a cross-site form post
        ("POST", "/api/run", {"Content-Type": "application/json", "Origin": "http://evil.test"},
         403),
        ("GET", "/report/../../.env", {}, 404),
        ("GET", "/api/run/20260101_000000_000000", {}, 404),
    ],
)  # fmt: skip
def test_request_guards(ui, method, path, headers, code):
    body = json.dumps({"url": "demo"}) if method == "POST" else None
    assert ui(method, path, body, **headers)[0] == code


def test_ui_refuses_local_targets(ui):
    run = json.dumps({"url": "http://127.0.0.1:9/"})
    _, _, body = ui("POST", "/api/run", run, **{"Content-Type": "application/json"})
    run_id = json.loads(body)["id"]
    for _ in range(40):
        state = json.loads(ui("GET", f"/api/run/{run_id}")[2])
        if state["done"]:
            break
        time.sleep(0.25)
    assert state["messages"][-1].startswith("Stopped: refusing http://127.0.0.1:9/")
