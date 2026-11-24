"""Human review step: what a reviewer may and may not change in test_cases.json."""

import json

import pytest

from gennai import GennaiError
from gennai.phase2_generate import Case, Step
from gennai.review import load_reviewed, write_for_review

CASES = [
    Case(id="t01", title="Email: valid", technique="ep", target="e01", expect="valid",
         steps=[Step(element="e01", action="fill", value="a@b.c")]),
    Case(id="t02", title="Go: clickable", technique="click", target="e02", expect="clickable"),
    Case(id="t03", title="Email: invalid", technique="ep", target="e01", expect="invalid",
         steps=[Step(element="e01", action="fill", value="nope")]),
]  # fmt: skip


def review(tmp_path, edit):
    path = tmp_path / "test_cases.json"
    write_for_review(path, CASES)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert all(item["approved"] is True for item in data)
    data = edit(data)
    path.write_text(json.dumps(data), encoding="utf-8")
    return load_reviewed(path, CASES)


def test_untouched_file_approves_everything(tmp_path):
    kept, stats = review(tmp_path, lambda d: d)
    assert [c.id for c in kept] == ["t01", "t02", "t03"]
    assert stats == {"approved": 3, "rejected": 0, "edited": 0}


def test_reject_delete_and_edit(tmp_path):
    def edit(d):
        d[0]["steps"][0]["value"] = "reviewer@example.com"
        d[0]["title"] = "Email: reviewer's value"
        d[1]["approved"] = False
        return [d[2], d[0], d[1]][:2]  # reordered, and t02 deleted as well as rejected

    kept, stats = review(tmp_path, edit)
    assert [c.id for c in kept] == ["t01", "t03"]  # original order is kept
    assert kept[0].steps[0].value == "reviewer@example.com"
    assert stats == {"approved": 2, "rejected": 1, "edited": 1}


@pytest.mark.parametrize(
    "edit",
    [
        lambda d: d[0].update(target="e02"),  # structural change
        lambda d: d[0].update(expect="invalid"),
        lambda d: d[0]["steps"][0].update(element="e02"),
        lambda d: d[0]["steps"].append({"element": "e02", "action": "check", "value": ""}),
        lambda d: d[0].update(id="t01(page):\n    import os\ndef x"),  # would be a def name
        lambda d: d.append(dict(d[0])),  # repeated id
        lambda d: d[0].update(approved="yes"),
        lambda d: d[0].update(extra=1),  # unknown key
        lambda d: d.append(["t09"]),
    ],
)
def test_structural_edits_are_refused(tmp_path, edit):
    with pytest.raises(GennaiError):
        review(tmp_path, lambda d: edit(d) or d)


def test_unreadable_file(tmp_path):
    path = tmp_path / "test_cases.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(GennaiError):
        load_reviewed(path, CASES)
