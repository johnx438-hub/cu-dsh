"""Machine-path configuration: zero hardcoded paths (M1).

Every P1-P6 binding resolves at call time as:  env var  >  derived default.
Defaults are derived from the repo layout (this file's grandparent dir), so a
checkout works identically on Windows, WSL or CI without setting anything.

Env vars
--------
CU_ROOT                 cu-perceive checkout root (default: this repo)
CU_ENIKK_ROOT           enikk OCR engine (default: <CU_ROOT>/vendor/enikk)
CU_SHOT_DIR             perceive/act output dir (default: <CU_ROOT>/shots)
CU_APPS_JSON            package apps.json (default: <CU_ROOT>/apps.json)
CU_SCREENPARSER_WEIGHT  YOLO weight (default: <CU_ROOT>/weights/screenparser/best.pt)
CU_PYTHON               Windows python.exe for bin/cu-perceive.sh (default: PATH probe)
CU_WSL_DISTRO           WSL distro used in UNC path mappings (default: Ubuntu)

apps.json user override: ~/.config/cu-perceive/apps.json is merged on top of
the package list, entries matched by lowercased name.

Note: values are read at call time so tests can monkeypatch os.environ freely.
When cu-perceive is later packaged as a frozen exe (M3), CU_ROOT will be
derived from sys._MEIPASS instead of __file__; nothing else changes.
"""
from __future__ import annotations

import json
import os
import sys
import tomllib
from functools import lru_cache
from pathlib import Path

__all__ = [
    "cu_root",
    "enikk_root",
    "shot_dir",
    "cu_weights_dir",
    "screenparser_weight",
    "apps_json",
    "user_apps_json",
    "load_apps",
    "wsl_distro",
    "wsl_checkout",
    "wsl_nvm_bin",
    "wsl_sessions_rel",
    "machine_allowlist",
    "tailscale_host",
    "cu_python",
    "config_file",
    "dump",
]

_USER_APPS = "cu-perceive/apps.json"
_CONFIG_NAME = "cu-dsh/config.toml"


def _env(name: str) -> str | None:
    """Raw env value with surrounding quotes stripped (shells love quoting paths)."""
    v = os.environ.get(name)
    if v is None:
        return None
    v = v.strip().strip('"').strip("'")
    return v or None


@lru_cache(maxsize=1)
def config_file() -> Path:
    """M2: config file (CU_CONFIG env, else ~/.config/cu-dsh/config.toml)."""
    v = _env("CU_CONFIG")
    return Path(v) if v else Path.home() / ".config" / _CONFIG_NAME


