"""Optional LLM step: propose extra test cases, gated by safety.gate_llm_cases."""

import http.client
import json
import logging
import math
import time
import urllib.error
import urllib.request

from gennai import GennaiError
from gennai.config import Provider, Settings
from gennai.phase2_generate import Case
from gennai.safety import build_prompt, gate_llm_cases

log = logging.getLogger(__name__)
NOT_USED = "not used: no LLM key configured (set GEMINI_API_KEY or OPENROUTER_API_KEY in .env)"
RETRIES = 2
DEFAULT_COOLDOWN_S = 60.0


class LLMUnavailable(GennaiError):
    """No provider could answer (cap reached, rate limited, or failing)."""


class _Client:
    def __init__(self, settings: Settings) -> None:
        self.s = settings
        self.calls = 0
        self.last_call: dict[str, float] = {}
        self.cooldown_until: dict[str, float] = {}
        self.reasons: dict[str, str] = {}

    def _unavailable(self, why: str = "") -> LLMUnavailable:
        parts = [f"{n}: {r}" for n, r in self.reasons.items()]
        return LLMUnavailable("; ".join(([why] if why else []) + parts) or "no provider left")

    def _post(self, p: Provider, system: str, user: str) -> str:
        body = {
            "model": p.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": self.s.llm_max_output_tokens,
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            f"{p.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {p.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "gennai",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.s.llm_timeout_s) as resp:
            data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError("content is not a string")
        return content

    def _space(self, p: Provider) -> None:
        """Wait so that calls to one provider are at least 60/RPM seconds apart."""
        wait = self.last_call.get(p.name, -math.inf) + 60 / p.rpm - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self.last_call[p.name] = time.monotonic()

    def _cool_down(self, p: Provider, err: urllib.error.HTTPError) -> None:
        try:
            text = err.read().decode("utf-8", "replace").lower()
        except OSError:
            text = ""
        retry_after = (err.headers.get("Retry-After") if err.headers else None) or ""
        if retry_after.strip().isdigit():
            wait = float(retry_after)
        elif "daily" in text or "per day" in text:
            wait = math.inf
        else:
            wait = DEFAULT_COOLDOWN_S
        self.cooldown_until[p.name] = time.monotonic() + wait

    def complete(self, system: str, user: str) -> tuple[str, Provider]:
        """Try providers in order; return (answer, provider) or raise LLMUnavailable."""
        for p in self.s.llm_providers:
            if self.cooldown_until.get(p.name, -math.inf) > time.monotonic():
                self.reasons[p.name] = "cooling down after rate limit"
                continue
            for attempt in range(RETRIES + 1):
                if self.calls >= self.s.llm_max_calls:
                    raise self._unavailable(f"call cap {self.s.llm_max_calls} reached")
                self._space(p)
                self.calls += 1
                try:
                    return self._post(p, system, user), p
                except urllib.error.HTTPError as e:
                    self.reasons[p.name] = f"HTTP {e.code}"
                    log.warning("LLM %s answered HTTP %s", p.name, e.code)
                    if e.code == 429:
                        self._cool_down(p, e)
                        break
                    if e.code < 500:
                        break
                except (
                    urllib.error.URLError,
                    http.client.HTTPException,
                    TimeoutError,
                    OSError,
                ) as e:
                    self.reasons[p.name] = f"network error ({type(e).__name__})"
                    log.warning("LLM %s network error: %s", p.name, type(e).__name__)
                except (ValueError, KeyError, IndexError, TypeError):
                    self.reasons[p.name] = "malformed response"
                    log.warning("LLM %s returned a malformed response", p.name)
                    break
                if attempt < RETRIES:
                    time.sleep(2**attempt)
        raise self._unavailable()


def propose_cases(url: str, elements: list[dict], settings: Settings) -> tuple[list[Case], dict]:
    """Ask the configured LLM for extra cases; never raises (falls back to no extra cases)."""
    if not settings.llm_providers:
        return [], {"status": NOT_USED}
    system, user = build_prompt(url, elements, settings.llm_max_input_chars)
    log.debug("LLM system prompt:\n%s\nLLM user prompt:\n%s", system, user)
    client = _Client(settings)
    try:
        text, provider = client.complete(system, user)
    except LLMUnavailable as e:
        log.warning("LLM unavailable: %s", e)
        status = f"unavailable: {e}; used the algorithmic generators only"
        return [], {"status": status, "calls": client.calls}
    cases, stats = gate_llm_cases(text, elements)
    stats |= {"status": f"used: {provider.name}/{provider.model}", "calls": client.calls}
    log.info("LLM proposed %d, accepted %d cases", stats["proposed"], stats["accepted"])
    return cases, stats
