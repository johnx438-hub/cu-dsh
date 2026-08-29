# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for cu-dsh.exe.

Pure-open-source binary (see LICENSING.md): cu_dsh + vendored enikk code +
runtime deps; NO model weights inside (downloaded separately), no AGPL.
Third-party license texts are bundled via build/LICENSES/ (collect-licenses.py).

Build (Windows python with pyinstaller installed):

    python build/collect-licenses.py
    pyinstaller --clean --noconfirm cu-dsh.spec
"""

import os

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

block_cipher = None

SPEC_DIR = SPECPATH if isinstance(SPECPATH, str) else str(SPECPATH)
ROOT = os.path.abspath(os.path.join(SPEC_DIR, '..'))
ENIKK_DIR = os.path.join(ROOT, 'vendor', 'enikk')

# ── onnxruntime CAPI DLLs (no torch/scipy/pyarrow) ──────────────────────
ort_binaries = collect_dynamic_libs('onnxruntime')

# ── enikk vendored package: python modules + static assets ──────────────
enikk_datas = [
    (os.path.join(ENIKK_DIR, 'enikk', 'static'), 'enikk/enikk/static'),
    (os.path.join(ENIKK_DIR, 'enikk', 'skills'), 'enikk/enikk/skills'),
    # LICENSE must ship with the code
    (os.path.join(ENIKK_DIR, 'LICENSE'), 'enikk/'),
]

# ── third-party license texts (MIT/Apache/BSD duty) ─────────────────────
licenses_datas = [
    (os.path.join(SPEC_DIR, 'LICENSES'), 'LICENSES'),
]

# ── rapidocr data (dicts/configs; weights stay external) ────────────────
try:
    from PyInstaller.utils.hooks import collect_data_files as _cdf
    rapidocr_datas = _cdf('rapidocr_onnxruntime')
except Exception:
    rapidocr_datas = []

hiddenimports = list(set(
    collect_submodules('cu_dsh')
    + collect_submodules('enikk')
    + ['mcp', 'mcp.server.fastmcp', 'PIL', 'cv2', 'onnxruntime']
))

a = Analysis(
    [os.path.join(SPEC_DIR, 'pyinstaller_entry.py')],
    pathex=[ROOT, ENIKK_DIR],
    binaries=ort_binaries,
    datas=enikk_datas + licenses_datas + rapidocr_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchvision', 'torchaudio', 'pyarrow',
        'onnxruntime.quantization', 'onnxruntime.transformers',
        'onnxruntime.tools', 'onnxruntime.datasets',
        'matplotlib', 'pandas', 'IPython', 'jupyter', 'notebook',
        'pytest', 'ruff', 'mypy', 'ultralytics',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cu-dsh',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,          # CLI tool: keep the console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cu-dsh',
)