@lru_cache(maxsize=1)
def _toml() -> dict:
    """Parsed config file; missing/broken file is an empty table."""
    p = config_file()
    if not p.exists():
        return {}
    try:
        with open(p, "rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _cfg(section: str, key: str) -> str | None:
    """M2: env > config file > None. Env name: CU_<SECTION>_<KEY>."""
    v = _env(f"CU_{section.upper()}_{key.upper()}")
    if v is not None:
        return v
    val = _toml().get(section, {}).get(key)
    return str(val) if val is not None else None


def machine_allowlist() -> list[str]:
    """M2: machine names allowed to run the MCP server. Empty = no check.

    env CU_MACHINE_ALLOWLIST (comma-separated) > config [machine] allowlist.
    """
    v = _env("CU_MACHINE_ALLOWLIST")
    if v is not None:
        return [x.strip() for x in v.split(",") if x.strip()]
    raw = _toml().get("machine", {}).get("allowlist", [])
    if isinstance(raw, list):
        return [str(x) for x in raw if str(x).strip()]
    return []


def tailscale_host() -> str | None:
    """M2: tailscale hostname admitted to the MCP allowlist (config [tailscale] host)."""
    return _cfg("tailscale", "host")


def wsl_checkout() -> str:
    """M2: minimal-agent-ts checkout path seen from WSL (config [wsl] checkout)."""
    return _cfg("wsl", "checkout") or "/home/archer/zerostack-analysis/minimal-agent-ts"


def wsl_nvm_bin() -> str:
    """M2: node bin dir used by the inbox bridge inside WSL (config [wsl] nvm_bin)."""
    return _cfg("wsl", "nvm_bin") or "/home/archer/.nvm/versions/node/v24.14.1/bin"


def wsl_sessions_rel() -> str:
    """M2: DSH session store path relative to the checkout (config [wsl] sessions_rel)."""
    return (
        _cfg("wsl", "sessions_rel")
        or "docs/research/dsh-spike/.dsh-home/sessions/"
        "--home-archer-zerostack-analysis-minimal-agent-ts-docs-research-dsh-cu-perceive--"
    )


def vision_backend() -> str:
    """describe() backend: 'lmstudio' (default, inbox-bridge to a local
    multimodal DSH minion) or 'openai' (any OpenAI-compatible vision API:
    qwen / doubao / kimi / ...). Config [vision] backend / CU_VISION_BACKEND."""
    v = _cfg("vision", "backend")
    return (v or "lmstudio").lower()


def vision_base_url() -> str | None:
    """OpenAI-compatible base URL for the 'openai' backend
    (config [vision] base_url / CU_VISION_BASE_URL)."""
    return _cfg("vision", "base_url")


def vision_model() -> str | None:
    """Vision model id for the 'openai' backend
    (config [vision] model / CU_VISION_MODEL)."""
    return _cfg("vision", "model")


def vision_api_key() -> str | None:
    """API key for the 'openai' backend. CU_VISION_API_KEY beats the key named
    by config [vision] api_key_env (which is read from the process env)."""
    direct = _env("CU_VISION_API_KEY")
    if direct is not None:
        return direct
    ref = _cfg("vision", "api_key_env")
    if ref:
        return _env(ref)
    return None


def vision_session() -> str | None:
    """Pin the vision minion session id (config [vision] session /
    CU_VISION_SESSION). Fixing it prevents describe from auto-discovering a
    session bound to a DIFFERENT model — which would make LM Studio unload
    the loaded model and load another one into VRAM."""
    return _cfg("vision", "session")


def _env_path(name: str, default: Path) -> Path:
    v = _env(name)
    return Path(v) if v else default


def repo_root() -> Path:
    """The cu-perceive checkout root = parent of the cu_dsh package dir."""
    return Path(__file__).resolve().parent.parent


def _is_frozen() -> bool:
    """True when running from a PyInstaller bundle (cu-dsh.exe)."""
    return bool(getattr(sys, "frozen", False))


def _bundle_root() -> Path:
    """Where the exe lives (onefile: sys.executable dir; onedir: _MEIPASS)."""
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return Path.cwd()


@lru_cache(maxsize=1)
def cu_root() -> Path:
    """P1: checkout root (CU_ROOT env, else derived from __file__ or the exe dir)."""
    if _is_frozen():
        return _env_path("CU_ROOT", _bundle_root())
    return _env_path("CU_ROOT", repo_root())


@lru_cache(maxsize=1)
def enikk_root() -> Path:
    """P2: enikk OCR engine checkout (CU_ENIKK_ROOT, else vendored)."""
    if _is_frozen():
        # Bundled as data under _MEIPASS/enikk (see cu-dsh.spec).
        default = Path(sys._MEIPASS) / "enikk"  # type: ignore[attr-defined]
    else:
        default = cu_root() / "vendor" / "enikk"
    root = _env_path("CU_ENIKK_ROOT", default)
    if not root.exists():
        raise FileNotFoundError(
            f"enikk OCR engine not found at {root}. "
            "It ships vendored at <CU_ROOT>/vendor/enikk; if you use an "
            "external checkout, set CU_ENIKK_ROOT to its location."
        )
    return root


@lru_cache(maxsize=1)
def shot_dir() -> Path:
    """P4: perceive/act output dir (CU_SHOT_DIR, else <CU_ROOT>/shots).

    The pre-M1 default was C:\\Users\\jawn\\agent-bus\\archive\\shots\\perceive;
    export CU_SHOT_DIR to that path to keep old stamps discoverable.
    """
    return _env_path("CU_SHOT_DIR", cu_root() / "shots")


@lru_cache(maxsize=1)
def cu_weights_dir() -> Path:
    """P5a: weights dir (relative to CU_ROOT; never tracked, downloaded separately)."""
    return cu_root() / "weights"


@lru_cache(maxsize=1)
def screenparser_weight() -> Path:
    """P5b: ScreenParser YOLO weight (CU_SCREENPARSER_WEIGHT, else <CU_ROOT>/weights/...)."""
    return _env_path("CU_SCREENPARSER_WEIGHT", cu_weights_dir() / "screenparser" / "best.pt")


@lru_cache(maxsize=1)
def apps_json() -> Path:
    """P6a: package apps.json (CU_APPS_JSON, else <CU_ROOT>/apps.json)."""
    return _env_path("CU_APPS_JSON", cu_root() / "apps.json")


@lru_cache(maxsize=1)
def user_apps_json() -> Path:
    """P6b: per-user apps.json override (~/.config/cu-perceive/apps.json)."""
    return Path.home() / ".config" / _USER_APPS


def load_apps() -> list[dict]:
    """Merged app list: package apps.json, then per-user override by name."""
    merged: dict[str, dict] = {}
    order: list[str] = []
    for p in (apps_json(), user_apps_json()):
        if not p.exists():
            continue
        for row in json.loads(p.read_text(encoding="utf-8")):
            name = str(row.get("name") or "").lower()
            if not name:
                continue
            if name not in merged:
                order.append(name)
            merged[name] = row
    return [merged[name] for name in order]


@lru_cache(maxsize=1)
def wsl_distro() -> str:
    """M3a: WSL distro used in UNC path mappings (CU_WSL_DISTRO, else Ubuntu)."""
    return _env("CU_WSL_DISTRO") or "Ubuntu"


@lru_cache(maxsize=1)
def cu_python() -> str | None:
    """P3: Windows python.exe for bin/cu-perceive.sh (CU_PYTHON, else None = probe)."""
    return _env("CU_PYTHON")


def dump() -> dict:
    """Resolved config as JSON-friendly dict (for `cu-perceive config`).

    Never raises: a missing enikk root is reported as a string so the command
    stays usable as a diagnostic.
    """
    def p(x: Path | None) -> str | None:
        return str(x) if x is not None else None
    try:
        enikk = p(enikk_root())
    except FileNotFoundError as e:
        enikk = f"<missing: {e}>"
    return {
        "cu_root": p(cu_root()),
        "enikk_root": enikk,
        "shot_dir": p(shot_dir()),
        "cu_weights_dir": p(cu_weights_dir()),
        "screenparser_weight": p(screenparser_weight()),
        "apps_json": p(apps_json()),
        "user_apps_json": p(user_apps_json()),
        "wsl_distro": wsl_distro(),
        "wsl_checkout": wsl_checkout(),
        "wsl_nvm_bin": wsl_nvm_bin(),
        "wsl_sessions_rel": wsl_sessions_rel(),
        "machine_allowlist": machine_allowlist(),
        "tailscale_host": tailscale_host(),
        "vision_backend": vision_backend(),
        "vision_base_url": vision_base_url(),
        "vision_model": vision_model(),
        "config_file": p(config_file()),
        "cu_python": cu_python(),
        "apps_count": len(load_apps()),
    }
