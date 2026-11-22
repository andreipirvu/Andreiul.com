"""Unit tests for the Shodan snapshot (RISK-REGISTER R-05). They make no network call."""
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("exposure_check", ROOT / "scripts/exposure_check.py")
exposure_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exposure_check)


def test_snapshot_keeps_only_comparable_fields_with_sorted_ports():
    host = {"ip_str": "198.51.100.20", "ports": [443, 22], "org": "Example ISP",
            "last_update": "2026-11-01T08:00:00.000000", "data": [{"banner": "noise"}]}
    assert exposure_check.snapshot(host) == {
        "source": "shodan-api", "ip": "198.51.100.20", "ports": [22, 443],
        "org": "Example ISP", "last_update": "2026-11-01T08:00:00.000000",
    }


def test_internetdb_snapshot_has_the_same_shape():
    data = {"ip": "198.51.100.20", "ports": [443, 80, 22], "hostnames": ["x"], "vulns": []}
    assert exposure_check.snapshot_internetdb("198.51.100.20", data) == {
        "source": "internetdb", "ip": "198.51.100.20", "ports": [22, 80, 443],
        "org": None, "last_update": None,
    }


def _fake_shodan(monkeypatch, message):
    class APIError(Exception):
        pass

    class Shodan:
        def __init__(self, key):
            pass

        def host(self, ip):
            raise APIError(message)

    monkeypatch.setitem(sys.modules, "shodan", types.SimpleNamespace(Shodan=Shodan, APIError=APIError))


def test_free_key_403_falls_back_to_internetdb(monkeypatch):
    _fake_shodan(monkeypatch, "Access denied (403 Forbidden)")
    monkeypatch.setattr(exposure_check, "fetch_internetdb", lambda ip: {"ip": ip, "ports": [443, 22]})
    snap = exposure_check.lookup("198.51.100.20", "free-key")
    assert snap["source"] == "internetdb" and snap["ports"] == [22, 443]


def test_other_shodan_errors_stop_without_fallback(monkeypatch):
    _fake_shodan(monkeypatch, "Invalid API key")
    monkeypatch.setattr(exposure_check, "fetch_internetdb", lambda ip: (_ for _ in ()).throw(AssertionError))
    try:
        exposure_check.lookup("198.51.100.20", "bad-key")
    except SystemExit as err:
        assert "Invalid API key" in str(err)
    else:
        raise AssertionError("expected SystemExit")
