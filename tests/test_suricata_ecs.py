"""Run pipelines/suricata.conf in Logstash and check the ECS output.
Base pipeline and harness from cybrd0ne/secops-demo; extended in Lab 5 and Lab 6.
The image comes from LOGSTASH_IMAGE (set in .env, pinned by digest).
Covers RISK-REGISTER R-03.
"""
import json
import os
import subprocess
from pathlib import Path
import pytest

from sigma_match import rule_matches

ROOT = Path(__file__).resolve().parent.parent
RULE = ROOT / "detections/sigma/dns_long_txt.yml"
IMAGE = os.environ.get("LOGSTASH_IMAGE")
pytestmark = pytest.mark.skipif(not IMAGE, reason="LOGSTASH_IMAGE not set (see .env)")
def run_pipeline(sample: Path) -> list[dict]:
    cmd = [
        "docker", "run", "--rm", "-i",
        "-v", f"{ROOT / 'pipelines' / 'suricata.conf'}:/pipe/10-suricata.conf:ro",
        "-v", f"{ROOT / 'tests' / 'harness.conf'}:/pipe/00-harness.conf:ro",
        "-v", f"{ROOT / 'tests' / 'samples' / 'ioc_ip_test.yml'}:/enrich/ioc_ip.yml:ro",
        IMAGE, "logstash", "-f", "/pipe", "--log.level=error",
    ]
    out = subprocess.run(
        cmd, input=sample.read_text(), capture_output=True, text=True, timeout=300, check=True
    ).stdout
    return [json.loads(line) for line in out.splitlines() if line.startswith("{")]
def test_alert_maps_to_ecs():
    (ev,) = run_pipeline(ROOT / "tests/samples/suricata_alert.json")
    assert ev["source"] == {"ip": "10.0.0.5", "port": 51514}
    assert ev["destination"] == {"ip": "203.0.113.7", "port": 443}
    assert ev["network"]["transport"] == "tcp"
    assert ev["network"]["protocol"] == "tls"
    assert ev["event"]["kind"] == "alert"
    assert ev["rule"]["id"] == 2024897
    assert ev["rule"]["name"] == "ET MALWARE Demo C2 Beacon"
    assert ev["@timestamp"].startswith("2026-10-19T10:15:30.123")
def test_invalid_json_is_tagged_and_unmapped():
    (ev,) = run_pipeline(ROOT / "tests/samples/suricata_invalid.txt")
    assert "_jsonparsefailure" in ev["tags"]
    # Logstash 8 (ECS compatibility) adds event.original to every record by itself, so
    # "no event field" can never hold. What matters is that nothing was mapped to ECS.
    assert "source" not in ev
    assert "module" not in ev.get("event", {}) and "kind" not in ev.get("event", {})



def test_dns_answer_maps_to_ecs_and_fires_the_rule():
    events = run_pipeline(ROOT / "tests/samples/eve_dns_txt_positive.json")
    assert events and all(rule_matches(RULE, ev) for ev in events)


def test_negative_dns_samples_stay_quiet_after_the_pipeline():
    events = run_pipeline(ROOT / "tests/samples/eve_dns_txt_negative.json")
    assert len(events) == 3 and not any(rule_matches(RULE, ev) for ev in events)


def test_known_bad_destination_is_tagged_and_scored():
    (ev,) = run_pipeline(ROOT / "tests/samples/eve_flow_ioc_positive.json")
    assert ev["threat"]["indicator"]["matched"] == "misp:0:Network activity"
    assert "threat_match" in ev["tags"]
    assert ev["event"]["risk_score"] == 80.0


def test_clean_destination_is_untouched():
    (ev,) = run_pipeline(ROOT / "tests/samples/eve_flow_ioc_negative.json")
    assert "threat" not in ev
    assert "threat_match" not in ev.get("tags", [])


# My own rule (Lab 5 Part F): the same chain for HTTP, raw Suricata -> Logstash -> rule.
HTTP_RULE = ROOT / "detections/sigma/http_legacy_ie_post.yml"


def test_http_beacon_maps_to_ecs_and_fires_my_rule():
    (ev,) = run_pipeline(ROOT / "tests/samples/eve_http_ie_post_positive.json")
    assert ev["user_agent"]["original"].startswith("Mozilla/4.0 (compatible; MSIE 6.0")
    assert ev["http"]["request"]["method"] == "POST"
    assert ev["url"]["domain"] == "203.0.113.66"
    assert rule_matches(HTTP_RULE, ev)


def test_http_near_misses_stay_quiet_after_the_pipeline():
    events = run_pipeline(ROOT / "tests/samples/eve_http_ie_post_negative.json")
    assert len(events) == 2 and not any(rule_matches(HTTP_RULE, ev) for ev in events)
