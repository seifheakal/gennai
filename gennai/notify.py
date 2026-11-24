"""Optional notifications when a run finishes: a Slack-compatible webhook and/or an email.

Both are off unless configured in .env. A failed notification is reported, never fatal. The
webhook URL (it contains a secret token) and the SMTP password are never logged.
"""

import json
import logging
import smtplib
import ssl
import urllib.error
import urllib.request
from email.message import EmailMessage
from pathlib import Path

from gennai.config import Settings

log = logging.getLogger(__name__)
TIMEOUT_S = 15


def summary_text(results: dict, out: Path) -> str:
    s = results["summary"]
    text = f"GenNAI finished {results['url']}: {s['passed']} passed, {s['failed']} failed"
    if s["failures_per_class"]:
        text += " (" + ", ".join(f"{k} {v}" for k, v in s["failures_per_class"].items()) + ")"
    if results.get("history"):
        text += f", {s['flaky']} flaky"
    return text + f". Report: {out.name}/report.html"


def _slack(url: str, text: str) -> None:
    body = json.dumps({"text": text}).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S):  # raises on HTTP >= 400
        pass


def _email(settings: Settings, subject: str, text: str) -> None:
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, settings.email_from, settings.email_to
    msg.set_content(text)
    host, port = settings.smtp_host, settings.smtp_port
    tls = ssl.create_default_context()
    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=TIMEOUT_S, context=tls)
    else:
        server = smtplib.SMTP(host, port, timeout=TIMEOUT_S)
    with server:
        if port != 465 and server.has_extn("starttls"):
            server.starttls(context=tls)
        elif port != 465 and settings.smtp_user:
            raise smtplib.SMTPException("server offers no TLS; not sending the password")
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


def _reason(e: Exception) -> str:
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}"
    return type(e).__name__ + (f": {e}" if isinstance(e, smtplib.SMTPException) else "")


def notify(settings: Settings, results: dict, out: Path) -> dict[str, str]:
    """Send the configured notifications; return {"slack"|"email": "sent" | "failed: ..."}."""
    s = results["summary"]
    subject = f"GenNAI: {s['passed']} passed, {s['failed']} failed"
    text, status = summary_text(results, out), {}
    channels = []
    if settings.slack_webhook_url:
        channels.append(("slack", lambda: _slack(settings.slack_webhook_url, text)))
    if settings.smtp_host and settings.email_to:
        channels.append(("email", lambda: _email(settings, subject, text)))
    for name, send in channels:
        try:
            send()
            status[name] = "sent"
        except (OSError, smtplib.SMTPException, ValueError) as e:  # URLError is an OSError
            status[name] = f"failed: {_reason(e)}"
            log.warning("%s notification failed: %s", name, _reason(e))
    return status
