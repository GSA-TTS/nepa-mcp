"""Static and command-contract tests for the additive container layer."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCKER_ROOT = ROOT / "docker"
SERVERS = {
    "blm",
    "census",
    "cfr",
    "efh",
    "epa_acres",
    "epa_aqs",
    "esa_ranges",
    "fema_nfhl",
    "gbif",
    "ipac",
    "noaa",
    "nrhp",
    "padus",
    "pcsrf",
    "tigerweb_counties",
    "tribal",
    "usace",
}


def test_container_inventory_and_wrapper_files_are_complete():
    wrappers = {path.parent.name for path in DOCKER_ROOT.glob("*/entry.py")}
    assert wrappers == SERVERS
    for server in SERVERS:
        wrapper = DOCKER_ROOT / server
        assert (wrapper / "entry.py").is_file()
        assert (wrapper / "build-and-push.sh").is_file()
        assert not (wrapper / "Dockerfile").exists()
        assert not (wrapper / ".dockerignore").exists()


def test_each_wrapper_passes_its_server_and_a_unique_image():
    images = set()
    for server in SERVERS:
        script = (DOCKER_ROOT / server / "build-and-push.sh").read_text(encoding="utf-8")
        match = re.search(
            rf'exec bash .*build-image\.sh" {re.escape(server)} (ghcr\.io/gsa-tts/[^ ]+) docker/Dockerfile$',
            script,
            re.MULTILINE,
        )
        assert match, f"{server} wrapper does not call the shared hardened build"
        images.add(match.group(1))
    assert len(images) == len(SERVERS)


def test_shared_dockerfile_enforces_runtime_and_supply_chain_controls():
    dockerfile = (DOCKER_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert re.search(r"^FROM python:3\.12-slim@sha256:[0-9a-f]{64}$", dockerfile, re.MULTILINE)
    assert "--constraint /tmp/requirements/constraints.txt" in dockerfile
    assert "python -m pip install --no-cache-dir" in dockerfile
    assert "pip install --upgrade" not in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert dockerfile.count("COPY --chown=10001:10001") == 4
    assert 'CMD ["python", "/app/entry.py"]' in dockerfile
    assert "PORT=8080 python" not in dockerfile
    for label in (
        "org.opencontainers.image.source",
        "org.opencontainers.image.version",
        "org.opencontainers.image.revision",
        "org.opencontainers.image.created",
        "org.opencontainers.image.licenses",
        "gov.gsa.nepa-mcp.source-dirty",
    ):
        assert label in dockerfile


def test_root_dockerignore_excludes_sensitive_and_out_of_scope_content():
    patterns = set((ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines())
    assert {".git", ".env", ".env.*", "credentials.env", "config.toml", "tests", "docs"} <= patterns
    assert {"gis", "map_composer", "nepa_assist", "blm_mlrs", "nrcs_soils", "permitting_dashboard"} <= patterns


def test_constraints_pin_runtime_requirements_to_exact_versions():
    constraints = (DOCKER_ROOT / "constraints.txt").read_text(encoding="utf-8")
    for package in ("fastmcp", "mcp", "platformdirs", "pyproj", "python-dotenv", "requests", "shapely"):
        assert re.search(rf"^{re.escape(package)}==[^=\s]+", constraints, re.MULTILINE)


def _run_wrapper(
    tmp_path: Path,
    monkeypatch,
    *,
    push: str | None = None,
    latest: str | None = None,
    dirty: bool = True,
):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    capture = tmp_path / "docker-args"
    docker = bin_dir / "docker"
    docker.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$DOCKER_CAPTURE"\n', encoding="utf-8")
    docker.chmod(0o755)
    git = bin_dir / "git"
    git.write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        '  rev-parse) printf "0123456789abcdef0123456789abcdef01234567\\n" ;;\n'
        '  show) printf "2026-10-20T10:39:27-04:00\\n" ;;\n'
        f"  status) {'printf dirty\\n' if dirty else ':'} ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    git.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.setenv("DOCKER_CAPTURE", str(capture))
    monkeypatch.delenv("PUSH", raising=False)
    monkeypatch.delenv("PUBLISH_LATEST", raising=False)
    if push is not None:
        monkeypatch.setenv("PUSH", push)
    if latest is not None:
        monkeypatch.setenv("PUBLISH_LATEST", latest)
    result = subprocess.run(
        ["bash", str(DOCKER_ROOT / "blm" / "build-and-push.sh")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    args = capture.read_text(encoding="utf-8").splitlines() if capture.exists() else []
    return result, args


def test_build_defaults_to_local_amd64_without_latest(tmp_path, monkeypatch):
    result, args = _run_wrapper(tmp_path, monkeypatch)
    assert result.returncode == 0, result.stderr
    assert args[:2] == ["buildx", "build"]
    assert "linux/amd64" in args
    assert "--load" in args
    assert "--push" not in args
    assert "ghcr.io/gsa-tts/mcp-server-nepa-blm:latest" not in args
    assert "SERVER=blm" in args
    assert "SOURCE_DIRTY=1" in args


def test_publish_and_latest_require_explicit_flags(tmp_path, monkeypatch):
    result, args = _run_wrapper(tmp_path, monkeypatch, push="1", latest="1", dirty=False)
    assert result.returncode == 0, result.stderr
    assert "--push" in args
    assert "--load" not in args
    assert "ghcr.io/gsa-tts/mcp-server-nepa-blm:latest" in args


def test_invalid_publish_flag_fails_before_docker(tmp_path, monkeypatch):
    result, args = _run_wrapper(tmp_path, monkeypatch, push="yes")
    assert result.returncode == 2
    assert "PUSH must be 0 or 1" in result.stderr
    assert args == []


def test_publish_from_dirty_worktree_fails_before_docker(tmp_path, monkeypatch):
    result, args = _run_wrapper(tmp_path, monkeypatch, push="1")
    assert result.returncode == 2
    assert "Refusing to publish from a dirty worktree" in result.stderr
    assert args == []
