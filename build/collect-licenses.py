"""Collect third-party license texts into build/LICENSES/ for the exe.

Run with the same Windows python that builds the exe:

    python build/collect-licenses.py

Copies each installed package's LICENSE/COPYING/NOTICE into build/LICENSES/
as <pkg>-<LICENSE|NOTICE> so the binary ships every bundled component's
license text (MIT/Apache/BSD duty — see LICENSING.md).
"""
from __future__ import annotations

import importlib.metadata as md
import shutil
import sys
from pathlib import Path

PKGS = [
    "opencv-python",       # Apache-2.0 (OpenCV core) — NOTICE matters
    "pillow",              # MIT-CMU
    "numpy",               # BSD-3
    "onnxruntime",         # MIT
    "rapidocr-onnxruntime",# Apache-2.0
    "mcp",                 # MIT
    "zstandard",           # BSD-3
    "pyinstaller",         # GPL-2.0-with-exception (build tool, listed for transparency)
]

CANDIDATES = ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING", "NOTICE", "NOTICE.txt"]


def main() -> int:
    out = Path(__file__).resolve().parent / "LICENSES"
    out.mkdir(parents=True, exist_ok=True)
    copied = 0
    for dist_name in PKGS:
        try:
            dist = md.distribution(dist_name)
        except md.PackageNotFoundError:
            print(f"  skip (not installed): {dist_name}")
            continue
        files = dist.files or []
        hits = [f for f in files if f.name.upper() in {c.upper() for c in CANDIDATES}]
        if not hits:
            print(f"  no license file found: {dist_name}")
            continue
        for f in hits:
            src = Path(dist.locate_file(f))
            if not src.exists():
                continue
            dst = out / f"{dist_name.replace('-', '_')}-{f.name}"
            shutil.copy2(src, dst)
            copied += 1
            print(f"  {dst.name} <- {src}")
    # cu-dsh's own license + LICENSING.md travel too
    root = Path(__file__).resolve().parent.parent
    shutil.copy2(root / "LICENSE", out / "cu_dsh-LICENSE")
    shutil.copy2(root / "LICENSING.md", out / "cu_dsh-LICENSING.md")
    print(f"done: {copied} license files in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
