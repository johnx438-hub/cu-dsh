# cu-perceive 本机绑定清点（去硬编码工作底稿）

> 2026-08-29 搬入本工作区（`docs/research/dsh-cu-perceive`）时盘点。
> 目标：把 `C:\Users\jawn\...` / `ARCHER` / WSL 映射等系统性绑定配置化，
> 最终把麻烦的部分（OCR 引擎 / 模型加载 / Windows 交互）编成二进制分发。
> 来源：`/mnt/c/Users/jawn/src/cu-perceive`（本体）+ `vendor/enikk/`（OCR 引擎，已 vendor）。

## 1. 硬编码路径（6 类）

| # | 绑定 | 出现位置 | 用途 | 修复方向 |
|---|---|---|---|---|
| P1 | `C:\Users\jawn\src\cu-perceive` | `cu_perceive/core.py`、`launch.py`、`yolo.py`、`bin/cu-perceive.sh` | 本体/APPS/权重根目录 | `CU_ROOT` 环境变量 / 推导自 `__file__` |
| P2 | `C:\Users\jawn\src\enikk` | `cu_perceive/core.py:13`、`windows.py:9`、`bin/cu-perceive.sh` | **OCR 引擎（外部 checkout，未 vendored）** | 已 vendor 到 `vendor/enikk/` → 配置 `ENIKK_ROOT`，优先用 vendor |
| P3 | `C:\Users\jawn\miniconda3\python.exe` | `bin/cu-perceive.sh:6`、README | Python 解释器 | 配置 `CU_PYTHON` / `PATH` 探测 |
| P4 | `C:\Users\jawn\agent-bus\archive\shots\perceive` | `cu_perceive/act.py:8`、`core.py:14` | 出图目录 | 配置 `CU_SHOT_DIR` |
| P5 | `...\cu-perceive\weights\screenparser\best.pt` | `yolo.py:8` | YOLO 权重 | 相对 `CU_ROOT/weights`，已 gitignore、单独下载 |
| P6 | `...\cu-perceive\apps.json` | `launch.py:9` | 启动应用清单 | 相对 `CU_ROOT`，用户级覆盖（`~/.config/cu-perceive/apps.json`） |

## 2. 机器 / 用户绑定

| # | 绑定 | 出现位置 | 修复方向 |
|---|---|---|---|
| M1 | 机器名 `ARCHER` | `cu_perceive/mcp_server.py:1`（"Must run on ARCHER"） | 去掉机器名校验，只留"需 Windows 目标"检查 |
| M2 | Windows 用户 `jawn` | 全部 `C:\Users\jawn` | 随 P1–P6 配置化 |
| M3 | WSL 用户 `archer` / 发行版 `Ubuntu` | `cu_perceive/paths.py`（UNC 映射） | `WSL_DISTRO`/`WSL_USER` 配置或探测 |
| M4 | 描述 "Shawn 的 Windows 桌面" | `SKILL.md` / 人设 | 泛化为"目标机"描述 |

## 3. 环境假设

- Windows 目标（本质合理：computer-use 工具），但 **WSL 调用链**要文档化/可选；
- miniconda3 → 解释器可探测（`python -m cu_perceive` 优先，`CU_PYTHON` 覆盖）；
- enikk 是 Windows PyInstaller exe（`vendor/enikk/enikk.spec` + `build.bat`）——
  正好是"编成二进制"的现成先例。

## 4. 二进制化候选（"麻烦的部分"）

| 候选 | 原因 | 方案 |
|---|---|---|
| enikk（OCR UIParser） | 外部依赖 + C++/ONNX 提速 | 已 vendor；保留 exe 构建，随包分发或 pip 包 |
| screenparser YOLO | 265M 权重 + 推理 | 权重单独下载（HuggingFace/Release asset），推理代码可 Nuitka/PyInstaller |
| 整体 CLI | 用户不需要 Python 环境 | `pyinstaller`/`nuitka` 打 `cu-perceive.exe`（参考 enikk.spec） |

## 5. 里程碑

- [ ] M0（已完成）：搬入独立工作区 + vendor enikk + 绑定清点
- [ ] M1：路径配置化（P1–P6 → env/配置文件），代码零硬编码
- [ ] M2：机器名/用户绑定去除（M1–M4）
- [ ] M3：Windows 侧构建链独立（enikk exe + cu-perceive exe）
- [ ] M4：发布形态（MCP server vs cordis 插件）定稿 + 泛化文档
- [ ] M5：社区发布（npm/GitHub/dsh-plugin topic，复用 A/B 的发布链路）
