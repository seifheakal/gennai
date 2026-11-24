"""Minimal local web UI: a chat-style page that starts a run and shows each phase as it ends.

It reuses run_pipeline (progress callback) and serves each run's own report.html. It listens
on 127.0.0.1 only, checks the Host header (DNS rebinding) and accepts runs only as JSON POSTs
from its own origin, so another website open in the browser can't start one.
"""

import json
import logging
import re
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from gennai import GennaiError
from gennai.config import load_settings
from gennai.notify import summary_text
from gennai.pipeline import run_paths, run_pipeline, serve_dir, site_name
from gennai.safety import check_url

log = logging.getLogger(__name__)
RUN_ID = r"\d{8}_\d{6}_\d{6}"
MAX_PAGES = 20
PAGE_CSP = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'"
)
REPORT_CSP = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:"
)

PAGE = """<!doctype html><html lang="en"><meta charset="utf-8"><title>GenNAI</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font:15px system-ui,sans-serif;max-width:760px;margin:0 auto;padding:16px;color:#222}
#log{display:flex;flex-direction:column;gap:8px;margin:16px 0}
.m{padding:8px 12px;border-radius:10px;max-width:85%;white-space:pre-wrap}
.you{align-self:flex-end;background:#dbeafe}.bot{align-self:flex-start;background:#f1f1f1}
form{display:flex;gap:8px}input[name=url]{flex:1;padding:8px}input[name=pages]{width:4em}
</style>
<h1>GenNAI</h1>
<p>Paste the URL of a page you may test, or type <code>demo</code>. Runs use the settings in
<code>.env</code> (LLM, login, notifications).</p>
<div id="log"></div>
<form id="f"><input name="url" placeholder="https://the-internet.herokuapp.com or demo" required>
<label>pages <input name="pages" type="number" min="1" max="20" value="1"></label>
<button>Test</button></form>
<script>
const log = document.getElementById('log'), form = document.getElementById('f');
function say(text, who, link) {
  const d = document.createElement('div'); d.className = 'm ' + who; d.textContent = text;
  if (link) { const a = document.createElement('a'); a.href = link; a.target = '_blank';
    a.textContent = 'Open the report'; d.append(document.createElement('br'), a); }
  log.append(d); d.scrollIntoView();
}
form.addEventListener('submit', async e => {
  e.preventDefault();
  const url = form.url.value.trim(), pages = Number(form.pages.value) || 1;
  say(url + (pages > 1 ? ' (up to ' + pages + ' pages)' : ''), 'you');
  form.querySelector('button').disabled = true;
  const r = await fetch('/api/run', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url, max_pages: pages})});
  const start = await r.json();
  if (!r.ok) { say(start.error, 'bot'); form.querySelector('button').disabled = false; return; }
  let seen = 0;
  const poll = async () => {
    const s = await (await fetch('/api/run/' + start.id)).json();
    s.messages.slice(seen).forEach((m, i) =>
      say(m, 'bot', s.done && s.report && seen + i === s.messages.length - 1 ? s.report : null));
    seen = s.messages.length;
    if (s.done) form.querySelector('button').disabled = false; else setTimeout(poll, 1000);
  };
  poll();
});
</script></html>"""


class _Run:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.done = False
        self.report: Path | None = None


class App:
    """Starts at most one run at a time in a background thread and keeps its messages."""

    def __init__(self, runs: Path = Path("runs")) -> None:
        self.runs_dir = runs
        self.runs: dict[str, _Run] = {}
        self.lock = threading.Lock()

    def start(self, target: str, max_pages: int) -> str | None:
        """Return the new run's id, or None while another run is still going."""
        with self.lock:
            if any(not r.done for r in self.runs.values()):
                return None
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            run = self.runs[run_id] = _Run()
        threading.Thread(target=self._work, args=(run, target, max_pages), daemon=True).start()
        return run_id

    def _work(self, run: _Run, target: str, max_pages: int) -> None:
        say = run.messages.append
        try:
            settings = load_settings()
            if target.lower() == "demo":
                out, history = run_paths("demo", settings, runs=self.runs_dir)
                with serve_dir() as url:
                    results = run_pipeline(url, out, settings, allow_local=True,
                                           max_pages=max_pages, history=history,
                                           progress=say)  # fmt: skip
            else:
                check_url(target)  # public targets only from the UI
                out, history = run_paths(site_name(target), settings, runs=self.runs_dir)
                results = run_pipeline(target, out, settings, max_pages=max_pages,
                                       history=history, progress=say)  # fmt: skip
            run.report = out / "report.html"
            say(summary_text(results, out))
        except GennaiError as e:
            say(f"Stopped: {e}")
        except Exception as e:  # keep the UI alive; details go to the terminal
            log.exception("run failed")
            say(f"Stopped: unexpected {type(e).__name__}; see the terminal")
        finally:
            run.done = True


class _Handler(BaseHTTPRequestHandler):
    app: App

    def log_message(self, format, *args):  # noqa: A002
        pass

    def _send(self, code: int, body: bytes, ctype: str, csp: str = PAGE_CSP) -> None:
        self.send_response(code)
        for k, v in (("Content-Type", ctype), ("Content-Length", str(len(body))),
                     ("Content-Security-Policy", csp), ("X-Content-Type-Options", "nosniff"),
                     ("Cache-Control", "no-store")):  # fmt: skip
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, data: dict) -> None:
        self._send(code, json.dumps(data).encode(), "application/json")

    def _own_host(self) -> bool:
        port = self.server.server_address[1]
        return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def do_GET(self):
        if not self._own_host():
            return self._json(403, {"error": "wrong Host header"})
        if self.path == "/":
            return self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        m = re.fullmatch(rf"/(api/run|report)/({RUN_ID})", self.path)
        run = self.app.runs.get(m.group(2)) if m else None
        if run is None:
            return self._json(404, {"error": "not found"})
        if m.group(1) == "api/run":
            report = f"/report/{m.group(2)}" if run.report else None
            return self._json(200, {"messages": run.messages, "done": run.done, "report": report})
        if run.report and run.report.exists():
            return self._send(200, run.report.read_bytes(), "text/html; charset=utf-8", REPORT_CSP)
        return self._json(404, {"error": "no report for this run"})

    def do_POST(self):
        origin = self.headers.get("Origin")
        if not self._own_host() or (origin and origin != f"http://{self.headers['Host']}"):
            return self._json(403, {"error": "requests are accepted only from this page"})
        if self.path != "/api/run":
            return self._json(404, {"error": "not found"})
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self._json(415, {"error": "send JSON"})
        try:
            length = int(self.headers["Content-Length"])
            if not 0 < length <= 10_000:
                raise ValueError("bad length")
            data = json.loads(self.rfile.read(length))
            url, pages = str(data["url"]).strip(), int(data.get("max_pages", 1))
        except (KeyError, TypeError, ValueError):
            return self._json(400, {"error": 'expected {"url": ..., "max_pages": n}'})
        if not url or not 1 <= pages <= MAX_PAGES:
            return self._json(400, {"error": f"give a URL and 1-{MAX_PAGES} pages"})
        run_id = self.app.start(url, pages)
        if run_id is None:
            return self._json(409, {"error": "a run is already going; wait for it to finish"})
        return self._json(200, {"id": run_id})


def make_server(port: int, app: App | None = None) -> ThreadingHTTPServer:
    handler = type("Handler", (_Handler,), {"app": app or App()})
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def serve(port: int) -> None:
    """Serve the UI until Ctrl+C."""
    server = make_server(port)
    print(f"GenNAI UI on http://127.0.0.1:{server.server_address[1]}/ (Ctrl+C stops it)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
