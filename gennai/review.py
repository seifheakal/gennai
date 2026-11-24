"""Human review between Phase 2 and Phase 3: a person approves, rejects or edits test cases.

The reviewer may set "approved" to false (or delete a case) and may change a case's title and
its step values. Everything that decides what code is generated (ids, technique, target,
expectation, which elements are touched and how) must stay as generated, so an edit can't
produce a broken or injected test. Values and titles are embedded with repr() like any other.
"""

import json
from pathlib import Path

from pydantic import ValidationError

from gennai import GennaiError
from gennai.phase2_generate import Case

EDITABLE = "title and step values"


def write_for_review(path: Path, cases: list[Case]) -> None:
    """Write the cases with an "approved": true flag each, for a person to edit."""
    data = [{"approved": True, **c.model_dump()} for c in cases]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _shape(c: Case) -> tuple:
    return (c.technique, c.target, c.expect, c.limit, c.page, c.priority,
            [(s.element, s.action) for s in c.steps])  # fmt: skip


def load_reviewed(path: Path, cases: list[Case]) -> tuple[list[Case], dict]:
    """Read the reviewed file; return (approved cases in original order, counts)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise GennaiError(f"could not read the reviewed {path.name}: {e}") from e
    if not isinstance(data, list):
        raise GennaiError(f"{path.name} must be a JSON list of test cases")
    original = {c.id: c for c in cases}
    reviewed: dict[str, tuple[bool, Case]] = {}
    for item in data:
        cid = item.get("id") if isinstance(item, dict) else None
        if not isinstance(cid, str) or cid not in original or cid in reviewed:
            raise GennaiError(f"{path.name}: unknown or repeated test case id {cid!r}")
        approved = item.pop("approved", True)
        if not isinstance(approved, bool):
            raise GennaiError(f'{path.name}: {cid}: "approved" must be true or false')
        try:
            case = Case.model_validate(item)
        except ValidationError as e:
            raise GennaiError(f"{path.name}: {cid}: {e.errors()[0]['msg']}") from e
        if _shape(case) != _shape(original[cid]):
            raise GennaiError(f'{path.name}: {cid}: only "approved", {EDITABLE} may be changed')
        reviewed[cid] = (approved, case)
    kept = [reviewed[c.id][1] for c in cases if reviewed.get(c.id, (False,))[0]]
    edited = sum(
        1 for c in kept
        if (c.title, [s.value for s in c.steps])
        != (original[c.id].title, [s.value for s in original[c.id].steps])
    )  # fmt: skip
    stats = {"approved": len(kept), "rejected": len(cases) - len(kept), "edited": edited}
    return kept, stats


def ask_in_terminal(path: Path) -> None:
    """Block until the person presses Enter; Ctrl+C or end of input cancels the run."""
    print(f"\nReview the generated test cases in:\n  {path}")
    print(f'Set "approved": false (or delete a case) to drop it; you may also edit {EDITABLE}.')
    try:
        input("Press Enter when done to generate and run the approved tests (Ctrl+C cancels): ")
    except (EOFError, KeyboardInterrupt) as e:
        raise GennaiError("review cancelled; no tests were generated or run") from e
