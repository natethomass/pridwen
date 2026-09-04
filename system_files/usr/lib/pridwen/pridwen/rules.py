"""Rules engine: load the tree, the Coach rules, and the nudges; match events.

Rules never see command output. Probes look at the system instead (is the
path unreadable, is the unit missing, is this an image-based host) so a hint
is right for the reason the command failed, not just its exit code.
"""
import glob
import os
import re
import shutil
import subprocess
import sys

import yaml

from . import SHARE

SUDO_RE = re.compile(r"^\s*(?:sudo|doas)(?:\s+-\S+)*\s+")
FIRST_WORD_RE = re.compile(r"^\s*(?:sudo|doas)?(?:\s+-\S+)*\s*(\S+)")

# Things that must never be stored. Applied to the command line before anything else.
SCRUB = [
    (re.compile(r"(?i)((?:password|passwd|pass|pwd|secret|token|api[_-]?key|key)\s*[=:]\s*)\S+"), r"\1<redacted>"),
    (re.compile(r"(?i)(-p|--password[= ]|--token[= ]|--api-key[= ])\s*\S+"), r"\1<redacted>"),
    (re.compile(r"(?i)(authorization:\s*(?:bearer|basic)?\s*)\S+"), r"\1<redacted>"),
    (re.compile(r"\b[A-Za-z0-9+/_-]{40,}={0,2}\b"), "<redacted>"),
    (re.compile(r"\b[0-9a-fA-F]{32,}\b"), "<redacted>"),
]


def scrub(cmd):
    for rx, rep in SCRUB:
        cmd = rx.sub(rep, cmd)
    return cmd


def first_word(cmd):
    m = FIRST_WORD_RE.match(cmd)
    return os.path.basename(m.group(1)) if m else ""


def under_sudo(cmd):
    return bool(SUDO_RE.match(cmd))


# ---- probes -----------------------------------------------------------------

def _expand(path, cwd):
    path = os.path.expanduser(path)
    if not os.path.isabs(path) and cwd:
        path = os.path.join(cwd, path)
    return path


def probe(spec, groups, cwd=None, cache=None):
    """Evaluate one probe spec like 'unreadable:{path}' or 'not ostree'."""
    spec = spec.strip()
    if spec.startswith("not "):
        return not probe(spec[4:], groups, cwd, cache)
    try:
        spec = spec.format(**groups)
    except (KeyError, IndexError, ValueError):
        return False
    name, _, arg = spec.partition(":")
    name = name.strip()
    arg = arg.strip()
    cache = cache if cache is not None else {}
    key = (name, arg)
    if key in cache:
        return cache[key]
    result = False
    try:
        if name in ("unreadable", "unwritable", "missing", "exists", "is_dir"):
            p = _expand(arg, cwd)
            if name == "missing":
                result = not os.path.lexists(p)
            elif name == "exists":
                result = os.path.lexists(p)
            elif name == "is_dir":
                result = os.path.isdir(p)
            elif name == "unreadable":
                result = os.path.exists(p) and not os.access(p, os.R_OK)
            elif name == "unwritable":
                result = os.path.exists(p) and not os.access(p, os.W_OK)
        elif name == "no_command":
            result = shutil.which(arg) is None
        elif name == "no_unit":
            unit = arg if "." in arg else arg + ".service"
            result = True
            for scope in ([], ["--user"]):
                r = subprocess.run(["systemctl", *scope, "cat", "--", unit], capture_output=True, timeout=2)
                if r.returncode == 0:
                    result = False
                    break
        elif name == "ostree":
            result = os.path.exists("/run/ostree-booted")
        elif name == "selinux_enforcing":
            try:
                with open("/sys/fs/selinux/enforce") as f:
                    result = f.read().strip() == "1"
            except OSError:
                result = False
        elif name == "in_container":
            result = os.path.exists("/run/.containerenv") or os.path.exists("/.dockerenv")
        elif name == "true":
            result = True
    except (OSError, subprocess.SubprocessError, ValueError):
        result = False
    cache[key] = result
    return result


# ---- rules ------------------------------------------------------------------

