"""Settings loaded from the environment (and an optional .env file)."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

from gennai import GennaiError

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


@dataclass(frozen=True)
class Provider:
    """One OpenAI-compatible LLM endpoint. The key is never logged or printed."""

    name: str
    api_key: str = field(repr=False)
    model: str
    base_url: str
    rpm: int


@dataclass(frozen=True)
class Settings:
    page_timeout_ms: int = 30000  # initial page load
    action_timeout_ms: int = 5000  # per action in generated tests
    settle_ms: int = 2000  # wait after load so late elements appear
    max_elements: int = 40
    max_tests: int = 25
    run_timeout_s: int = 600  # generated pytest run
    log_level: str = "INFO"
    llm_providers: tuple[Provider, ...] = ()  # configured providers, in fallback order
    llm_max_calls: int = 3  # hard cap on HTTP attempts per run
    llm_max_output_tokens: int = 4096
    llm_timeout_s: int = 120  # thinking models (e.g. Gemma) can take a minute
    llm_max_input_chars: int = 12000
    history_dir: str = "runs/history"  # one append-only <site>.jsonl per site
    flaky_window: int = 5  # a test is flaky if it passed and failed within this many runs
    login_url: str = ""  # with user and password: log in before exploring and in each test run
    login_user: str = field(default="", repr=False)
    login_password: str = field(default="", repr=False)


def _positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value <= 0:
        raise GennaiError(f"{name} must be a positive integer")
    return value


def _providers() -> tuple[Provider, ...]:
    raw = os.environ.get("GENNAI_LLM_PROVIDERS", "").strip() or "gemini,gemma,openrouter"
    out = []
    for name in (n.strip().lower() for n in raw.split(",")):
        if not name:  # a name without a key (e.g. "none") is skipped below
            continue
        prefix = name.upper()
        key = os.environ.get(f"{prefix}_API_KEY", "").strip()
        if not key:
            continue
        model = os.environ.get(f"{prefix}_MODEL", "").strip()
        base_url = os.environ.get(f"{prefix}_BASE_URL", "").strip()
        for var, val in ((f"{prefix}_MODEL", model), (f"{prefix}_BASE_URL", base_url)):
            if not val:
                raise GennaiError(f"{var} must be set when {prefix}_API_KEY is set")
        if not base_url.startswith("https://"):  # the key is sent as a bearer token
            raise GennaiError(f"{prefix}_BASE_URL must start with https://")
        rpm = _positive_int(f"{prefix}_RPM", 10)
        out.append(Provider(name, key, model, base_url.rstrip("/"), rpm))
    return tuple(out)


def _login() -> tuple[str, str, str]:
    names = ("GENNAI_LOGIN_URL", "GENNAI_LOGIN_USER", "GENNAI_LOGIN_PASSWORD")
    values = tuple(os.environ.get(n, "").strip() for n in names)
    if any(values) and not all(values):
        raise GennaiError(f"set all of {', '.join(names)} to log in, or none of them")
    if values[0] and not values[0].startswith(("http://", "https://")):
        raise GennaiError("GENNAI_LOGIN_URL must start with http:// or https://")
    return values  # type: ignore[return-value]


def load_settings() -> Settings:
    """Read GENNAI_* variables, validating each; fails fast naming the bad variable."""
    load_dotenv()
    level = os.environ.get("GENNAI_LOG_LEVEL", "").strip().upper() or "INFO"
    if level not in LOG_LEVELS:
        raise GennaiError(f"GENNAI_LOG_LEVEL must be one of {', '.join(LOG_LEVELS)}")
    d = Settings()
    login_url, login_user, login_password = _login()
    return Settings(
        page_timeout_ms=_positive_int("GENNAI_PAGE_TIMEOUT_MS", d.page_timeout_ms),
        action_timeout_ms=_positive_int("GENNAI_ACTION_TIMEOUT_MS", d.action_timeout_ms),
        settle_ms=_positive_int("GENNAI_SETTLE_MS", d.settle_ms),
        max_elements=_positive_int("GENNAI_MAX_ELEMENTS", d.max_elements),
        max_tests=_positive_int("GENNAI_MAX_TESTS", d.max_tests),
        run_timeout_s=_positive_int("GENNAI_RUN_TIMEOUT_S", d.run_timeout_s),
        log_level=level,
        llm_providers=_providers(),
        llm_max_calls=_positive_int("GENNAI_LLM_MAX_CALLS", d.llm_max_calls),
        llm_max_output_tokens=_positive_int(
            "GENNAI_LLM_MAX_OUTPUT_TOKENS", d.llm_max_output_tokens
        ),
        llm_timeout_s=_positive_int("GENNAI_LLM_TIMEOUT_S", d.llm_timeout_s),
        llm_max_input_chars=_positive_int("GENNAI_LLM_MAX_INPUT_CHARS", d.llm_max_input_chars),
        history_dir=os.environ.get("GENNAI_HISTORY_DIR", "").strip() or d.history_dir,
        flaky_window=_positive_int("GENNAI_FLAKY_WINDOW", d.flaky_window),
        login_url=login_url,
        login_user=login_user,
        login_password=login_password,
    )
