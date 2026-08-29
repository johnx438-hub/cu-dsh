# cu-dsh 本机绑定清点（去硬编码工作底稿）

> 2026-08-29 搬入本工作区（`docs/research/dsh-cu-dsh`）时盘点。
> 目标：把 `C:\Users\jawn\...` / `ARCHER` / WSL 映射等系统性绑定配置化，
> 最终把麻烦的部分（OCR 引擎 / 模型加载 / Windows 交互）编成二进制分发。
> 来源：`/mnt/c/Users/jawn/src/cu-dsh`（本体）+ `vendor/enikk/`（OCR 引擎，已 vendor）。

## 1. 硬编码路径（6 类）— ✅ M1 已全部落地（2026-08-29）

所有绑定收敛到 `cu_dsh/config.py`：**环境变量覆盖 > 仓库布局推导**，
代码零硬编码（`C:\Users\jawn\...` 已从源码消失）。解析结果可用
`python -m cu_dsh config` 查看。

| # | 绑定 | 收敛为 | 修复方向 |
|---|---|---|---|
| P1 | 本体根目录 | `CU_ROOT` | 默认推导自 `__file__`（仓库根），env 覆盖 |
| P2 | enikk OCR 引擎 | `CU_ENIKK_ROOT` | 默认 `<CU_ROOT>/vendor/enikk`（已 vendor）；外部 checkout 用 env 指向 |
| P3 | Python 解释器 | `CU_PYTHON` | `bin/cu-dsh.sh` 用：env 优先，其次 PATH 探测 `python.exe` |
| P4 | 出图目录 | `CU_SHOT_DIR` | 默认 `<CU_ROOT>/shots`（行为变更：旧为 `agent-bus\archive\shots\perceive`，export 该值即保留） |
| P5 | YOLO 权重 | `CU_SCREENPARSER_WEIGHT` | 默认 `<CU_ROOT>/weights/screenparser/best.pt`，gitignore + 单独下载 |
| P6 | apps.json | `CU_APPS_JSON` | 默认 `<CU_ROOT>/apps.json`；**用户级覆盖** `~/.config/cu-dsh/apps.json` 按 name 合并（`config.load_apps`） |

### 配置总表（config.py）

| env | 默认 | 说明 |
|---|---|---|
| `CU_ROOT` | 仓库根（`__file__` 推导） | 一切相对路径的锚点 |
| `CU_ENIKK_ROOT` | `<CU_ROOT>/vendor/enikk` | 缺失时抛错并提示设 env |
| `CU_SHOT_DIR` | `<CU_ROOT>/shots` | perceive/act 出图 |
| `CU_APPS_JSON` | `<CU_ROOT>/apps.json` | launch 清单（包级） |
| `CU_SCREENPARSER_WEIGHT` | `<CU_ROOT>/weights/screenparser/best.pt` | yolo 权重 |
| `CU_PYTHON` | PATH 探测 | 仅 `bin/cu-dsh.sh` 用 |
| `CU_WSL_DISTRO` | `Ubuntu` | UNC 映射发行版（M3 前半） |

配套改动：`cu_dsh/__init__.py` 改 PEP 562 懒加载（重依赖 cv2/PIL 不再
在 import 时拉入，CLI 帮助 / config / 测试 / MCP 启动均轻量）；新增
`tests/test_config.py`（6 个用例，env 覆盖 / 引号剥离 / 合并 / 容错 dump，
Linux 可跑，不依赖 Windows）。

## 2. 机器 / 用户绑定

| # | 绑定 | 出现位置 | 修复方向 |
|---|---|---|---|
| M1 | 机器名 `ARCHER` | `cu_dsh/mcp_server.py:1`（"Must run on ARCHER"） | 去掉机器名校验，只留"需 Windows 目标"检查 |
| M2 | Windows 用户 `jawn` | 全部 `C:\Users\jawn` | 随 P1–P6 配置化 |
| M3 | WSL 用户 `archer` / 发行版 `Ubuntu` | `cu_dsh/paths.py`（UNC 映射） | `WSL_DISTRO`/`WSL_USER` 配置或探测 |
| M4 | 描述 "Shawn 的 Windows 桌面" | `SKILL.md` / 人设 | 泛化为"目标机"描述 |

## 3. 环境假设

- Windows 目标（本质合理：computer-use 工具），但 **WSL 调用链**要文档化/可选；
- miniconda3 → 解释器可探测（`python -m cu_dsh` 优先，`CU_PYTHON` 覆盖）；
- enikk 是 Windows PyInstaller exe（`vendor/enikk/enikk.spec` + `build.bat`）——
  正好是"编成二进制"的现成先例。

## 4. 二进制化候选（"麻烦的部分"）

| 候选 | 原因 | 方案 |
|---|---|---|
| enikk（OCR UIParser） | 外部依赖 + C++/ONNX 提速 | 已 vendor；保留 exe 构建，随包分发或 pip 包 |
| screenparser YOLO | 265M 权重 + 推理 | 权重单独下载（HuggingFace/Release asset），推理代码可 Nuitka/PyInstaller |
| 整体 CLI | 用户不需要 Python 环境 | `pyinstaller`/`nuitka` 打 `cu-dsh.exe`（参考 enikk.spec） |

## 5. 里程碑

- [x] M0：搬入独立工作区 + vendor enikk + 绑定清点
- [x] M1：路径配置化（P1–P6 → env/配置文件），代码零硬编码
- [ ] M2：机器名/用户绑定去除（M1–M4）
- [ ] M3：Windows 侧构建链独立（enikk exe + cu-dsh exe）
- [ ] M4：发布形态（MCP server vs cordis 插件）定稿 + 泛化文档
- [ ] M5：社区发布（npm/GitHub/dsh-plugin topic，复用 A/B 的发布链路）
