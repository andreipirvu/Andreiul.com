"""Detection as code for the long DNS TXT rule (RISK-REGISTER R-03)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from sigma_match import rule_matches

ROOT = Path(__file__).resolve().parent.parent
RULE = ROOT / "detections/sigma/dns_long_txt.yml"
QUERY = ROOT / "detections/opensearch/dns_long_txt.json"
SAMPLES = ROOT / "tests/samples"


def load(name):
    lines = (SAMPLES / name).read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_rule_fires_on_positive_sample():
    assert all(rule_matches(RULE, ev) for ev in load("ecs_dns_txt_positive.json"))


def test_rule_stays_quiet_on_negative_sample():
    assert not any(rule_matches(RULE, ev) for ev in load("ecs_dns_txt_negative.json"))


@pytest.mark.skipif(not shutil.which("sigma"), reason="sigma-cli not installed")
def test_committed_query_matches_the_rule():
    out = subprocess.run(
        ["sigma", "convert", "-t", "opensearch_lucene", "--without-pipeline",
         "-f", "dsl_lucene", str(RULE)],
        capture_output=True, text=True, check=True,
    ).stdout
    assert json.loads(out) == json.loads(QUERY.read_text())
