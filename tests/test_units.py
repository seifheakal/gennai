import ast

import pytest

from gennai import GennaiError
from gennai.config import Settings
from gennai.phase1_explore import candidate_locators, infer_kind, normalize_url, skip_reason
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


def test_normalize_url_dedupes_fragment_query_order_and_case():
    assert normalize_url("HTTP://Example.com#top") == "http://example.com/"
    assert normalize_url("http://example.com/a?b=2&a=1#x") == "http://example.com/a?a=1&b=2"


ORIGIN = ("https", "example.com", 443)


@pytest.mark.parametrize(
    ("href", "text", "reason"),
    [
        ("https://example.com/about", "About", None),
        ("https://EXAMPLE.com:443/about", "About", None),  # default port is the same origin
        ("http://example.com/about", "About", "other origin"),  # scheme differs
        ("https://other.com/", "Other", "other origin"),
        ("mailto:a@example.com", "Mail", "not http(s)"),
        ("https://example.com/logout", "Bye", "looks like logout/delete"),
        ("https://example.com/item/7", "Delete item", "looks like logout/delete"),
        ("https://example.com/files/guide.PDF", "Guide", "not an HTML page"),
    ],
)  # fmt: skip
def test_skip_reason(href, text, reason):
    assert skip_reason(href, text, ORIGIN) == reason


def test_generation_keeps_forms_per_page_and_shares_the_cap():
    a = [_el("e01", "text", label="A1", page="http://x/a"),
         _el("e02", "text", label="A2", page="http://x/a")]  # fmt: skip
    b = [_el("e03", "text", label="B1", page="http://x/b"),
         _el("e04", "text", label="B2", page="http://x/b")]  # fmt: skip
    cases = generate(a + b, 100)
    state = [c for c in cases if c.technique == "state"]
    assert len(state) == 2  # same form index on two pages = two forms, not one
    for c in cases:
        assert c.page == {"e01": "http://x/a", "e02": "http://x/a"}.get(c.target, "http://x/b")
    assert {c.page for c in generate(a + b, 2)} == {"http://x/a", "http://x/b"}


def test_codegen_writes_one_page_object_per_page(tmp_path):
    els = [_el("e01", "text", label="Name", page="http://x/"),
           _el("e02", "email", label="Mail", page="http://x/contact")]  # fmt: skip
    cases = generate(els, 100)
    tests = write_project("http://x/", els, cases, tmp_path, Settings())
    assert sorted(f.name for f in (tests / "pages").glob("*.py")) == [
        "site_x_p2_contact_page.py", "site_x_page.py"]  # fmt: skip
    second = (tests / "test_generated_p2.py").read_text(encoding="utf-8")
    assert "PAGE_URL = 'http://x/contact'" in second
    assert "from pages.site_x_p2_contact_page import Page" in second
    first = (tests / "test_generated.py").read_text(encoding="utf-8")
    for c in cases:  # every test lands in its own page's file, once
        name = f"def test_{c.id}("
        assert (name in first) != (name in second)
        assert (name in second) == (c.page == "http://x/contact")
