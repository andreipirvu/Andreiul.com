"""Unit test for the MISP lookup writer (RISK-REGISTER R-04). Needs no MISP server."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import yaml

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("misp_pull", ROOT / "scripts/misp_pull.py")
misp_pull = importlib.util.module_from_spec(spec)
spec.loader.exec_module(misp_pull)


def attr(value, event_id, category="Network activity"):
    return SimpleNamespace(value=value, event_id=event_id, category=category)


def test_lookup_is_deduplicated_sorted_and_valid_yaml():
    text = misp_pull.render([attr("198.51.100.9", 7), attr("192.0.2.1", 3), attr("198.51.100.9", 9)])
    assert yaml.safe_load(text) == {
        "192.0.2.1": "misp:3:Network activity",
        "198.51.100.9": "misp:7:Network activity",
    }
    assert text.splitlines()[0].startswith('"192.0.2.1"')


def test_empty_feed_renders_nothing():
    assert misp_pull.render([]) == ""


def _fake_pymisp(monkeypatch, attrs):
    """Stand-in for the pymisp module, so main() runs without a MISP server."""
    import sys
    from types import ModuleType

    class FakeMISP:
        def __init__(self, url, key, ssl):
            self.url, self.key, self.ssl = url, key, ssl

        def search(self, **query):
            assert query["to_ids"] is True and query["enforce_warninglist"] is True
            return attrs

    mod = ModuleType("pymisp")
    mod.PyMISP = FakeMISP
    monkeypatch.setitem(sys.modules, "pymisp", mod)
    monkeypatch.setenv("MISP_URL", "https://misp.invalid")
    monkeypatch.setenv("MISP_KEY", "not-a-real-key")


def test_main_writes_the_lookup_atomically(tmp_path, monkeypatch):
    _fake_pymisp(monkeypatch, [attr("192.0.2.1", 3)])
    monkeypatch.chdir(tmp_path)
    misp_pull.main()
    out = tmp_path / "enrich" / "ioc_ip.yml"
    assert yaml.safe_load(out.read_text()) == {"192.0.2.1": "misp:3:Network activity"}
    assert not (tmp_path / "enrich" / "ioc_ip.tmp").exists()


def test_empty_feed_keeps_the_previous_lookup(tmp_path, monkeypatch):
    import pytest

    _fake_pymisp(monkeypatch, [])
    monkeypatch.chdir(tmp_path)
    previous = tmp_path / "enrich" / "ioc_ip.yml"
    previous.parent.mkdir()
    previous.write_text('"198.51.100.9": "misp:7:Network activity"\n')
    with pytest.raises(SystemExit):
        misp_pull.main()
    assert "198.51.100.9" in previous.read_text()
