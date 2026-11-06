"""Deterministic stdio MCP fixture; this is not application runtime code."""
import json
import sys
import time
import os

sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    if "id" not in request:
        continue
    result = {}
    if method == "initialize":
        result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                  "serverInfo": {"name": "sencode-test", "version": "1"}}
    elif method == "tools/list":
        if request.get("params", {}).get("cursor"):
            result = {"tools": [{"name": "second", "description": "Second page",
                                 "inputSchema": {"type": "object"}}]}
        else:
            result = {"tools": [{"name": "echo", "description": "Echo arguments",
                                 "inputSchema": {"type": "object"}}], "nextCursor": "page2"}
    elif method == "tools/call":
        params = request.get("params", {})
        if params.get("name") == "slow":
            time.sleep(10)
        if params.get("name") == "exit":
            os._exit(23)
        if params.get("name") == "oversize":
            sys.stdout.write("x" * 1100000)
            sys.stdout.flush()
            time.sleep(10)
        # Fill stderr beyond ordinary pipe capacity while retaining stdout framing.
        sys.stderr.write("fixture diagnostic\n" * 8192)
        sys.stderr.flush()
        result = {"content": [{"type": "text", "text": json.dumps(params.get("arguments"), ensure_ascii=False)}]}
    else:
        print(json.dumps({"jsonrpc": "2.0", "id": request["id"],
                          "error": {"code": -32601, "message": "Unknown method"}}), flush=True)
        continue
    encoded = (json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": result}, ensure_ascii=False) + "\n").encode("utf-8")
    for byte in encoded:
        sys.stdout.buffer.write(bytes([byte]))
        sys.stdout.buffer.flush()
