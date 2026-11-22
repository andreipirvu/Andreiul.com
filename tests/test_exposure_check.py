"""Unit test for the Shodan snapshot (RISK-REGISTER R-05). Makes no network call."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("exposure_check", ROOT / "scripts/exposure_check.py")
exposure_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exposure_check)


def test_snapshot_keeps_only_comparable_fields_with_sorted_ports():
    host = {"ip_str": "198.51.100.20", "ports": [443, 22], "org": "Example ISP",
            "last_update": "2026-11-01T08:00:00.000000", "data": [{"banner": "noise"}]}
    assert exposure_check.snapshot(host) == {
        "ip": "198.51.100.20", "ports": [22, 443], "org": "Example ISP",
        "last_update": "2026-11-01T08:00:00.000000",
    }