class Rule:
    __slots__ = ("id", "node", "lesson", "regex", "exit", "not_sudo", "probes", "hint", "why", "man", "cooldown", "priority", "source")

    def __init__(self, d, source, tree):
        self.id = d["id"]
        self.node = d.get("node", "")
        node = tree.get("nodes", {}).get(self.node, {})
        self.lesson = d.get("lesson") or (node.get("lessons") or [None])[0]
        when = d.get("when") or {}
        self.regex = re.compile(when.get("command", ""))
        ex = when.get("exit")
        if ex is None:
            self.exit = None            # any failure
        elif ex == "any":
            self.exit = "any"
        else:
            self.exit = {int(x) for x in (ex if isinstance(ex, list) else [ex])}
        self.not_sudo = bool(when.get("not_sudo", False))
        pr = when.get("probe") or []
        self.probes = [pr] if isinstance(pr, str) else list(pr)
        self.hint = " ".join(str(d.get("hint", "")).split())
        self.why = d.get("why")
        self.man = d.get("man") or []
        self.cooldown = int(d.get("cooldown", 3600))
        self.priority = int(d.get("priority", 0))
        self.source = source

    def matches(self, cmd, exit_code, cwd=None, cache=None):
        """Returns the regex groups dict on match, else None."""
        if self.exit is None:
            if exit_code == 0:
                return None
        elif self.exit != "any" and exit_code not in self.exit:
            return None
        if self.not_sudo and under_sudo(cmd):
            return None
        # Rules are written for the bare command; a leading sudo/doas is
        # stripped for matching (not_sudo tells the two cases apart).
        m = self.regex.search(cmd)
        if not m and under_sudo(cmd):
            m = self.regex.search(SUDO_RE.sub("", cmd, count=1))
        if not m:
            return None
        groups = {k: v for k, v in m.groupdict().items() if v is not None}
        groups.setdefault("cmd", first_word(cmd))
        for p in self.probes:
            if not probe(p, groups, cwd, cache):
                return None
        return groups


def fill(text, groups):
    try:
        return text.format(**groups)
    except (KeyError, IndexError, ValueError):
        return text


class Library:
    def __init__(self, share=SHARE):
        self.share = share
        self.tree = {"tiers": {}, "nodes": {}}
        self.rules = []
        self.nudges = []
        self.errors = []
        self.load()

    def _yaml(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except (OSError, yaml.YAMLError) as e:
            self.errors.append(f"{path}: {e}")
            return None

    def load(self):
        tree = self._yaml(os.path.join(self.share, "tree.yaml"))
        if isinstance(tree, dict):
            self.tree = tree
        for path in sorted(glob.glob(os.path.join(self.share, "rules", "*.yaml"))):
            data = self._yaml(path)
            if not isinstance(data, list):
                continue
            for d in data:
                try:
                    self.rules.append(Rule(d, os.path.basename(path), self.tree))
                except (KeyError, re.error, ValueError, TypeError) as e:
                    self.errors.append(f"{path}: rule {d.get('id') if isinstance(d, dict) else d!r}: {e}")
        # Highest priority first; ties keep file order.
        self.rules.sort(key=lambda r: -r.priority)
        nud = self._yaml(os.path.join(self.share, "nudges.yaml"))
        if isinstance(nud, list):
            for d in nud:
                try:
                    cnt = d.get("count") or {}
                    d["_regex"] = re.compile(cnt["command"]) if "command" in cnt else None
                    self.nudges.append(d)
                except (re.error, TypeError, AttributeError) as e:
                    self.errors.append(f"nudges.yaml: {d!r}: {e}")
        for e in self.errors:
            print(f"pridwen rules: {e}", file=sys.stderr)

    def match(self, cmd, exit_code, cwd=None, skip=None):
        """Best matching rule for an event, honouring `skip(rule)` (cooldowns)."""
        cache = {}
        for r in self.rules:
            if skip and skip(r):
                continue
            g = r.matches(cmd, exit_code, cwd, cache)
            if g is not None:
                return r, g
        return None, None

    def match_all(self, cmd, exit_code, cwd=None):
        cache = {}
        out = []
        for r in self.rules:
            g = r.matches(cmd, exit_code, cwd, cache)
            if g is not None:
                out.append((r, g))
        return out

    def node(self, nid):
        return self.tree.get("nodes", {}).get(nid, {})

    def lesson_node(self, lesson_id):
        for nid, n in self.tree.get("nodes", {}).items():
            if lesson_id in (n.get("lessons") or []):
                return nid
        return None

    def lesson_path(self, lesson_id):
        return os.path.join(self.share, "lessons", f"{lesson_id}.md")
