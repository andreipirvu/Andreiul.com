"""Website checks as tests, so they run in the same CI "test" job (R-10)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_sri", ROOT / "scripts/check_sri.py")
check_sri = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_sri)

PAGES = sorted(str(p) for p in (ROOT / "site").glob("*.html"))


def test_every_third_party_script_is_pinned_with_sri():
    assert PAGES, "no site/*.html found"
    assert check_sri.main(PAGES) == 0


def test_sri_check_fails_without_integrity(tmp_path):
    page = tmp_path / "bad.html"
    page.write_text('<script src="https://cdnjs.cloudflare.com/x.js"></script>')
    assert check_sri.main([str(page)]) == 1


def test_main_page_has_no_inline_event_handlers():
    """The main page CSP forbids inline script (R-11)."""
    html = (ROOT / "site/index.html").read_text(encoding="utf-8")
    assert "onclick=" not in html.lower()
    assert "<script>" not in html.lower()
