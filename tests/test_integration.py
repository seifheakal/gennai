import json

from gennai.config import Settings
from gennai.pipeline import run_pipeline, serve_dir


def test_demo_end_to_end(tmp_path):
    with serve_dir() as url:
        run_pipeline(url, tmp_path, Settings(), allow_local=True)
    assert (tmp_path / "report.html").exists()
    results = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert results["summary"]["passed"] >= 1
    classes = results["summary"]["failures_per_class"]
    assert classes.get("element_intercepted", 0) >= 1
    assert classes.get("assertion", 0) >= 1
    blocked = next(t for t in results["tests"] if t["failure_class"] == "element_intercepted")
    assert blocked["message"].startswith('<div id="cookie"')  # names the covering element


def test_demo_multi_page_crawl(tmp_path):
    with serve_dir() as url:
        run_pipeline(url, tmp_path, Settings(), allow_local=True, max_pages=5)
        contact = url + "contact.html"
    results = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    # contact.html is linked twice ("./" and "#form" dedupe); "Log out" is never followed
    assert results["pages"] == [url, contact]
    elements = json.loads((tmp_path / "elements.json").read_text(encoding="utf-8"))
    assert {e["page"] for e in elements} == {url, contact}
    assert len({e["id"] for e in elements}) == len(elements)
    assert len(list((tmp_path / "tests" / "pages").glob("*.py"))) == 2
    on_contact = [t for t in results["tests"] if t["page"] == contact]
    assert on_contact and all(t["status"] == "passed" for t in on_contact)
    assert any(t["page"] == url for t in results["tests"])


def test_demo_with_review(tmp_path):
    seen = {}

    def reviewer(path):  # stands in for a person editing the file, then pressing Enter
        data = json.loads(path.read_text(encoding="utf-8"))
        seen["ids"] = [c["id"] for c in data]
        data[0]["approved"] = False
        data[1]["title"] = "renamed by the reviewer"
        path.write_text(json.dumps(data), encoding="utf-8")

    with serve_dir() as url:
        run_pipeline(url, tmp_path, Settings(), allow_local=True, review=reviewer)
    results = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert results["review"] == {"approved": len(seen["ids"]) - 1, "rejected": 1, "edited": 1}
    assert [t["id"] for t in results["tests"]] == seen["ids"][1:]
    assert results["tests"][0]["title"] == "renamed by the reviewer"
    code = (tmp_path / "tests" / "test_generated.py").read_text(encoding="utf-8")
    assert f"def test_{seen['ids'][0]}(" not in code
