"""M1: config resolution — env override, repo-derived defaults, apps merge.

Runs on any platform (config.py has no heavy deps), so CI/WSL can verify
the path layer without cv2/PIL/Windows.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cu_dsh import config

_ENV_VARS = (
    "CU_ROOT",
    "CU_ENIKK_ROOT",
    "CU_SHOT_DIR",
    "CU_APPS_JSON",
    "CU_SCREENPARSER_WEIGHT",
    "CU_PYTHON",
    "CU_WSL_DISTRO",
    "CU_CONFIG",
    "CU_MACHINE_ALLOWLIST",
    "CU_WSL_CHECKOUT",
    "CU_WSL_NVM_BIN",
    "CU_WSL_SESSIONS_REL",
    "CU_TAILSCALE_HOST",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    for fn in (
        config.cu_root,
        config.enikk_root,
        config.shot_dir,
        config.cu_weights_dir,
        config.screenparser_weight,
        config.apps_json,
        config.user_apps_json,
        config.wsl_distro,
        config.cu_python,
        config.config_file,
        config._toml,
    ):
        fn.cache_clear()


def test_defaults_derive_from_repo_layout():
    root = Path(__file__).resolve().parent.parent
    assert config.cu_root() == root
    assert config.enikk_root() == root / "vendor" / "enikk"
    assert config.shot_dir() == root / "shots"
    assert config.cu_weights_dir() == root / "weights"
    assert config.screenparser_weight() == root / "weights" / "screenparser" / "best.pt"
    assert config.apps_json() == root / "apps.json"
    assert config.wsl_distro() == "Ubuntu"
    assert config.cu_python() is None


def test_env_overrides(monkeypatch, tmp_path):
    enikk = tmp_path / "enikk"
    enikk.mkdir()  # enikk_root fail-fasts on missing dir
    monkeypatch.setenv("CU_ROOT", str(tmp_path))
    monkeypatch.setenv("CU_ENIKK_ROOT", str(enikk))
    monkeypatch.setenv("CU_SHOT_DIR", str(tmp_path / "shots"))
    monkeypatch.setenv("CU_SCREENPARSER_WEIGHT", str(tmp_path / "best.pt"))
    monkeypatch.setenv("CU_APPS_JSON", str(tmp_path / "apps.json"))
    monkeypatch.setenv("CU_PYTHON", r"C:\Users\x\python.exe")
    monkeypatch.setenv("CU_WSL_DISTRO", "Arch")

    assert config.cu_root() == tmp_path
    assert config.enikk_root() == enikk
    assert config.shot_dir() == tmp_path / "shots"
    assert config.screenparser_weight() == tmp_path / "best.pt"
    assert config.apps_json() == tmp_path / "apps.json"
    assert config.cu_python() == r"C:\Users\x\python.exe"
    assert config.wsl_distro() == "Arch"


def test_env_values_have_quotes_stripped(monkeypatch, tmp_path):
    monkeypatch.setenv("CU_SHOT_DIR", f'"{tmp_path / "shots"}"')
    assert config.shot_dir() == tmp_path / "shots"


def test_missing_enikk_raises_with_helpful_message(monkeypatch, tmp_path):
    monkeypatch.setenv("CU_ENIKK_ROOT", str(tmp_path / "nope"))
    with pytest.raises(FileNotFoundError, match="CU_ENIKK_ROOT"):
        config.enikk_root()


def test_apps_merge_package_then_user(monkeypatch, tmp_path):
    pkg = tmp_path / "apps.json"
    usr = tmp_path / ".config" / "cu-perceive" / "apps.json"
    usr.parent.mkdir(parents=True)
    pkg.write_text(json.dumps([
        {"name": "steam", "exe": r"D:\steam.exe"},
        {"name": "chrome", "exe": r"C:\chrome.exe"},
    ]), encoding="utf-8")
    usr.write_text(json.dumps([
        {"name": "chrome", "exe": r"C:\custom\chrome.exe"},
        {"name": "newapp", "exe": r"D:\new.exe"},
    ]), encoding="utf-8")
    monkeypatch.setenv("CU_APPS_JSON", str(pkg))
    monkeypatch.setenv("HOME", str(tmp_path))

    apps = config.load_apps()
    names = [a["name"] for a in apps]
    assert names == ["steam", "chrome", "newapp"]  # package order; override in place; user app appended
    assert apps[1]["exe"] == r"C:\custom\chrome.exe"  # user override wins
    assert apps[0]["exe"] == r"D:\steam.exe"  # untouched package entry
    assert config.user_apps_json() == tmp_path / ".config" / "cu-perceive" / "apps.json"


def test_dump_is_resilient_and_complete(monkeypatch, tmp_path):
    monkeypatch.setenv("CU_ENIKK_ROOT", str(tmp_path / "nope"))
    d = config.dump()
    assert d["cu_root"] == str(Path(__file__).resolve().parent.parent)
    assert d["enikk_root"].startswith("<missing:")
    assert d["wsl_distro"] == "Ubuntu"
    assert set(d) >= {
        "cu_root", "enikk_root", "shot_dir", "cu_weights_dir",
        "screenparser_weight", "apps_json", "user_apps_json",
        "wsl_distro", "cu_python", "apps_count",
    }


def _write_config(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "config.toml"
    p.write_text(text, encoding="utf-8")
    return p


def test_config_file_toml_resolution(monkeypatch, tmp_path):
    cfg = _write_config(tmp_path, """
