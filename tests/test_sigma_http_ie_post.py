"""My own rule (Lab 5 Part F): legacy Internet Explorer user agent posting data (R-03, T1071.001)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from sigma_match import rule_matches

ROOT = Path(__file__).resolve().parent.parent
RULE = ROOT / "detections/sigma/http_legacy_ie_post.yml"
QUERY = ROOT / "detections/opensearch/http_legacy_ie_post.json"
SAMPLES = ROOT / "tests/samples"


def load(name):
    lines = (SAMPLES / name).read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_rule_fires_on_the_beacon():
    assert all(rule_matches(RULE, ev) for ev in load("ecs_http_ie_post_positive.json"))


def test_rule_ignores_the_near_misses():
    events = load("ecs_http_ie_post_negative.json")
    assert len(events) == 2
    assert not any(rule_matches(RULE, ev) for ev in events)


@pytest.mark.skipif(not shutil.which("sigma"), reason="sigma-cli not installed")
def test_committed_query_matches_the_rule():
    out = subprocess.run(
        ["sigma", "convert", "-t", "opensearch_lucene", "--without-pipeline",
         "-f", "dsl_lucene", str(RULE)],
        capture_output=True, text=True, check=True,
    ).stdout
    assert json.loads(out) == json.loads(QUERY.read_text())
