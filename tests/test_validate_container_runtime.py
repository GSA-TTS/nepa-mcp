import json

from scripts.validate_container_runtime import expected_tools, request_json


def test_expected_tools_parses_only_maintained_servers():
    catalog = """
| `blm` | `one` | Purpose |
| `blm` | `two` | Purpose |
| `gis` | `ignored` | Purpose |
"""
    # Supply one row for every other maintained server to satisfy completeness.
    catalog += "".join(
        f"| `{server}` | `{server}_tool` | Purpose |\n"
        for server in expected_tools.__globals__["IMAGES"]
        if server != "blm"
    )
    tools = expected_tools(catalog)
    assert tools["blm"] == {"one", "two"}
    assert "gis" not in tools


def test_request_json_decodes_sse(monkeypatch):
    class Response:
        headers = {"Content-Type": "text/event-stream", "mcp-session-id": "abc"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{}}\n\n'

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: Response())
    payload, headers = request_json("http://example.test/mcp", payload={"method": "initialize"})
    assert payload == json.loads('{"jsonrpc":"2.0","id":1,"result":{}}')
    assert headers["mcp-session-id"] == "abc"
