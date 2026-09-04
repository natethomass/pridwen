"""`pridwen explain`: annotate a command word and its flags.

Curated annotations live in /usr/share/pridwen/explain/<command>.yaml. When a
flag is not curated, the man page is searched for its option paragraph.
"""
import os
import re
import shlex
import subprocess

import yaml

from . import SHARE
from .rules import first_word, under_sudo

OPT_LINE = re.compile(r"^\s{2,12}(-{1,2}[A-Za-z0-9][\w-]*)(?:[,\s=\[][^\n]*)?$")


def load_curated(cmd):
    path = os.path.join(SHARE, "explain", f"{cmd}.yaml")
    try:
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
        return None
    flags = {}
    for k, v in (d.get("flags") or {}).items():
        for part in str(k).split(","):
            part = part.strip()
            if part:
                flags[part] = str(v)
    d["_flags"] = flags
    return d


def whatis(cmd):
    try:
        r = subprocess.run(["whatis", "--", cmd], capture_output=True, text=True, timeout=3)
        for line in r.stdout.splitlines():
            if " - " in line:
                return line.split(" - ", 1)[1].strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


_man_cache = {}


def man_options(cmd):
    """{flag: first sentence of its paragraph} parsed from the man page."""
    if cmd in _man_cache:
        return _man_cache[cmd]
    out = {}
    try:
        env = dict(os.environ, MANWIDTH="200", MAN_KEEP_FORMATTING="0", PAGER="cat", MANPAGER="cat")
        r = subprocess.run(["man", "--", cmd], capture_output=True, text=True, timeout=5, env=env)
        lines = re.sub(r".\x08", "", r.stdout).splitlines()
    except (OSError, subprocess.SubprocessError):
        lines = []
    i = 0
    while i < len(lines):
        m = OPT_LINE.match(lines[i])
        if m:
            # Collect every flag on the header line, then the description below.
            header = lines[i].strip()
            flags = re.findall(r"(?<![\w-])(-{1,2}[A-Za-z0-9][\w-]*)", header.split("  ")[0])
            j = i + 1
            desc = []
            while j < len(lines) and lines[j].strip() and not OPT_LINE.match(lines[j]):
                desc.append(lines[j].strip())
                j += 1
            if not desc and header.count("  ") >= 1:
                desc = [header.split("  ", 1)[1].strip()]
            sent = " ".join(desc)
            sent = re.split(r"(?<=[.;])\s", sent, 1)[0] if sent else ""
            for f in flags:
                out.setdefault(f, sent[:200])
            i = j
        else:
            i += 1
    _man_cache[cmd] = out
    return out


def split_flags(tokens):
    """['-la', '--color=auto'] -> [('-l', None), ('-a', None), ('--color', 'auto')]"""
    out = []
    for t in tokens:
        if t.startswith("--"):
            name, _, val = t.partition("=")
            out.append((name, val or None))
        elif t.startswith("-") and len(t) > 1 and not t[1].isdigit():
            for ch in t[1:]:
                out.append((f"-{ch}", None))
        else:
            out.append((t, "arg"))
    return out


def explain(command_line, library=None):
    """Returns a list of (kind, key, text) rows: kind in {command, flag, arg, node, man}."""
    try:
        tokens = shlex.split(command_line)
    except ValueError:
        tokens = command_line.split()
    if not tokens:
        return []
    rows = []
    sudo = under_sudo(command_line)
    if sudo:
        rows.append(("flag", "sudo", "Run the rest as root (wheel members only on Pridwen); asks for your own password."))
        while tokens and (tokens[0] in ("sudo", "doas") or tokens[0].startswith("-")):
            tokens.pop(0)
        if not tokens:
            return rows
    cmd = os.path.basename(tokens[0])
    cur = load_curated(cmd)
    summary = (cur or {}).get("summary") or whatis(cmd) or "No description found."
    rows.append(("command", cmd, summary))
    manopts = None
    for flag, val in split_flags(tokens[1:]):
        if val == "arg":
            rows.append(("arg", flag, ""))
            continue
        textv = (cur or {}).get("_flags", {}).get(flag)
        if textv is None:
            if manopts is None:
                manopts = man_options(cmd)
            textv = manopts.get(flag)
        if textv is None and flag.startswith("-") and len(flag) == 2 and cur and any(k.startswith("-") for k in cur["_flags"]):
            textv = None
        rows.append(("flag", flag + (f"={val}" if val else ""), textv or "Not in the curated notes or the man page's option list."))
    node = (cur or {}).get("node")
    if library is not None and node:
        n = library.node(node)
        if n:
            rows.append(("node", node, f"{n.get('title', node)}: {n.get('summary', '')}"))
    man = (cur or {}).get("man") or f"{cmd}(1)"
    rows.append(("man", str(man), ""))
    return rows
