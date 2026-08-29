# CU-dsh

本地屏幕感知 + 视觉桥。钉住一个窗口,读 0-1000 网格图,然后操作;或者
一键把实拍交给本地/云端多模态模型反详细描述——**给 DSH 文本 agent 的
视觉替补**。

一个核心,两种面孔:

- CLI:`python -m cu_dsh perceive|windows|act|describe|config`
- MCP:`python -m cu_dsh mcp` -> http://127.0.0.1:8771/mcp(仅回环,拒绝 0.0.0.0)

## 契约

- 网格图就是地图。按 `norm`(0-1000)或窗口 `xy` 点击 / 输入 / 拖动。
- OCR 与 YOLO 可选,默认关闭。
- 动作默认 dry-run。`--go` / `go=true` 只在 Shawn 本轮明确授权时使用。

## 视觉桥(describe)

文本模型看不了图?一条命令补上:

```
cu-dsh describe --hwnd N [--task "自定义问题"] [--timeout 240]
```

- **本地后端(默认)**:实拍 → 经 dsh-inbox MCP 桥唤醒本地多模态小弟
  (LM Studio,如 `qwen3.8-27b-uncensored-orcarouter`)→ 反详细中文描述
- **云端后端**:填个 API key 直调任意 OpenAI 兼容视觉 API——
  **qwen / 豆包 / kimi 都是**,低频看屏幕用云端按次更划算
- 切换:改 `~/.config/cu-dsh/config.toml` 的 `[vision] backend`
- 上手 5 分钟:`QUICKSTART.md`

## 路径:零硬编码(M1/M2)

所有机器路径 = **env 覆盖 > 配置文件 > 仓库推导**,代码里没有
`C:\Users\...`。任意机器验证:

```
python -m cu_dsh config
```

配置文件:`~/.config/cu-dsh/config.toml`(模板 `config.example.toml`)——
机器白名单、Tailscale 主机、WSL 布局、视觉后端。env `CU_*` 始终覆盖文件。
打包为 exe 后所有路径自动指向 exe 目录(frozen 支持)。

## OCR / YOLO

- OCR:Enikk RapidOCR UIParser,**vendored** 于 `vendor/enikk/`(MIT)
- YOLO:可选(`--yolo`),ScreenParser YOLO11-L;**AGPL 不捆绑**,推理走
  onnxruntime + 外置权重(见 `LICENSING.md` 的纯净边界)
- 权重不入库不入包,`./download-weights.sh` 一行拉取(来源官方)

## 运行

```
python -m cu_dsh windows
python -m cu_dsh perceive --hwnd N
python -m cu_dsh act --stamp STAMP
cu-dsh describe --hwnd N
```

WSL 包装(自定位,Windows python 来自 `CU_PYTHON` 或 PATH):

```
CU_PYTHON=/mnt/c/Users/you/miniconda3/python.exe ./bin/cu-dsh.sh windows
```

Windows 二进制:GitHub Releases(`cu-dsh.exe`,解压即用,不需要 Python)。

## 文档

- `QUICKSTART.md` — 5 分钟开箱
- `SKILL.md` — 操作员契约(网格/坐标/dry-run)
- `LICENSING.md` — 二进制再分发边界(MIT/Apache 纯净,权重外置)
- `BINDINGS.md` — 去硬编码工作日志(M1-M3 完成)
- `config.example.toml` — 配置模板(qwen/豆包/kimi 示例)

## 许可

MIT(见 LICENSE)。enikk 为 MIT vendored;OpenCV core Apache-2.0;
RapidOCR Apache-2.0。**ScreenParser 权重与 ultralytics 永不捆绑。**
