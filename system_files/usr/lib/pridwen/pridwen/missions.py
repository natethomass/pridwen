"""Missions: load them, run their checks on the host, derive node and track state.

Checks run as the learner, in their session. A check with `sudo: true` runs
through pkexec and only when the caller passes allow_sudo=True (Academy asks
first). Every check returns (ok, message).
"""
import glob
import os
import re
import shlex
import stat
import subprocess
import time

import yaml

from . import SHARE
from .rules import fill

CHECK_TYPES = {
    "path_exists", "path_missing", "path_mode", "path_owner", "path_contains", "path_type",
    "cmd_exit", "cmd_output", "unit_active", "unit_enabled", "unit_inactive",
    "user_exists", "group_member", "sysctl", "selinux", "firewalld_zone", "bootc_rollback",
    "journal_has", "env_shell",
}


def _yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class Mission:
    def __init__(self, d, source):
        self.d = d
        self.source = source
        self.id = d["id"]
        self.node = d.get("node", "")
        self.title = d.get("title", self.id)
        self.track = d.get("track", "")
        self.required = bool(d.get("required", True))
        self.minutes = int(d.get("minutes", 10))
        self.target = d.get("target", "host")
        self.brief = d.get("brief", "")
        self.steps = list(d.get("steps") or [])
        self.hints = list(d.get("hints") or [])
        self.checks = list(d.get("checks") or [])
        self.cleanup = d.get("cleanup")
        self.setup = d.get("setup")


class Track:
    def __init__(self, d, source):
        self.d = d
        self.id = d["id"]
        self.title = d.get("title", self.id)
        self.lede = d.get("lede", "")
        self.maps_to = d.get("maps_to", "")
        self.nodes = list(d.get("nodes") or [])
        self.missions = list(d.get("missions") or [])
        self.capstone = d.get("capstone")


class Catalog:
    def __init__(self, share=SHARE):
        self.share = share
        self.missions = {}
        self.tracks = {}
        self.errors = []
        for p in sorted(glob.glob(os.path.join(share, "missions", "*.yaml"))):
            try:
                m = Mission(_yaml(p), p)
                self.missions[m.id] = m
            except (KeyError, TypeError, yaml.YAMLError, OSError) as e:
                self.errors.append(f"{p}: {e}")
        for p in sorted(glob.glob(os.path.join(share, "tracks", "*.yaml"))):
            try:
                t = Track(_yaml(p), p)
                self.tracks[t.id] = t
            except (KeyError, TypeError, yaml.YAMLError, OSError) as e:
                self.errors.append(f"{p}: {e}")

    def for_node(self, node):
        return [m for m in self.missions.values() if m.node == node]


# ---- checks -----------------------------------------------------------------

def _path(c, key="path"):
    return os.path.expanduser(fill(str(c.get(key, ""))))


def _argv(cmd):
    if isinstance(cmd, list):
        return [fill(str(x)) for x in cmd]
    return shlex.split(fill(str(cmd)))


def _run(argv, sudo=False, timeout=20):
    if sudo:
        argv = ["pkexec", *argv]
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return 127, "", f"{argv[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"


