# Weights (not in git)

All model weights are downloaded separately — never committed and never
shipped inside the binary. `*.pt`, `*.onnx`, `*.onnx.bad`, `*.bin` are
gitignored; the repo only documents the layout.

## Layout

```
weights/                        # cu-dsh working weights (this repo)
  rapidocr/                     # RapidOCR ONNX (det/rec/cls) — staged for
                                #   OCR-on via the Enikk UIParser
  screenparser/best.pt          # optional ScreenParser YOLO11-L (--yolo only)
  icon_detect/                  # leftover / quarantined Enikk icon detector (not used)

vendor/enikk/weights/           # weights consumed by the vendored Enikk engine
  rapidocr/                     # RapidOCR ONNX used by the UIParser
  icon_detect/                  # Enikk icon detector (not used by cu-dsh)
```

Since M1 the Enikk OCR engine ships vendored at `vendor/enikk/` (MIT);
its own weights stay out of git (see `vendor/enikk/weights/` on disk).

## License notes (re-distribution)

- **RapidOCR ONNX** — Apache-2.0. Fine to redistribute with the engine.
- **ScreenParser `best.pt`** — no explicit redistribution license. Never
  bundle it: download separately, and do not commit it. The YOLO extra stays
  optional (`--yolo`).
- **Enikk `icon_detect`** — not used by cu-dsh; ignore.

## Download

See `vendor/enikk/README` for the engine's own instructions; RapidOCR ONNX
files are published by the RapidOCR project, and `best.pt` by the
ScreenParser project.
