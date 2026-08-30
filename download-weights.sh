#!/usr/bin/env bash
# Download cu-dsh model weights (never shipped in the binary — see
# LICENSING.md). Weights are data: RapidOCR ONNX is Apache-2.0 (PaddleOCR
# converted), ScreenParser best.pt has no explicit redistribution license so
# it is fetched from its upstream project and never bundled.
#
# Usage:  ./download-weights.sh [--screenparser] [--rapidocr] [--dry-run]   (default: all)
#   --dry-run: list which weights would be downloaded, without downloading.
# Run from the repo root (or set CU_ROOT).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEIGHTS="$ROOT/weights"
ENIKK_WEIGHTS="$ROOT/vendor/enikk/weights"

# RapidOCR ONNX (Apache-2.0) — ch_PP-OCRv4 det/rec/cls used by the Enikk
# UIParser. Mirrored on HF (PaddleOCR converted to ONNX).
RAPIDOCR_BASE="${CU_RAPIDOCR_BASE:-https://huggingface.co/Kiuyha/paddleocr-onnx/resolve/main}"
RAPIDOCR_FILES=(
  "ch_PP-OCRv4_det_infer.onnx"
  "ch_PP-OCRv4_rec_infer.onnx"
  "ch_ppocr_mobile_v2.0_cls_infer.onnx"
)

# ScreenParser YOLO11-L best.pt — upstream project only, never bundled.
SCREENPARSER_URL="${CU_SCREENPARSER_URL:-https://huggingface.co/ShilinW/screenparser/resolve/main/weights/best.pt}"

dl() { # dl <url> <dest>
  local url="$1" dest="$2"
  if [[ -f "$dest" && -s "$dest" ]]; then
    echo "  already present: $dest"
    return 0
  fi
  if [[ "$dry_run" == 1 ]]; then
    echo "  would download: $dest"
    return 0
  fi
  echo "  downloading $dest"
  mkdir -p "$(dirname "$dest")"
  if command -v curl >/dev/null 2>&1; then
    curl -fL --retry 3 -o "$dest" "$url"
  else
    wget -O "$dest" "$url"
  fi
}

want_rapidocr=1 want_screenparser=1 dry_run=0
for arg in "$@"; do
  case "$arg" in
    --rapidocr) want_screenparser=0 ;;
    --screenparser) want_rapidocr=0 ;;
    --dry-run) dry_run=1 ;;
  esac
done

if [[ "$want_rapidocr" == 1 ]]; then
  echo "== RapidOCR ONNX (Apache-2.0) =="
  for f in "${RAPIDOCR_FILES[@]}"; do
    dl "$RAPIDOCR_BASE/$f" "$ENIKK_WEIGHTS/rapidocr/$f"
    # core.py stages RapidOCR onnx under <CU_ROOT>/weights too
    dl "$RAPIDOCR_BASE/$f" "$WEIGHTS/rapidocr/$f"
  done
fi

if [[ "$want_screenparser" == 1 ]]; then
  echo "== ScreenParser best.pt (external, not bundled) =="
  dl "$SCREENPARSER_URL" "$WEIGHTS/screenparser/best.pt"
fi

if [[ "$dry_run" == 1 ]]; then
  echo "done. (dry-run: no files were downloaded)"
else
  echo "done. See weights/README.md for layout + license notes."
fi
