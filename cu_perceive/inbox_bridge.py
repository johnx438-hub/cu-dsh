"""WSL-side MCP stdio bridge: deliver a task into a DSH session via dsh-inbox.

Runs on WSL python (no external deps): spawns `scripts/dsh-inbox-mcp.ts`
(stdio transport) from the minimal-agent-ts checkout, performs the MCP
handshake, and calls the `dsh_inbox_deliver` tool. Used by cu-perceive's
`describe` command (which runs on Windows python and shells out here) so the
vision minion can be woken up without a persistent MCP client.

Usage: python3 inbox_bridge.py <session_id> <body-json>
Exit 0 with the tool result JSON on stdout; non-zero with error on stderr.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

CHECKOUT = "/home/archer/zerostack-analysis/minimal-agent-ts"
NVM_BIN = "/home/archer/.nvm/versions/node/v24.14.1/bin"
HOUSE = os.environ.get("DSH_INBOX_HOUSE", "dsh-local")
TRUST = os.environ.get("DSH_INBOX_TRUST", "dogfood-trust")
FROM = os.environ.get("INBOX_FROM", "cu-dsh")


def _env() -> dict:
    """PATH with the WSL nvm node bin first (wsl.exe interop can leak the
    Windows node into PATH and break `npx tsx`)."""
    env = dict(os.environ)
    env["PATH"] = f"{NVM_BIN}:" + env.get("PATH", "")
    return env


def _recv_until(proc: subprocess.Popen, msgid: int) -> dict:
    for line in proc.stdout:  # type: ignore[union-attr]
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("id") == msgid:
            return msg
    raise RuntimeError("dsh-inbox MCP closed before responding")


def deliver(session_id: str, body: str) -> dict:
    proc = subprocess.Popen(
        ["npx", "tsx", "scripts/dsh-inbox-mcp.ts"],
        cwd=CHECKOUT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        bufsize=1,
        env=_env(),
    )
    try:
        assert proc.stdin and proc.stdout
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "cu-dsh-bridge", "version": "0.1"},
            },
        }) + "\n")
        proc.stdin.flush()
        _recv_until(proc, 1)
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0", "method": "notifications/initialized",
        }) + "\n")
        proc.stdin.flush()
        proc.stdin.write(json.dumps({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {
                "name": "dsh_inbox_deliver",
                "arguments": {
                    "session_id": session_id,
                    "body": body,
                    "kind": "task",
                    "from_id": FROM,
                    "house_id": HOUSE,
                    "trust_id": TRUST,
                },
            },
        }) + "\n")
        proc.stdin.flush()
        return _recv_until(proc, 2)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: inbox_bridge.py <session_id> <body-json>", file=sys.stderr)
        return 2
    session_id, body = sys.argv[1], sys.argv[2]
    try:
        result = deliver(session_id, body)
    except Exception as exc:  # noqa: BLE001 - report any bridge failure
        print(f"bridge error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
