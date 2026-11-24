"""Run history and flaky-test marking (Phase 4)."""

import json

from gennai.phase2_generate import Case, Step
from gennai.phase4_execute import case_key, record_history

EL = {"e01": {"tag": "input", "kind": "email", "dom_id": "mail", "label": "Email"},
      "e07": {"tag": "input", "kind": "email", "dom_id": "mail", "label": "Email"}}  # fmt: skip


def _case(cid, eid, value, page="http://127.0.0.1:5000/"):
    return Case(id=cid, title=cid, technique="ep", target=eid, expect="valid", page=page,
                steps=[Step(element=eid, action="fill", value=value)])  # fmt: skip


def test_key_ignores_rank_id_and_host_but_not_content():
    a = case_key(_case("t01", "e01", "a@b.c"), EL)
    assert a == case_key(_case("t09", "e07", "a@b.c", page="http://127.0.0.1:6000/"), EL)
    assert a != case_key(_case("t01", "e01", "x@y.z"), EL)
    assert a != case_key(_case("t01", "e01", "a@b.c", page="http://127.0.0.1:5000/b"), EL)


def _run(path, tmp_path, statuses, window=3):
    rows = [{"key": k, "status": s} for k, s in statuses.items()]
    meta = {"finished": "now", "url": "http://x/"}
    info = record_history(path, tmp_path, meta, rows, window)
    return info, {r["key"]: r for r in rows}


def test_flaky_within_window_only(tmp_path):
    path = tmp_path / "history" / "site.jsonl"
    _run(path, tmp_path, {"a": "failed", "b": "passed", "c": "passed"})
    _run(path, tmp_path, {"a": "passed", "b": "passed", "c": "failed"})
    info, rows = _run(path, tmp_path, {"a": "passed", "b": "passed", "d": "not_run"})
    assert info["runs"] == 3 and info["window"] == 3
    assert rows["a"]["history"] == ["failed", "passed", "passed"] and rows["a"]["flaky"]
    assert not rows["b"]["flaky"]
    assert rows["d"]["history"] == [None, None, None] and not rows["d"]["flaky"]
    info, rows = _run(path, tmp_path, {"a": "passed"})  # the failure is now 4 runs back
    assert rows["a"]["history"] == ["passed", "passed", "passed"] and not rows["a"]["flaky"]
    assert info["runs"] == 4


def test_history_is_append_only_and_skips_bad_lines(tmp_path, caplog):
    path = tmp_path / "site.jsonl"
    _run(path, tmp_path, {"a": "passed"})
    first = path.read_text(encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write("not json\n" + json.dumps({"tests": ["a"]}) + "\n")
        f.write(json.dumps({"tests": {"a": "failed", "b": ["odd"]}}) + "\n")
    info, rows = _run(path, tmp_path, {"a": "passed", "b": "passed"})
    assert path.read_text(encoding="utf-8").startswith(first)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 5
    assert info["runs"] == 3  # two bad lines ignored, with a warning each
    assert sum("not a run record" in m for m in caplog.messages) == 2
    assert rows["a"]["history"] == ["passed", "failed", "passed"] and rows["a"]["flaky"]
    assert rows["b"]["history"] == [None, None, "passed"]  # a non-status value is dropped
