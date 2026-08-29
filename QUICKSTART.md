# CU-dsh 快速上手(5 分钟开箱)

本地屏幕感知 + 本地多模态描述。**给 DSH 文本 agent 的视觉替补**：
纯文本模型看不了图？`cu-dsh describe --hwnd N` = 实拍窗口 → 唤醒本地
多模态模型 → 详细中文描述。

## 你需要的（先看清楚，别白装）

| 需要 | 说明 | 没有会怎样 |
|---|---|---|
| Windows 10/11 | CU-dsh 是 Windows 工具（枚举窗口/截图） | — |
| Python 3.11+（可选） | 跑源码；或直接用 release 的 exe | 用 exe 就不需要 |
| **本地多模态模型** | 如 Qwen2.5-VL 27B（LM Studio 加载） | describe 会等不到回复 |

> 门槛提醒：多模态模型 27B 量化后约需 ~16GB 显存/内存。**已有本地 GPU
> 或 LM Studio 的人 5 分钟见效；没有的人请先掂量**——低频看屏幕用云端
> API 可能更划算。

## 5 分钟路径

**第 1 分钟 — 拿代码或 exe**

```bash
# 源码（推荐，可改可学）
git clone https://github.com/johnx438-hub/cu-dsh.git
cd cu-dsh

# 或直接下 Windows 二进制（Release 页）：
#   https://github.com/johnx438-hub/cu-dsh/releases
#   解压后直接用 cu-dsh.exe
```

**第 2 分钟 — 装依赖（源码方式）**

```bash
python -m pip install -r requirements.txt   # 或 pip install cu-dsh 之后提供
```

**第 3 分钟 — 下载模型权重（不进仓库、不进 exe）**

```bash
./download-weights.sh        # rapidocr(OCR) + screenparser(YOLO)，来源官方
```

**第 4 分钟 — 起本地多模态**

LM Studio 加载 Qwen2.5-VL（或任意多模态 GGUF），开本地 server（默认 1234 端口）。

**第 5 分钟 — 一条命令看屏幕**

```bash
cu-dsh describe --hwnd N    # N = 窗口句柄；0 = 主屏
```

把 `CU_VISION_SESSION` 指到你的多模态 DSH session（或用自动发现）。

## 验证一切正常

```bash
cu-dsh config              # 路径/机器配置解析，确认无硬编码报错
cu-dsh windows             # 列出窗口 → 挑一个 hwnd
cu-dsh describe --hwnd <那个 hwnd>
```

## 配置（可选）

`~/.config/cu-dsh/config.toml`（模板 `config.example.toml`）：
`[machine] allowlist`（MCP 机器门）、`[tailscale] host`、`[wsl]` 布局。
env `CU_*` 始终覆盖文件。

## 完整契约

操作员级细节（0-1000 网格、dry-run 默认、OCR/YOLO 开关）见 `SKILL.md`；
许可与再分发边界见 `LICENSING.md`。
