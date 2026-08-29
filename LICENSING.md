# Licensing & redistribution (cu-dsh)

Binary distribution policy: the `.exe` must be **pure open source inside** —
no AGPL components bundled, no weights with unclear redistribution licenses.
Everything else (MIT/Apache/BSD) is fine to bundle as long as the license
texts ship **with the binary**, not just in the source repo.

## Component matrix (audited 2026-08-29, cross-checked with minimal/txyy)

| Component | License | In exe? | Redistribution duty |
|---|---|---|---|
| cu-dsh (this repo) | MIT (see LICENSE) | yes | keep copyright notice |
| enikk (vendored OCR engine) | MIT | yes | **license text must ship with the exe** (`--add-data LICENSES/`) |
| rapidocr ONNX (weights) | Apache-2.0 (code); **weights: verify source** | yes (engine) / weights on disk | ⚠️ see TODO below |
| mcp / pillow / numpy | MIT / CMU / BSD | yes | keep notices |
| opencv-python | wheel MIT; **OpenCV core Apache-2.0 since 4.5.2** (BSD before; never LGPL) | yes | keep Apache-2.0 NOTICE (no LGPL-style dynamic-link obligations) |
| ultralytics (YOLO inference) | **AGPL** | **never** | do not import; YOLO runs via onnxruntime + raw weights |
| ScreenParser `best.pt` | no explicit redistribution license | **never** | external download only; not committed, not in Releases |
| Enikk `icon_detect` weights | unused | no | — |

> Correction (from txyy): OpenCV is **not** LGPL. It moved to Apache-2.0 in
> 4.5.2 (2021) and was 3-clause BSD before. The "LGPL" impression comes from
> optional third-party integrations (FFmpeg) that the default opencv-python
> wheels do not bundle. Static bundling is fine; just ship the NOTICE.

## Hard boundaries

1. **No AGPL**: the repo and the exe never import or depend on ultralytics.
   YOLO inference = onnxruntime + raw ONNX weights. Keep it that way — the
   training pipeline must also stay out of this repo (trainer scripts are the
   legally contested derivative, not the trained weights).
2. **Weights are data, external**: `*.pt` / `*.onnx` / `*.bin` are gitignored,
   never committed, never in Releases. Ship a one-command download script
   (`download-weights.sh` / first-run prompt) with explicit source links.
3. **License texts travel with the binary**: PyInstaller `--add-data
   "LICENSES/:**"` (MIT/Apache/BSD notices for every bundled component),
   plus a `licenses` about page in the CLI.
4. **MCP stays local-first**: loopback binding only, machine gate via config
   (see BINDINGS M2).

## TODO (verify before first public release)

- [ ] rapidocr ONNX **weights** redistribution license: check the RapidAI
      model download pages / original PaddleOCR sources. The code is
      Apache-2.0; the converted ONNX weights are a separate question (do not
      assume the code license covers them).
- [ ] enikk: confirm upstream repo + that vendoring under MIT is complete
      (copyright lines preserved in vendor/enikk/LICENSE).
- [ ] openseadragon/other frontend assets in vendor/enikk (if any) — sweep
      for embedded notices.

## YOLO via onnxruntime (port notes, from txyy)

1. Preprocess must byte-match ultralytics letterbox: aspect-ratio keep +
   pad to stride-32 multiple (640 default), BGR→RGB, /255.
2. Postprocess is hand-written: output is `[1, 8400, 4+1+num_classes]` raw
   logits → sigmoid(objectness+class), decode xywh→xyxy, NMS (ultralytics
   NMS is Python-side, NOT in the ONNX graph).
3. Export opset ≥ 12 (ultralytics default); onnxruntime ≥ 1.9 (use 1.16+).
4. Fixed 640×640 input avoids dynamic-shape headaches.
5. Class order must match the exporter's `model.names`.
