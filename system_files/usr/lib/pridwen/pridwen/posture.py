"""Posture: the hardening baseline as data, checked read-only (M3 panel; M6 owns it)."""
import os

import yaml

from . import SHARE
from .missions import run_check


def load(share=SHARE):
    path = os.path.join(share, "posture.yaml")
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
    except (OSError, yaml.YAMLError):
        return []
    return [c for c in data if isinstance(c, dict) and c.get("id")]


def evaluate(controls=None):
    """-> list of dicts: control fields plus ok (bool), actual/message, expected (bool: drift is known)."""
    out = []
    for c in controls if controls is not None else load():
        ok, msg = run_check(c.get("check") or {}, allow_sudo=False)
        out.append({**c, "ok": ok, "message": msg, "expected_drift": bool(c.get("note")) and not ok})
    return out
