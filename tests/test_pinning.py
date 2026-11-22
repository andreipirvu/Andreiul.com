"""Nothing this repository builds, runs or installs floats (RISK-REGISTER R-08).

A floating tag such as nginx:1.27-alpine, or an action tag such as @v4, can change under
you between two runs. A digest or a commit SHA cannot. Images that come from .env
(${VAR}) are pinned there instead.
"""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
SHA = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))


def rel(p):
    return str(p.relative_to(ROOT))


def dockerfiles():
    return sorted(p for p in ROOT.rglob("Dockerfile*") if ".git" not in p.parts)


@pytest.mark.parametrize("path", dockerfiles(), ids=rel)
def test_dockerfile_base_images_are_pinned_by_digest(path):
    froms = [line.split()[1] for line in path.read_text().splitlines()
             if line.strip().upper().startswith("FROM ")]
    assert froms, f"{path} has no FROM line"
    for image in froms:
        assert DIGEST.search(image), f"{path}: {image} is not pinned by a real digest"


def test_compose_images_are_pinned_by_digest_or_come_from_env():
    compose = ROOT / "compose.yaml"
    if not compose.exists():
        pytest.skip("no compose.yaml in this repository")
    services = yaml.safe_load(compose.read_text()).get("services", {})
    for name, svc in services.items():
        image = svc.get("image", "")
        if not image or image.startswith("${"):
            continue
        assert DIGEST.search(image), f"service {name}: {image} is not pinned by digest"


@pytest.mark.parametrize("path", WORKFLOWS, ids=rel)
def test_actions_are_pinned_to_a_full_commit_sha(path):
    for line in path.read_text().splitlines():
        m = re.match(r"\s*-?\s*uses:\s*(\S+)", line)
        if not m or m.group(1).startswith("./"):
            continue
        ref = m.group(1)
        if ref.startswith("docker://"):
            assert DIGEST.search(ref), f"{rel(path)}: {ref} is not pinned by digest"
        else:
            assert SHA.match(ref), f"{rel(path)}: {ref} is not pinned to a 40-character SHA"


@pytest.mark.parametrize("path", WORKFLOWS, ids=rel)
def test_images_run_inside_workflows_are_pinned_by_digest(path):
    for value in re.findall(r"^\s*[A-Z_]*IMAGE:\s*(\S+)", path.read_text(), re.M):
        if value.startswith("${{"):
            continue
        assert DIGEST.search(value), f"{rel(path)}: {value} is not pinned by digest"


@pytest.mark.parametrize("path", sorted(ROOT.glob("requirements*.txt")), ids=rel)
def test_python_requirements_are_pinned_exactly(path):
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            assert re.fullmatch(r"[A-Za-z0-9_.\-\[\]]+==[0-9][\w.]*", line), \
                f"{rel(path)}: '{line}' is not pinned with =="