[machine]
allowlist = ["ARCHER", "other-box"]

[wsl]
checkout = "/home/alice/minimal-agent-ts"
nvm_bin = "/home/alice/.nvm/versions/node/v22/bin"
sessions_rel = "docs/research/other/.dsh-home/sessions/--x--"

[tailscale]
host = "alice.tailnet.ts.net"
""")
    monkeypatch.setenv("CU_CONFIG", str(cfg))
    assert config.config_file() == cfg
    assert config.machine_allowlist() == ["ARCHER", "other-box"]
    assert config.wsl_checkout() == "/home/alice/minimal-agent-ts"
    assert config.wsl_nvm_bin() == "/home/alice/.nvm/versions/node/v22/bin"
    assert config.wsl_sessions_rel() == "docs/research/other/.dsh-home/sessions/--x--"
    assert config.tailscale_host() == "alice.tailnet.ts.net"


def test_env_overrides_config_file(monkeypatch, tmp_path):
    cfg = _write_config(tmp_path, '[wsl]\ncheckout = "/home/alice/checkout"\n')
    monkeypatch.setenv("CU_CONFIG", str(cfg))
    monkeypatch.setenv("CU_WSL_CHECKOUT", "/home/env-override/checkout")
    assert config.wsl_checkout() == "/home/env-override/checkout"


def test_machine_allowlist_env_and_defaults(monkeypatch):
    # empty config + no env -> no machine check
    assert config.machine_allowlist() == []
    monkeypatch.setenv("CU_MACHINE_ALLOWLIST", " ARCHER , box2 ")
    assert config.machine_allowlist() == ["ARCHER", "box2"]


def test_missing_config_file_is_empty(monkeypatch, tmp_path):
    monkeypatch.setenv("CU_CONFIG", str(tmp_path / "nope.toml"))
    assert config.machine_allowlist() == []
    assert config.wsl_checkout() == "/home/archer/zerostack-analysis/minimal-agent-ts"
    assert config.tailscale_host() is None


def test_vision_backend_config(monkeypatch, tmp_path):
    # default backend is lmstudio
    assert config.vision_backend() == "lmstudio"
    assert config.vision_base_url() is None
    assert config.vision_api_key() is None

    cfg = _write_config(tmp_path, """
[vision]
backend = "openai"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
model = "qwen-vl-max"
api_key_env = "DASHSCOPE_API_KEY"
""")
    monkeypatch.setenv("CU_CONFIG", str(cfg))
    config.config_file.cache_clear()
    config._toml.cache_clear()
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    assert config.vision_backend() == "openai"
    assert config.vision_base_url() == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert config.vision_model() == "qwen-vl-max"
    # api_key_env resolves the named env var
    assert config.vision_api_key() == "sk-test"
    # direct CU_VISION_API_KEY beats api_key_env
    monkeypatch.setenv("CU_VISION_API_KEY", "sk-direct")
    assert config.vision_api_key() == "sk-direct"
