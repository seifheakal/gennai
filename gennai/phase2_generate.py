"""Phase 2: derive test cases from elements (equivalence partitioning, BVA, state, click)."""

from collections import defaultdict
from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, ConfigDict

TEXTY = ("text", "password", "phone")  # kinds where "a" * n is valid text
FIELDS = ("email", "number", "phone", "password", "text", "select", "checkbox", "radio")
MAX_LEN = 1000  # skip length boundaries above this
MAX_STATE_OMISSIONS = 3
IMPORTANCE = {
    "email": 1.0, "password": 1.0, "button": 0.9, "number": 0.8, "phone": 0.8, "text": 0.7,
    "select": 0.6, "checkbox": 0.6, "radio": 0.6, "link": 0.3,
}  # fmt: skip
TECHNIQUE_WEIGHT = {"state": 1.0, "click": 0.9, "bva": 0.8, "ep": 0.7, "llm": 0.75}


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Step(_Model):
    element: str
    action: Literal["fill", "select", "check"]
    value: str = ""


class Case(_Model):
    id: str = ""
    title: str
    technique: Literal["ep", "bva", "state", "click", "llm"]
    steps: list[Step] = []
    target: str  # element the expectation is asserted on
    expect: Literal[
        "valid", "invalid", "max_length", "selected", "checked", "clickable",
        "form_valid", "form_invalid",
    ]  # fmt: skip
    limit: int | None = None  # maxlength for expect="max_length"
    priority: float = 0.0


def _num(s: str | None) -> float | None:
    try:
        return float(s) if s not in (None, "") else None
    except ValueError:
        return None


def _int(s: str | None) -> int | None:
    n = _num(s)
    return int(n) if n is not None and n >= 0 else None


def _fmt(n: float) -> str:
    return str(int(n)) if n == int(n) else str(n)


def _name(el: dict) -> str:
    return (
        el.get("label") or el.get("aria_label") or el.get("placeholder")
        or el.get("text") or el.get("name") or el.get("dom_id") or el["tag"]
    )  # fmt: skip


def _valid_value(el: dict) -> str | None:
    """A clearly fake value that should satisfy the element's constraints."""
    kind = el["kind"]
    if kind == "email":
        return "test.user@example.com"
    if kind == "number":
        lo, hi = _num(el["min"]), _num(el["max"])
        return _fmt(lo if lo is not None else hi if hi is not None else 42)
    if kind == "select":
        return next((o["value"] for o in el["options"] or [] if o["value"]), None)
    if kind in ("checkbox", "radio"):
        return ""
    text = (
        "+15555550123"
        if kind == "phone"
        else "Passw0rd!test"
        if kind == "password"
        else "Test User"
    )
    text = text.ljust(_int(el["minlength"]) or 0, "x")
    mx = _int(el["maxlength"])
    return text[:mx] if mx else text


def _step(el: dict, value: str) -> Step:
    action = {"select": "select", "checkbox": "check", "radio": "check"}.get(el["kind"], "fill")
    return Step(element=el["id"], action=action, value=value)


def _case(el: dict, technique: str, title: str, value: str | None, expect: str, **kw) -> Case:
    steps = [] if value is None else [_step(el, value)]
    return Case(
        title=f"{_name(el)}: {title}", technique=technique, steps=steps, target=el["id"],
        expect=expect, **kw,
    )  # fmt: skip


def _ep(el: dict) -> list[Case]:
    kind, out = el["kind"], []
    value = _valid_value(el)
    if value is not None and not el["pattern"]:
        expect = {"select": "selected", "checkbox": "checked", "radio": "checked"}.get(
            kind, "valid"
        )
        out.append(_case(el, "ep", "valid partition", value, expect))
    if kind == "email":
        out.append(_case(el, "ep", "invalid partition (not an email)", "not-an-email", "invalid"))
    if el["required"]:
        out.append(_case(el, "ep", "required left empty", None, "invalid"))
    return out


def _bva(el: dict) -> list[Case]:
    kind, out = el["kind"], []
    if el["pattern"]:
        return out
    if kind in TEXTY:
        mn, mx = _int(el["minlength"]), _int(el["maxlength"])
        if mn and mn > 1:
            out.append(
                _case(el, "bva", f"length {mn - 1} (below minlength)", "a" * (mn - 1), "invalid")
            )
        if mn:
            out.append(_case(el, "bva", f"length {mn} (minlength)", "a" * mn, "valid"))
        if mx and mx <= MAX_LEN and mx >= (mn or 0):
            out.append(_case(el, "bva", f"length {mx} (maxlength)", "a" * mx, "valid"))
            out.append(
                _case(
                    el, "bva", f"length {mx + 1} is limited", "a" * (mx + 1), "max_length", limit=mx
                )
            )
    elif kind == "number":
        lo, hi = _num(el["min"]), _num(el["max"])
        bounds = [(lo, -1, "invalid", "below min"), (lo, 0, "valid", "min"),
                  (hi, 0, "valid", "max"), (hi, 1, "invalid", "above max")]  # fmt: skip
        for bound, delta, expect, word in bounds:
            if bound is not None:
                value = _fmt(bound + delta)
                out.append(_case(el, "bva", f"{value} ({word})", value, expect))
    return out


def _state(form_idx: int, fields: list[dict]) -> list[Case]:
    fields = [e for e in fields if e["kind"] in FIELDS and _valid_value(e) is not None]
    if len(fields) < 2 or any(e["pattern"] for e in fields):
        return []
    steps = {e["id"]: _step(e, _valid_value(e)) for e in fields}  # type: ignore[arg-type]

    def make(title: str, omit: str | None, expect: str) -> Case:
        return Case(
            title=f"Form {form_idx + 1}: {title}", technique="state", target=fields[0]["id"],
            steps=[s for k, s in steps.items() if k != omit], expect=expect,
        )  # fmt: skip

    cases = [make("all fields valid", None, "form_valid")]
    required = [e for e in fields if e["required"] and e["kind"] != "radio"]
    for e in required[:MAX_STATE_OMISSIONS]:
        cases.append(make(f"required '{_name(e)}' left empty", e["id"], "form_invalid"))
    return cases


def _score(case: Case, by_id: dict[str, dict]) -> float:
    el = by_id[case.target]
    return round(
        0.3 * IMPORTANCE.get(el["kind"], 0.5) + 0.2 * el["required"] + 0.2 * (el["form"] >= 0)
        + 0.3 * TECHNIQUE_WEIGHT[case.technique], 3,
    )  # fmt: skip


def generate(elements: list[dict], max_tests: int, extra: Iterable[Case] = ()) -> list[Case]:
    """Build, de-duplicate, prioritise and cap test cases. `extra` = pre-validated extra cases."""
    cases: list[Case] = []
    forms: dict[int, list[dict]] = defaultdict(list)
    for el in elements:
        if el["kind"] in ("button", "link"):
            cases.append(_case(el, "click", "is clickable", None, "clickable"))
            continue
        if el["form"] >= 0:
            forms[el["form"]].append(el)
        cases += _ep(el) + _bva(el)
    for idx, fields in forms.items():
        cases += _state(idx, fields)
    cases += extra
    by_id = {e["id"]: e for e in elements}
    seen, unique = set(), []
    for c in cases:
        key = (c.target, tuple((s.element, s.action, s.value) for s in c.steps), c.expect, c.limit)
        if key not in seen:
            seen.add(key)
            c.priority = _score(c, by_id)
            unique.append(c)
    top = sorted(unique, key=lambda c: -c.priority)[:max_tests]
    for i, c in enumerate(top, 1):
        c.id = f"t{i:02d}"
    return top
