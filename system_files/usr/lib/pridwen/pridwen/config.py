"""User settings: ~/.config/pridwen/coach.toml (a flat key = value file).

Keys: enabled (bool), dispatch (bool), quiet_until (epoch seconds; 0 = not
quiet; -1 = forever), quiet_hours ("22:00-08:00" or ""), daily_cap (int).
"""
import os
import time

from . import config_dir

DEFAULTS = {"enabled": True, "dispatch": True, "quiet_until": 0, "quiet_hours": "22:00-08:00", "daily_cap": 3}


def path():
    return os.path.join(config_dir(), "coach.toml")


def _parse(v):
    v = v.strip()
    if v in ("true", "false"):
        return v == "true"
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    try:
        return int(v)
    except ValueError:
        return v


def load():
    cfg = dict(DEFAULTS)
    try:
        with open(path(), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = _parse(v)
    except OSError:
        pass
    return cfg


def save(cfg):
    os.makedirs(config_dir(), exist_ok=True)
    lines = ["# Pridwen Coach settings. `pridwen quiet` and `pridwen status` manage these."]
    for k, v in cfg.items():
        if isinstance(v, bool):
            s = "true" if v else "false"
        elif isinstance(v, int):
            s = str(v)
        else:
            s = f'"{v}"'
        lines.append(f"{k} = {s}")
    tmp = path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, path())


def quiet_state(cfg=None, now=None):
    """Returns (is_quiet, reason)."""
    cfg = cfg or load()
    now = now or time.time()
    if not cfg.get("enabled", True):
        return True, "disabled"
    qu = int(cfg.get("quiet_until", 0) or 0)
    if qu == -1:
        return True, "forever"
    if qu > now:
        left = int(qu - now)
        if left >= 3600:
            return True, f"{left // 3600}h {left % 3600 // 60}m left"
        return True, f"{max(1, left // 60)}m left"
    return False, ""


def in_quiet_hours(cfg=None, now=None):
    cfg = cfg or load()
    spec = str(cfg.get("quiet_hours", "") or "")
    if "-" not in spec:
        return False
    try:
        a, b = spec.split("-", 1)
        ah, am = (int(x) for x in a.split(":"))
        bh, bm = (int(x) for x in b.split(":"))
    except ValueError:
        return False
    t = time.localtime(now or time.time())
    cur = t.tm_hour * 60 + t.tm_min
    start, end = ah * 60 + am, bh * 60 + bm
    if start <= end:
        return start <= cur < end
    return cur >= start or cur < end
