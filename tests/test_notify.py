"""Notifications: all network calls are mocked."""

import io
import json
import logging
import urllib.error
from pathlib import Path

import pytest

from gennai import GennaiError
from gennai.config import Settings, load_settings
from gennai.notify import notify

HOOK = "https://hooks.example.com/services/T0/B0/secret-token"
RESULTS = {"url": "https://site.test/", "history": None, "summary": {
    "passed": 3, "failed": 1, "flaky": 0, "failures_per_class": {"assertion": 1}}}  # fmt: skip
OUT = Path("runs/site_1")


class FakeSMTP:
    sent: list = []

    def __init__(self, host, port, timeout, tls=True):
        self.tls, self.calls = tls, [("connect", host, port)]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        FakeSMTP.sent.append(self.calls)

    def has_extn(self, name):
        return self.tls

    def starttls(self, context):
        self.calls.append(("starttls",))

    def login(self, user, password):
        self.calls.append(("login", user))

    def send_message(self, msg):
        self.calls.append(("send", msg["To"], msg["Subject"], msg.get_content()))


def test_nothing_configured_sends_nothing(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: pytest.fail("sent"))
    assert notify(Settings(), RESULTS, OUT) == {}


def test_slack_posts_summary(monkeypatch):
    seen = []

    def urlopen(req, timeout):
        seen.append((req.full_url, json.loads(req.data)))
        return io.BytesIO(b"ok")

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    assert notify(Settings(slack_webhook_url=HOOK), RESULTS, OUT) == {"slack": "sent"}
    url, body = seen[0]
    assert url == HOOK
    assert body["text"] == (
        "GenNAI finished https://site.test/: 3 passed, 1 failed (assertion 1). "
        "Report: site_1/report.html"
    )


def test_slack_failure_is_reported_without_the_url(monkeypatch, caplog):
    def urlopen(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 404, "no", {}, io.BytesIO())  # type: ignore[arg-type]

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    with caplog.at_level(logging.WARNING):
        status = notify(Settings(slack_webhook_url=HOOK), RESULTS, OUT)
    assert status == {"slack": "failed: HTTP 404"}
    assert caplog.messages and not any("secret-token" in m for m in caplog.messages)


def test_email_uses_starttls_and_login(monkeypatch):
    FakeSMTP.sent = []
    monkeypatch.setattr("smtplib.SMTP", FakeSMTP)
    settings = Settings(smtp_host="smtp.test", smtp_user="me@site.test", smtp_password="pw-123",
                        email_from="me@site.test", email_to="qa@site.test")  # fmt: skip
    assert notify(settings, RESULTS, OUT) == {"email": "sent"}
    calls = FakeSMTP.sent[0]
    assert [c[0] for c in calls] == ["connect", "starttls", "login", "send"]
    assert calls[3][1:3] == ("qa@site.test", "GenNAI: 3 passed, 1 failed")
    assert "pw-123" not in repr(settings)


def test_email_refuses_password_without_tls(monkeypatch, caplog):
    FakeSMTP.sent = []
    monkeypatch.setattr("smtplib.SMTP", lambda h, p, timeout: FakeSMTP(h, p, timeout, tls=False))
    settings = Settings(smtp_host="smtp.test", smtp_user="me", smtp_password="pw-123",
                        email_to="qa@site.test")  # fmt: skip
    status = notify(settings, RESULTS, OUT)
    assert status["email"].startswith("failed: SMTPException: server offers no TLS")
    assert [c[0] for c in FakeSMTP.sent[0]] == ["connect"]  # no login, nothing sent
    assert not any("pw-123" in m for m in caplog.messages)


@pytest.mark.parametrize(
    ("url", "ok"),
    [(HOOK, True), ("http://127.0.0.1:9000/hook", True), ("http://hooks.example.com/x", False)],
)
def test_webhook_must_be_https_unless_local(monkeypatch, url, ok):
    monkeypatch.setattr("gennai.config.load_dotenv", lambda: None)
    monkeypatch.setenv("GENNAI_SLACK_WEBHOOK_URL", url)
    if ok:
        assert load_settings().slack_webhook_url == url
    else:
        with pytest.raises(GennaiError):
            load_settings()
