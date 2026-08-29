# cu-dsh

Private dogfood. Pin one window, read the 0-1000 grid map, then act.

One core, two faces:

- CLI: `python -m cu_dsh perceive|windows|act|config`
- MCP: `python -m cu_dsh mcp` -> http://127.0.0.1:8771/mcp (loopback only; do not bind 0.0.0.0)

8766 may still listen as a leftover instance. Testers use **8771**.

## Contract

- The grid map is the map. Click / type / drag by `norm` (0-1000) or window `xy`.
- OCR and YOLO are optional and off by default.
- Actions default to dry-run. `--go` / `go=true` only when Shawn said so this turn.

## Paths: zero hardcoded (M1)

All machine paths resolve from **env override > config file > derived default** —
no `C:\Users\...` anywhere in the code. Verify on any machine with:

    python -m cu_dsh config

Config file: `~/.config/cu-dsh/config.toml` (or `CU_CONFIG`), template in
`config.example.toml` — machine allowlist, tailscale host, WSL layout.
Env vars always beat the file:

| Env var | Default |
|---|---|
| `CU_ROOT` | this repo (derived from `__file__`) |
| `CU_ENIKK_ROOT` | `<CU_ROOT>/vendor/enikk` (vendored OCR engine) |
| `CU_SHOT_DIR` | `<CU_ROOT>/shots` |
| `CU_APPS_JSON` | `<CU_ROOT>/apps.json` (+ per-user override `~/.config/cu-dsh/apps.json`, merged by name) |
| `CU_SCREENPARSER_WEIGHT` | `<CU_ROOT>/weights/screenparser/best.pt` |
| `CU_PYTHON` | PATH probe (`python.exe`) — used by `bin/cu-dsh.sh` |
| `CU_WSL_DISTRO` | `Ubuntu` (UNC path mappings) |
| `CU_WSL_CHECKOUT` / `CU_WSL_NVM_BIN` / `CU_WSL_SESSIONS_REL` | config `[wsl]` / original deployment values |
| `CU_MACHINE_ALLOWLIST` | config `[machine] allowlist`; empty = MCP serves any host |
| `CU_TAILSCALE_HOST` | config `[tailscale] host`; empty = no tailscale admission |
| `CU_CONFIG` | `~/.config/cu-dsh/config.toml` |

> Behavior change vs pre-M1: default shots moved from
> `C:\Users\jawn\agent-bus\archive\shots\perceive` to `<CU_ROOT>/shots`.
> Export `CU_SHOT_DIR` to the old path to keep old stamps discoverable.

## OCR / YOLO

- OCR uses Enikk RapidOCR `UIParser`, **vendored** at `vendor/enikk/` (was a
  sibling checkout). Set `CU_ENIKK_ROOT` to use an external checkout instead.
- YOLO is an optional extra (`--yolo` / `yolo=true`) via ScreenParser
  (`ultralytics` YOLO11-L). That extra is AGPL; keep it optional.
- Weights are not in git (downloaded separately). See `weights/README.md` and
  `vendor/enikk/weights/README.md`.

## Run

    python -m cu_dsh windows
    python -m cu_dsh perceive --hwnd N
    python -m cu_dsh act --stamp STAMP

WSL wrapper (self-locating; Windows python from `CU_PYTHON` or PATH):

    CU_PYTHON=/mnt/c/Users/you/miniconda3/python.exe ./bin/cu-dsh.sh windows

See `SKILL.md` for the operator contract and `BINDINGS.md` for the
de-hardcoding worklog (M1-M3 done, M4 pending).

**New here? Start with `QUICKSTART.md`** — 5-minute setup to shot a window
and have a local multimodal model describe it (`cu-dsh describe`).