def run_check(c, allow_sudo=False):
    """-> (ok: bool, message: str). Messages use the check's `fail` when it fails."""
    t = c.get("type")
    sudo = bool(c.get("sudo", False))
    if sudo and not allow_sudo:
        return False, "This check needs administrator rights; press Check again and confirm."
    actual = ""
    ok = False
    try:
        if t == "path_exists":
            ok = os.path.lexists(_path(c))
        elif t == "path_missing":
            ok = not os.path.lexists(_path(c))
        elif t == "path_type":
            p = _path(c)
            kind = c.get("kind", "file")
            ok = {"file": os.path.isfile, "dir": os.path.isdir, "symlink": os.path.islink}.get(kind, os.path.exists)(p)
            actual = "missing" if not os.path.lexists(p) else ("dir" if os.path.isdir(p) else "symlink" if os.path.islink(p) else "file")
        elif t == "path_mode":
            p = _path(c)
            if os.path.lexists(p):
                actual = f"{stat.S_IMODE(os.stat(p).st_mode):04o}"
                ok = int(actual, 8) == int(str(c.get("mode", "0")), 8)
            else:
                actual = "missing"
        elif t == "path_owner":
            import grp
            import pwd
            p = _path(c)
            if os.path.lexists(p):
                st = os.stat(p)
                owner = pwd.getpwuid(st.st_uid).pw_name
                group = grp.getgrgid(st.st_gid).gr_name
                actual = f"{owner}:{group}"
                ok = owner == fill(str(c.get("owner", ""))) and (not c.get("group") or group == fill(str(c["group"])))
            else:
                actual = "missing"
        elif t == "path_contains":
            p = _path(c)
            if os.path.isfile(p):
                with open(p, encoding="utf-8", errors="replace") as f:
                    data = f.read()
                ok = re.search(fill(str(c.get("regex", ""))), data, re.M) is not None
                actual = f"{len(data)} bytes"
            else:
                actual = "missing"
        elif t == "cmd_exit":
            rc, out, err = _run(_argv(c.get("cmd", [])), sudo)
            actual = str(rc)
            ok = rc == int(c.get("exit", 0))
        elif t == "cmd_output":
            rc, out, err = _run(_argv(c.get("cmd", [])), sudo)
            ok = re.search(fill(str(c.get("regex", ""))), out, re.M) is not None
            actual = (out.strip().splitlines() or [err.strip() or f"exit {rc}"])[0][:120]
        elif t in ("unit_active", "unit_inactive", "unit_enabled"):
            scope = ["--user"] if c.get("scope") == "user" else []
            verb = "is-enabled" if t == "unit_enabled" else "is-active"
            rc, out, _ = _run(["systemctl", *scope, verb, "--", fill(str(c.get("unit", "")))])
            actual = out.strip() or f"exit {rc}"
            if t == "unit_active":
                ok = actual == "active"
            elif t == "unit_inactive":
                ok = actual != "active"
            else:
                ok = actual in ("enabled", "enabled-runtime", "static", "alias")
        elif t == "user_exists":
            rc, out, _ = _run(["getent", "passwd", fill(str(c.get("user", "")))])
            ok = rc == 0
        elif t == "group_member":
            rc, out, _ = _run(["id", "-nG", fill(str(c.get("user", "{user}")))])
            groups = out.split()
            actual = " ".join(groups)
            ok = fill(str(c.get("group", ""))) in groups
        elif t == "sysctl":
            key = str(c.get("key", "")).replace(".", "/")
            with open(f"/proc/sys/{key}", encoding="utf-8") as f:
                actual = f.read().strip()
            ok = actual == str(c.get("value", ""))
        elif t == "selinux":
            rc, out, _ = _run(["getenforce"])
            actual = out.strip()
            ok = actual.lower() == str(c.get("mode", "enforcing")).lower()
        elif t == "firewalld_zone":
            rc, out, _ = _run(["firewall-cmd", "--get-default-zone"])
            actual = out.strip() or f"exit {rc}"
            ok = actual == str(c.get("zone", ""))
        elif t == "bootc_rollback":
            rc, out, _ = _run(["bootc", "status", "--json"])
            import json
            try:
                ok = bool(((json.loads(out).get("status") or {}).get("rollback")))
            except ValueError:
                ok = False
            actual = "present" if ok else "none"
        elif t == "journal_has":
            argv = ["journalctl", "-q", "--no-pager", "-o", "cat"]
            if c.get("scope", "user") == "user":
                argv.append("--user")
            if c.get("unit"):
                argv += ["-u", fill(str(c["unit"]))]
            argv.append(f"--since={c.get('since', '-1h')}")
            rc, out, _ = _run(argv, sudo)
            ok = re.search(fill(str(c.get("regex", ""))), out, re.M) is not None
            actual = f"{len(out.splitlines())} lines"
        elif t == "env_shell":
            actual = os.environ.get("SHELL", "")
            ok = re.search(fill(str(c.get("regex", ""))), actual) is not None
        else:
            return False, f"Unknown check type {t!r}."
    except (OSError, ValueError, KeyError) as e:
        return False, f"Check could not run: {e}"
    if ok:
        return True, c.get("pass", "OK")
    msg = fill(str(c.get("fail", "Not yet.")))
    return False, msg.replace("{actual}", actual or "unknown")


def run_shell(script):
    """Run a mission's setup/cleanup script in the learner's shell."""
    if not script:
        return 0, ""
    r = subprocess.run(["bash", "-c", fill(script)], capture_output=True, text=True, timeout=60)
    return r.returncode, (r.stdout + r.stderr).strip()


# ---- progress ---------------------------------------------------------------

class Progress:
    """Mission results and node states on top of the Store."""

    def __init__(self, store, library, catalog):
        self.store = store
        self.lib = library
        self.cat = catalog

    def mission_state(self, mid):
        row = self.store.mission(mid)
        if row is None:
            return "available"
        if row["verified_ts"]:
            return "verified"
        return "in-progress" if row["attempts"] else "available"

    def check(self, mid, allow_sudo=False):
        m = self.cat.missions[mid]
        results = [(c.get("id", f"check{i}"), *run_check(c, allow_sudo)) for i, c in enumerate(m.checks)]
        passed = all(ok for _, ok, _ in results)
        self.store.mission_attempt(mid, passed)
        summary = "verified" if passed else "; ".join(msg for _, ok, msg in results if not ok)[:300]
        self.store.journal("mission", mid, summary, m.node)
        return passed, results

    def node_state(self, nid):
        node = self.lib.node(nid)
        for req in node.get("requires") or []:
            if self.node_state(req) != "verified":
                return "locked"
        missions = self.cat.for_node(nid)
        states = {m.id: self.mission_state(m.id) for m in missions}
        required = [m for m in missions if m.required]
        if required and all(states[m.id] == "verified" for m in required):
            return "verified"
        if missions and not required and any(s == "verified" for s in states.values()):
            return "verified"
        if any(s != "available" for s in states.values()):
            return "in-progress"
        if self.store.node_touched(nid):
            return "in-progress"
        return "available"

    def track_progress(self, tid):
        t = self.cat.tracks[tid]
        states = {n: self.node_state(n) for n in t.nodes}
        done = sum(1 for s in states.values() if s == "verified")
        next_mission = next((mid for mid in t.missions if self.mission_state(mid) != "verified"), None)
        return {"nodes": states, "verified": done, "total": len(t.nodes), "next": next_mission,
                "missions": {mid: self.mission_state(mid) for mid in t.missions}}
