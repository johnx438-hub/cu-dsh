"""Vision bridge: one command from shot to description.

`describe(hwnd, task)` runs on Windows python:
1. perceive the window (existing core.perceive) -> PNG path,
2. deliver a read-image task to the vision minion via the WSL-side
   dsh-inbox MCP bridge (inbox_bridge.py),
3. poll the minion's session log (UNC + zstandard) for its text reply.

This turns the manual "cu shoot -> inbox the vision minion -> read the
answer" loop into `cu-perceive describe --hwnd N`. The minion is any DSH
session spawned with provider=lmstudio / a multimodal model (e.g.
`session_create(provider=lmstudio, model=qwen3.8-27b-uncensored-orcarouter,
persona=vision-buddy)`); point CU_VISION_SESSION at it.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from . import config
from .core import perceive

DEFAULT_TASK = (
    "看图任务:请用 read_image 工具读取这张截图并用中文详细描述画面内容"
    "(这是什么界面?有哪些可见元素:标题、按钮、列表、状态等)。"
    "要求:1) 找到名为 read_image 的工具并调用它;2) 描述基于画面事实,不要编造。"
    "截图在: {path}"
)

# WSL-side layout comes from config (M2): [wsl] checkout / sessions_rel /
# nvm_bin, env CU_WSL_* overrides; defaults match the original deployment.
_WSL_HOME = config.wsl_checkout()
_SESSIONS_REL = config.wsl_sessions_rel()
_UNC_ROOT = r"\\wsl.localhost" + "\\" + config.wsl_distro() + _WSL_HOME.replace("/", "\\")


def _wsl_python(script_wsl: str, *args: str) -> subprocess.CompletedProcess:
    """Run a python script inside WSL from Windows python.

    Passes the resolved WSL layout through env so the bridge does not need
    its own copy of the config (env CU_WSL_CHECKOUT / CU_WSL_NVM_BIN).
    """
    quoted = " ".join(shlex_quote(a) for a in args)
    exports = (
        f"export CU_WSL_CHECKOUT={shlex_quote(_WSL_HOME)} "
        f"CU_WSL_NVM_BIN={shlex_quote(config.wsl_nvm_bin())} "
        f"CU_WSL_SESSIONS_REL={shlex_quote(_SESSIONS_REL)}; "
    )
    return subprocess.run(
        ["wsl.exe", "bash", "-lc", f"cd {_WSL_HOME} && {exports} python3 {script_wsl} {quoted}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        cwd=r"C:\\",
    )


def shlex_quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


def vision_session_id() -> str:
    """Explicit CU_VISION_SESSION wins; else the newest session dir."""
    env = os.environ.get("CU_VISION_SESSION")
    if env:
        return env
    base = Path(_UNC_ROOT)
    sessions = base / _SESSIONS_REL.replace("/", "\\")
    if sessions.exists():
        dirs = sorted(
            (p for p in sessions.iterdir() if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if dirs:
            return dirs[0].name
    raise RuntimeError(
        "no vision session found: set CU_VISION_SESSION=<session_id> "
        "(spawn one with session_create(provider='lmstudio', model='qwen3.8-27b-uncensored-orcarouter', persona='vision-buddy'))"
    )


def _session_log_unc(session_id: str) -> Path:
    return Path(_UNC_ROOT) / _SESSIONS_REL.replace("/", "\\") / session_id / "session.jsonl.zstd"


def _latest_reply_text(session_id: str, seen: set) -> str | None:
    """Latest assistant text reply in the minion's session log (None if none new)."""
    import zstandard as zstd

    log = _session_log_unc(session_id)
    if not log.exists():
        return None
    try:
        with open(log, "rb") as f:
            data = zstd.ZstdDecompressor().stream_reader(f).read()
    except Exception:
        return None
    latest: str | None = None
    for line in data.decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "assistant/message":
            content = e.get("data", {}).get("message", {}).get("content", [])
            for block in content:
                if block.get("type") == "text" and block.get("text"):
                    latest = block["text"]
    if latest is None or latest in seen:
        return None
    return latest


def describe(
    hwnd: int,
    task: str | None = None,
    session_id: str | None = None,
    timeout: int = 240,
    out_dir: str | None = None,
) -> dict:
    """Shot the window, wake the vision minion, return its description."""
    import zstandard  # noqa: F401  (probe availability early)

    shot = perceive(hwnd=hwnd, out_dir=out_dir)
    image = shot.get("map") or shot.get("json") or ""
    sid = session_id or vision_session_id()
    body = (task or DEFAULT_TASK).format(path=image)

    # 1. Baseline the minion's latest reply BEFORE delivering, then wait for
    #    a NEWER assistant text (the reply to this task, not an older one).
    seen: set[str] = set()
    _latest_reply_text(sid, seen)

    # 2. Deliver the read-image task through the WSL inbox bridge.
    bridge_wsl = f"{_WSL_HOME}/docs/research/dsh-cu-perceive/cu_dsh/inbox_bridge.py"
    body_json = json.dumps(body, ensure_ascii=False)
    r = _wsl_python(bridge_wsl, sid, body_json)
    if r.returncode != 0:
        raise RuntimeError(f"inbox bridge failed: {r.stdout or r.stderr}")

    # 3. Poll the minion session log for a fresh text reply.
    deadline = time.time() + timeout
    while time.time() < deadline:
        text = _latest_reply_text(sid, seen)
        if text is not None:
            return {
                "stamp": shot.get("stamp", ""),
                "session": sid,
                "image": image,
                "description": text.strip(),
            }
        time.sleep(5)
    raise TimeoutError(f"vision minion {sid} did not reply within {timeout}s")
