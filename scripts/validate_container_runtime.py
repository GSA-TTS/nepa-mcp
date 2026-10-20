"""Validate the local runtime contracts of all maintained NEPA MCP images."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "docs" / "mcp-tool-catalog.md"
DEFAULT_REPORT = Path("/tmp/nepa-mcp-runtime-validation.json")
CATALOG_ROW = re.compile(r"^\| `(?P<server>[^`]+)` \| `(?P<tool>[^`]+)` \|")
IMAGES = {
    "blm": "mcp-server-nepa-blm",
    "census": "mcp-server-nepa-census",
    "cfr": "mcp-server-nepa-cfr",
    "efh": "mcp-server-nepa-efh",
    "epa_acres": "mcp-server-nepa-epa-acres",
    "epa_aqs": "mcp-server-nepa-epa-aqs",
    "esa_ranges": "mcp-server-nepa-esa-ranges",
    "fema_nfhl": "mcp-server-nepa-fema-nfhl",
    "gbif": "mcp-server-nepa-gbif",
    "ipac": "mcp-server-nepa-ipac",
    "noaa": "mcp-server-nepa-noaa",
    "nrhp": "mcp-server-nepa-nrhp",
    "padus": "mcp-server-nepa-usgs-padus",
    "pcsrf": "mcp-server-nepa-noaa-pcsrf",
    "tigerweb_counties": "mcp-server-nepa-tigerweb-counties",
    "tribal": "mcp-server-nepa-tribal",
    "usace": "mcp-server-nepa-usace",
}


@dataclass
class ValidationResult:
    server: str
    image: str
    port: int
    health: str
    tools: list[str]
    status: str
    error: str | None = None
    logs: str | None = None


def expected_tools(catalog: str) -> dict[str, set[str]]:
    """Parse expected tool names from the generated catalog."""
    tools = {server: set() for server in IMAGES}
    for line in catalog.splitlines():
        match = CATALOG_ROW.match(line)
        if match and match.group("server") in tools:
            tools[match.group("server")].add(match.group("tool"))
    missing = sorted(server for server, names in tools.items() if not names)
    if missing:
        raise ValueError(f"generated catalog has no tools for: {', '.join(missing)}")
    return tools


def docker(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["docker", *args], check=check, capture_output=True, text=True)


def request_json(
    url: str,
    *,
    payload: dict[str, object] | None = None,
    session_id: str | None = None,
    timeout: float = 10,
) -> tuple[dict[str, object] | None, dict[str, str]]:
    """Send an MCP-compatible request and decode JSON or SSE JSON data."""
    headers = {"Accept": "application/json, text/event-stream"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    if session_id:
        headers["mcp-session-id"] = session_id
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode()
        response_headers = {key.lower(): value for key, value in response.headers.items()}
    if not body.strip():
        return None, response_headers
    if response_headers.get("content-type", "").startswith("text/event-stream"):
        data_lines = [line.removeprefix("data: ") for line in body.splitlines() if line.startswith("data: ")]
        if not data_lines:
            raise ValueError(f"SSE response contained no data event: {body[:500]}")
        body = "\n".join(data_lines)
    return json.loads(body), response_headers


def wait_for_health(port: int, container: str, timeout: float) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/health"
    last_error = "health endpoint did not respond"
    while time.monotonic() < deadline:
        state = docker("inspect", "--format", "{{.State.Status}}", container, check=False).stdout.strip()
        if state == "exited":
            raise RuntimeError("container exited before becoming healthy")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return json.loads(response.read().decode())
        except (OSError, ValueError, urllib.error.URLError) as exc:
            last_error = str(exc)
            time.sleep(0.5)
    raise TimeoutError(last_error)


def validate_server(
    server: str,
    image: str,
    expected: set[str],
    port: int,
    timeout: float,
    version: str,
) -> ValidationResult:
    container = f"nepa-runtime-{server.replace('_', '-')}"
    image_ref = f"ghcr.io/gsa-tts/{image}:{version}"
    docker("rm", "--force", container, check=False)
    try:
        docker(
            "run",
            "--detach",
            "--platform",
            "linux/amd64",
            "--name",
            container,
            "--env",
            f"PORT={port}",
            "--publish",
            f"127.0.0.1:{port}:{port}",
            image_ref,
        )
        health = wait_for_health(port, container, timeout)
        if health.get("status") != "healthy" or health.get("service") != image:
            raise ValueError(f"unexpected health response: {health}")

        mcp_url = f"http://127.0.0.1:{port}/mcp"
        initialized, headers = request_json(
            mcp_url,
            payload={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "nepa-runtime-validation", "version": "1"},
                },
            },
        )
        if not initialized or initialized.get("error"):
            raise ValueError(f"initialize failed: {initialized}")
        session_id = headers.get("mcp-session-id")
        if not session_id:
            raise ValueError("initialize response omitted mcp-session-id")

        request_json(
            mcp_url,
            session_id=session_id,
            payload={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
        listed, _ = request_json(
            mcp_url,
            session_id=session_id,
            payload={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        if not listed or listed.get("error"):
            raise ValueError(f"tools/list failed: {listed}")
        actual = {tool["name"] for tool in listed["result"]["tools"]}
        if actual != expected:
            raise ValueError(
                f"tool mismatch; missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}"
            )
        return ValidationResult(server, image_ref, port, str(health["service"]), sorted(actual), "passed")
    except Exception as exc:
        log_result = docker("logs", container, check=False)
        logs = log_result.stdout + log_result.stderr
        return ValidationResult(server, image_ref, port, "failed", [], "failed", str(exc), logs[-4000:])
    finally:
        docker("rm", "--force", container, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-port", type=int, default=18100)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--version", default="0.1.6")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    contracts = expected_tools(CATALOG_PATH.read_text(encoding="utf-8"))
    results = []
    for offset, (server, image) in enumerate(IMAGES.items()):
        print(f"[{offset + 1:02d}/{len(IMAGES)}] {server}: ", end="", flush=True)
        result = validate_server(server, image, contracts[server], args.start_port + offset, args.timeout, args.version)
        results.append(result)
        print(f"{result.status} ({len(result.tools)} tools)")
        if result.error:
            print(f"  {result.error}")

    args.report.write_text(json.dumps([asdict(result) for result in results], indent=2) + "\n", encoding="utf-8")
    passed = sum(result.status == "passed" for result in results)
    print(f"Runtime validation: {passed}/{len(results)} passed; report: {args.report}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
