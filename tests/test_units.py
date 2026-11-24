import ast

import pytest

from gennai import GennaiError
from gennai.config import Settings
from gennai.phase1_explore import candidate_locators, infer_kind
from gennai.phase2_generate import Case, Step, generate
from gennai.phase3_codegen import write_project
from gennai.phase4_execute import classify_failure
from gennai.safety import check_url


def _el(id_, kind, **kw):
    base = {
        "id": id_, "kind": kind, "tag": "input", "type": "text", "dom_id": None, "name": None,
        "label": "", "text": "", "placeholder": None, "aria_label": None, "required": False,
        "minlength": None, "maxlength": None, "min": None, "max": None, "pattern": None,
        "form": 0, "options": None, "locators": [("css", "#x")],
    }  # fmt: skip
    return {**base, **kw}


ELEMENTS = [
    _el("e01", "text", label="Name", required=True, minlength="2", maxlength="10"),
    _el("e02", "email", label="Email"),
    _el("e03", "number", label="Age", min="18", max="65"),
    _el("e04", "button", tag="button", text="Go"),
]


def test_generation_techniques():
    cases = generate(ELEMENTS, 100)
    by = {(c.technique, c.target, c.title.split(": ", 1)[1], c.expect) for c in cases}
    assert ("ep", "e02", "invalid partition (not an email)", "invalid") in by
    assert ("ep", "e01", "required left empty", "invalid") in by
    assert ("bva", "e01", "length 1 (below minlength)", "invalid") in by
    assert ("bva", "e01", "length 11 is limited", "max_length") in by
    assert ("bva", "e03", "17 (below min)", "invalid") in by
    assert ("bva", "e03", "66 (above max)", "invalid") in by
    assert ("click", "e04", "is clickable", "clickable") in by
    state = [c for c in cases if c.technique == "state"]
    assert {c.expect for c in state} == {"form_valid", "form_invalid"}
    assert len(state) == 2  # all valid + the one required field left empty


def test_generation_caps_and_ids():
    cases = generate(ELEMENTS, 3)
    assert [c.id for c in cases] == ["t01", "t02", "t03"]
    assert [c.priority for c in cases] == sorted((c.priority for c in cases), reverse=True)


def test_candidate_locators_order():
    attrs = {
        "tag": "input", "type": "text", "kind": "text", "testid": "tid", "dom_id": "1a b",
        "name": 'n"m', "label": "Name", "placeholder": "Your name", "text": "",
    }  # fmt: skip
    assert candidate_locators(attrs) == [
        ("testid", "tid"),
        ("css", r"#\31 a\ b"),
        ("css", 'input[name="n\\"m"]'),
        ("role:textbox", "Name"),
        ("label", "Name"),
        ("placeholder", "Your name"),
    ]
    link = {"tag": "a", "type": "", "text": "Home", "label": ""}
    assert candidate_locators(link) == [("role:link", "Home"), ("text", "Home")]


def test_infer_kind_uses_name_and_label():
    assert infer_kind({"tag": "input", "type": "text", "label": "Your E-mail"}) == "email"
    assert infer_kind({"tag": "input", "type": "date"}) == "other"


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("TimeoutError: Locator.click: Timeout 5000ms exceeded.\n <div> intercepts pointer events",
         "element_intercepted"),
        ("pages.x.LocatorNotFound: e01: no unique match", "locator_not_found"),
        ('failed on setup with "conftest.PageUnavailable: https://x/ returned HTTP 503"',
         "page_unavailable"),
        ("playwright._impl._errors.TimeoutError: Locator.fill: Timeout 5s exceeded.", "timeout"),
        ("AssertionError: expected the field to be invalid", "assertion"),
        ("ValueError: boom", "other"),
    ],
)  # fmt: skip
def test_classify_failure(message, expected):
    assert classify_failure(message) == expected


@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd", "http://127.0.0.1", "http://10.0.0.1", "http://100.64.0.1",
     "http://localhost:abc/", "http://[bad/"],
)  # fmt: skip
def test_check_url_rejects(url):
    with pytest.raises(GennaiError):
        check_url(url)


def test_check_url_allow_local():
    assert check_url("http://127.0.0.1:8000/", allow_local=True) == "http://127.0.0.1:8000/"


# quotes, triple quotes, newline, line separator, a code payload and the template markers
HOSTILE = "x'\"'''\"\"\"\n__import__('os').system('echo pwned') #__LOCATE__ __CANDIDATES__  "


def test_codegen_keeps_hostile_text_inside_literals(tmp_path):
    el = _el("e01", "text", label=HOSTILE, name=HOSTILE, locators=[("label", HOSTILE)])
    case = Case(title=HOSTILE, technique="ep", target="e01", expect="valid",
                steps=[Step(element="e01", action="fill", value=HOSTILE)])  # fmt: skip
    write_project("http://example.com/" + HOSTILE, [el], [case], tmp_path, Settings())
    files = list((tmp_path / "tests").rglob("*.py"))
    assert len(files) == 3
    for f in files:
        tree = ast.parse(f.read_text(encoding="utf-8"))  # SyntaxError = a broken template
        names = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)}  # fmt: skip
        assert "__import__" not in names  # the payload stayed inside a string
