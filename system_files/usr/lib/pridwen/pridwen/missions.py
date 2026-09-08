"""Missions: load them, run their checks, derive node and track state.

A check runs through an Executor: HostExecutor (below) runs it as the learner,
in their session, and is the only executor before M4. `range/targets.py` adds
ContainerExecutor and VMExecutor, which retarget the same CHECK_TYPES at a
Range target instead of the host (see docs/range.md, "Where a check runs").
A host check with `sudo: true` runs through pkexec and only when the caller
passes allow_sudo=True (Academy asks first); a non-host executor is already
root inside the target, so `sudo` is a no-op there. Every check returns
(ok, message), and any regex a check declares is always matched in Python on
the value an executor returned, never shipped to grep or run on the target.
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
    # Range-only (docs/range.md, "Range-only check types"): need a second target or a
    # network to be meaningful, so they are refused with HOST_ONLY_TYPES's message
    # when run on the host executor.
    "port_listening", "port_reachable", "port_refused", "http_status", "pkg_installed",
    "audit_has",
}

# Meaningful only on the host: refused on a Range target (docs/range.md, "Where a check
# runs" — a Rocky container has no bootc deployment and no learner shell).
HOST_ONLY_TYPES = {"bootc_rollback", "env_shell"}

# Meaningful only on a Range target: refused on the host (no second target, no network).
RANGE_ONLY_TYPES = {
    "port_listening", "port_reachable", "port_refused", "http_status", "pkg_installed",
    "audit_has",
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
        # Range (docs/range.md, "Chairs"): a mission may verify more than the one node
        # named by `node` (its own node is always first), and may stay locked behind
        # another mission's result instead of only the tree's node-level `requires`.
        self.nodes = [self.node] + [n for n in (d.get("also_verifies") or []) if n != self.node]
        self.after = d.get("after")


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
        return [m for m in self.missions.values() if node in m.nodes]


# ---- checks -----------------------------------------------------------------

def _path(c, key="path"):
    return os.path.expanduser(fill(str(c.get(key, ""))))


def _argv(cmd):
    if isinstance(cmd, list):
        return [fill(str(x)) for x in cmd]
    return shlex.split(fill(str(cmd)))


class HostExecutor:
    """Runs a check as the learner, in their session. The only executor before M4.
    `range/targets.py` adds ContainerExecutor (`podman exec`) and VMExecutor (`ssh`),
    which duck-type this same `.run()` and are otherwise unknown to this module."""

    name = "host"

    def run(self, argv, sudo=False, timeout=20):
        if sudo:
            argv = ["pkexec", *argv]
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
            return r.returncode, r.stdout, r.stderr
        except FileNotFoundError:
            return 127, "", f"{argv[0]}: not found"
        except subprocess.TimeoutExpired:
            return 124, "", "timed out"


HOST = HostExecutor()


def run_check(c, allow_sudo=False, executor=HOST):
    """-> (ok: bool, message: str). Messages use the check's `fail` when it fails.

    `executor` decides where the check looks: `HOST` (default) is this machine, as
    the learner; anything else is a Range target, and is already root inside it, so
    `sudo` on the check is a no-op there. The regex on `path_contains`/`cmd_output`/
    `journal_has`/`audit_has` is always matched here in Python, never on the target.
    """
    t = c.get("type")
    sudo = bool(c.get("sudo", False))
    if sudo and not allow_sudo and executor is HOST:
        return False, "This check needs administrator rights; press Check again and confirm."
    if executor is HOST and t in RANGE_ONLY_TYPES:
        return False, f"Check type {t!r} needs a Range target or network; it has no meaning on the host."
    if executor is not HOST and t in HOST_ONLY_TYPES:
        return False, f"Check type {t!r} is host-only: a Range target has no bootc deployment or learner shell."
    actual = ""
    ok = False
    try:
        if t == "path_exists":
            if executor is HOST:
                ok = os.path.lexists(_path(c))
            else:
                rc, _, _ = executor.run(["test", "-e", "--", fill(str(c.get("path", "")))])
                ok = rc == 0
        elif t == "path_missing":
            if executor is HOST:
                ok = not os.path.lexists(_path(c))
            else:
                rc, _, _ = executor.run(["test", "-e", "--", fill(str(c.get("path", "")))])
                ok = rc != 0
        elif t == "path_type":
            kind = c.get("kind", "file")
            if executor is HOST:
                p = _path(c)
                ok = {"file": os.path.isfile, "dir": os.path.isdir, "symlink": os.path.islink}.get(kind, os.path.exists)(p)
                actual = "missing" if not os.path.lexists(p) else ("dir" if os.path.isdir(p) else "symlink" if os.path.islink(p) else "file")
            else:
                rc, out, _ = executor.run(["stat", "-c", "%F", "--", fill(str(c.get("path", "")))])
                word = {"file": "regular file", "dir": "directory", "symlink": "symbolic link"}.get(kind, kind)
                actual = "missing" if rc != 0 else out.strip()
                ok = actual == word
        elif t == "path_mode":
            if executor is HOST:
                p = _path(c)
                if os.path.lexists(p):
                    actual = f"{stat.S_IMODE(os.stat(p).st_mode):04o}"
                else:
                    actual = "missing"
            else:
                rc, out, _ = executor.run(["stat", "-c", "%a", "--", fill(str(c.get("path", "")))])
                actual = "missing" if rc != 0 else out.strip()
            ok = actual != "missing" and int(actual, 8) == int(str(c.get("mode", "0")), 8)
        elif t == "path_owner":
            if executor is HOST:
                import grp
                import pwd
                p = _path(c)
                if os.path.lexists(p):
                    st = os.stat(p)
                    actual = f"{pwd.getpwuid(st.st_uid).pw_name}:{grp.getgrgid(st.st_gid).gr_name}"
                else:
                    actual = "missing"
            else:
                rc, out, _ = executor.run(["stat", "-c", "%U:%G", "--", fill(str(c.get("path", "")))])
                actual = "missing" if rc != 0 else out.strip()
            if actual != "missing":
                owner, _, group = actual.partition(":")
                ok = owner == fill(str(c.get("owner", ""))) and (not c.get("group") or group == fill(str(c["group"])))
        elif t == "path_contains":
            if executor is HOST:
                p = _path(c)
                if os.path.isfile(p):
                    with open(p, encoding="utf-8", errors="replace") as f:
                        data = f.read()
                    actual = f"{len(data)} bytes"
                else:
                    data, actual = "", "missing"
            else:
                rc, out, _ = executor.run(["head", "-c", "1048576", "--", fill(str(c.get("path", "")))])
                data = out if rc == 0 else ""
                actual = "missing" if rc != 0 else f"{len(data)} bytes"
            if actual != "missing":
                ok = re.search(fill(str(c.get("regex", ""))), data, re.M) is not None
        elif t == "cmd_exit":
            rc, out, err = executor.run(_argv(c.get("cmd", [])), sudo)
            actual = str(rc)
            ok = rc == int(c.get("exit", 0))
        elif t == "cmd_output":
            rc, out, err = executor.run(_argv(c.get("cmd", [])), sudo)
            ok = re.search(fill(str(c.get("regex", ""))), out, re.M) is not None
            actual = (out.strip().splitlines() or [err.strip() or f"exit {rc}"])[0][:120]
        elif t in ("unit_active", "unit_inactive", "unit_enabled"):
            scope = ["--user"] if c.get("scope") == "user" else []
            verb = "is-enabled" if t == "unit_enabled" else "is-active"
            rc, out, _ = executor.run(["systemctl", *scope, verb, "--", fill(str(c.get("unit", "")))])
            actual = out.strip() or f"exit {rc}"
            if t == "unit_active":
                ok = actual == "active"
            elif t == "unit_inactive":
                ok = actual != "active"
            else:
                ok = actual in ("enabled", "enabled-runtime", "static", "alias")
        elif t == "user_exists":
            rc, out, _ = executor.run(["getent", "passwd", fill(str(c.get("user", "")))])
            ok = rc == 0
        elif t == "group_member":
            rc, out, _ = executor.run(["id", "-nG", fill(str(c.get("user", "{user}")))])
            groups = out.split()
            actual = " ".join(groups)
            ok = fill(str(c.get("group", ""))) in groups
        elif t == "sysctl":
            key = str(c.get("key", "")).replace(".", "/")
            if executor is HOST:
                with open(f"/proc/sys/{key}", encoding="utf-8") as f:
                    actual = f.read().strip()
            else:
                rc, out, _ = executor.run(["cat", f"/proc/sys/{key}"])
                actual = out.strip() if rc == 0 else "missing"
            ok = actual == str(c.get("value", ""))
        elif t == "selinux":
            rc, out, _ = executor.run(["getenforce"])
            actual = out.strip()
            ok = actual.lower() == str(c.get("mode", "enforcing")).lower()
        elif t == "firewalld_zone":
            rc, out, _ = executor.run(["firewall-cmd", "--get-default-zone"])
            actual = out.strip() or f"exit {rc}"
            ok = actual == str(c.get("zone", ""))
        elif t == "bootc_rollback":
            rc, out, _ = executor.run(["bootc", "status", "--json"])
            import json
            try:
                ok = bool(((json.loads(out).get("status") or {}).get("rollback")))
            except ValueError:
                ok = False
            actual = "present" if ok else "none"
        elif t == "pkg_installed":
            rc, out, _ = executor.run(["rpm", "-q", fill(str(c.get("pkg", "")))])
            actual = out.strip() or f"exit {rc}"
            ok = rc == 0
        elif t == "port_listening":
            proto_flag = "-u" if c.get("proto") == "udp" else "-t"
            rc, out, _ = executor.run(["ss", "-lnH", proto_flag])
            port = str(c.get("port", ""))
            ok = re.search(rf":{re.escape(port)}\b", out) is not None
            actual = "not listening" if not ok else f"listening :{port}"
        elif t in ("port_reachable", "port_refused"):
            to = fill(str(c.get("to", "")))
            port = str(c.get("port", ""))
            probe = f"exec 3<>/dev/tcp/{to}/{port}"
            rc, _, err = executor.run(["timeout", "3", "bash", "-c", probe])
            reached = rc == 0
            actual = "reachable" if reached else (err.strip().splitlines() or [f"exit {rc}"])[0][:120]
            ok = reached if t == "port_reachable" else not reached
        elif t == "http_status":
            url = fill(str(c.get("url", "")))
            rc, out, _ = executor.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "5", url])
            actual = out.strip() or f"exit {rc}"
            ok = actual == str(c.get("status", "200"))
        elif t == "audit_has":
            rc, out, _ = executor.run(["ausearch", "-i", "-ts", str(c.get("since", "-1h"))])
            ok = rc == 0 and re.search(fill(str(c.get("regex", ""))), out, re.M) is not None
            actual = f"{len(out.splitlines())} lines" if rc == 0 else "no matching audit events"
        elif t == "journal_has":
            argv = ["journalctl", "-q", "--no-pager", "-o", "cat"]
            if c.get("scope", "user") == "user":
                argv.append("--user")
            if c.get("unit"):
                argv += ["-u", fill(str(c["unit"]))]
            argv.append(f"--since={c.get('since', '-1h')}")
            rc, out, _ = executor.run(argv, sudo)
            ok = re.search(fill(str(c.get("regex", ""))), out, re.M) is not None
            actual = f"{len(out.splitlines())} lines"
        elif t == "env_shell":
            actual = os.environ.get("SHELL", "")
            ok = re.search(fill(str(c.get("regex", ""))), actual) is not None
        else:
            return False, f"Unknown check type {t!r}."
    except (OSError, ValueError, KeyError) as e:
        return False, f"Check could not run: {e}"
    if c.get("expect") == "absent":
        ok = not ok
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
        after = self.cat.missions[mid].after
        if after and self.mission_state(after) != "verified":
            return "locked"
        row = self.store.mission(mid)
        if row is None:
            return "available"
        if row["verified_ts"]:
            return "verified"
        return "in-progress" if row["attempts"] else "available"

    def run_checks(self, mid, allow_sudo=False):
        """Run the checks only (safe from a worker thread: touches no store)."""
        m = self.cat.missions[mid]
        return [(c.get("id", f"check{i}"), *run_check(c, allow_sudo)) for i, c in enumerate(m.checks)]

    def record(self, mid, results):
        """Record an attempt (main thread: uses the store)."""
        m = self.cat.missions[mid]
        passed = all(ok for _, ok, _ in results)
        self.store.mission_attempt(mid, passed)
        summary = "verified" if passed else "; ".join(msg for _, ok, msg in results if not ok)[:300]
        self.store.journal("mission", mid, summary, m.node)
        return passed

    def check(self, mid, allow_sudo=False):
        results = self.run_checks(mid, allow_sudo)
        return self.record(mid, results), results

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
        # A mission "locked" behind another mission's `after` reads as untouched here,
        # the same as "available": the learner hasn't earned the chance to attempt it
        # yet, which is not the same as having started and stalled (docs/range.md).
        if any(s not in ("available", "locked") for s in states.values()):
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
