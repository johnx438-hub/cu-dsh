"""Regression: act.load_frame must never escape the shot dir (path traversal).

cf. 8d21bc5 — stamp regex anchor + json_path resolve/prefix check.
Runs anywhere: pure pathlib, no cv2/PIL/Windows needed.
"""
from __future__ import annotations

import json

import pytest

from cu_dsh import act


@pytest.fixture
def shot_dir(tmp_path, monkeypatch):
    """Point act.DEFAULT_OUT at a temp shot dir with one frame on disk."""
    monkeypatch.setattr(act, "DEFAULT_OUT", tmp_path)
    (tmp_path / "0e6f367.json").write_text(
        json.dumps({"stamp": "0e6f367", "items": []}), encoding="utf-8"
    )
    return tmp_path


def test_stamp_normal(shot_dir):
    frame, path = act.load_frame(stamp="0e6f367")
    assert frame["stamp"] == "0e6f367"
    assert path.name == "0e6f367.json"


def test_stamp_dotdot_rejected(shot_dir):
    # `/` and `\` are not in the stamp charset: any path separator is refused.
    for bad in ("../secret", "a/../b", "..%2f..%2fetc", "..\\secret", "sub/0e6f367"):
        with pytest.raises(ValueError):
            act.load_frame(stamp=bad)


def test_stamp_bare_dotdot_is_harmless(shot_dir):
    # `..` alone becomes the literal filename `...json` *inside* the shot dir
    # (no separator, no traversal) — it merely does not exist.
    with pytest.raises(FileNotFoundError):
        act.load_frame(stamp="..")


def test_stamp_absolute_rejected(shot_dir, tmp_path):
    outside = tmp_path / ".." / "outside.json"
    with pytest.raises(ValueError):
        act.load_frame(stamp=str(outside))


def test_stamp_oversize_rejected(shot_dir):
    with pytest.raises(ValueError):
        act.load_frame(stamp="a" * 81)


def test_json_path_inside_ok(shot_dir):
    frame, path = act.load_frame(json_path=str(shot_dir / "0e6f367.json"))
    assert frame["stamp"] == "0e6f367"


def test_json_path_escape_rejected(shot_dir, tmp_path):
    outside = tmp_path.parent / "secret.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        act.load_frame(json_path=str(outside))
    # encoded ../ must not resolve to the real file either
    with pytest.raises(ValueError):
        act.load_frame(json_path=str(shot_dir / ".." / ".." / "secret.json"))


def test_json_path_symlink_escape_rejected(shot_dir, tmp_path):
    """resolve() follows symlinks: a link inside shot dir pointing out must fail."""
    outside = tmp_path.parent / "secret.json"
    outside.write_text("{}", encoding="utf-8")
    link = shot_dir / "link.json"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform")
    with pytest.raises(ValueError):
        act.load_frame(json_path=str(link))
