"""The pridwen CLI: why, explain, learn, quiet, status."""
import os
import subprocess
import sys
import time

from . import config, socket_path, text, version
from .rules import Library, fill
from .store import Store
from . import selinux

USAGE = """pridwen: the Coach's pull side.

  pridwen why                  explain the last failed command
  pridwen explain <command...> annotate a command, flag by flag
  pridwen learn [id]           read a lesson; no id lists the tree
  pridwen quiet [1h|1d|forever|off]
  pridwen status               daemon, rules, events, quiet state
  pridwen version

Docs: /usr/share/doc/pridwen/coach.md
"""

EXIT_MEANINGS = {
    1: "a general failure: the program ran and reported a problem (read its message above)",
    2: "misuse: a bad flag or missing argument, usually",
    126: "found but not executable: check the mode with `ls -l` and add `chmod +x` if it is a script",
    127: "command not found: not installed, or not on `PATH`",
    128: "an invalid exit argument from a script",
    130: "you pressed Ctrl-C (terminated by SIGINT)",
    137: "killed by SIGKILL, often the kernel's out-of-memory killer or `kill -9`",
    139: "segmentation fault: the program crashed",
    143: "terminated by SIGTERM, a polite kill",
    255: "an exit status out of range, common from ssh when the connection failed",
}


def out(s=""):
    print(s)


def cmd_why(args, lib, store):
    if args and args[0] == "selinux":
        if not selinux.enforcing():
            out(text.hint("SELinux is not enforcing here, so nothing is being denied.", None))
            return 0
        se = selinux.latest_explanation(since_seconds=24 * 3600)
        out(text.render(se) if se else text.hint("No SELinux denials in the last day (or the journal is not readable: `journalctl _TRANSPORT=audit`).", "selinux-01"))
        return 0
    ev = store.last_failed(within=6 * 3600)
    if ev is None:
        out(text.hint("Nothing has failed in the last six hours. When a command does, `pridwen why` explains it.", None))
        return 0
    cmd, code = ev["cmd"], ev["exit"]
    out(text.hint(f"Last failure: `{cmd}` (exit {code}, {time.strftime('%H:%M', time.localtime(ev['ts']))})", None))
    out()
    matches = lib.match_all(cmd, code, ev["cwd"])
    explained = False
    for rule, groups in matches:
        if rule.why:
            body = fill(rule.why, groups)
            if not body.lstrip().startswith("#"):
                body = f"# {fill(rule.hint, groups)}\n\n{body}"
            out(text.render(body))
            if rule.man:
                out(text.para("man: " + ", ".join(rule.man)))
            out(text.para(f"Lesson: {rule.lesson}  ·  pridwen learn {rule.lesson}"))
            explained = True
            break
    if not explained and matches:
        rule, groups = matches[0]
        out(text.render(f"# {fill(rule.hint, groups)}"))
        out(text.para(f"Lesson: {rule.lesson}  ·  pridwen learn {rule.lesson}"))
        explained = True
    # A recent denial is shown when nothing else explained the failure, or when
    # the denied process is the command that failed. Otherwise it is noise from
    # elsewhere on the system (daemons trip the policy too) and only gets a line.
    if selinux.enforcing():
        denials = selinux.recent_denials(since_seconds=15 * 60, limit=3)
        if denials:
            word = cmd.split()[0] if cmd.split() else ""
            mine = [d for d in denials if d.get("comm", "").strip('"') == word]
            if mine or not explained:
                out()
                out(text.render(selinux.translate((mine or denials)[0])))
                if not mine:
                    out(text.para("This denial may be unrelated to your command; it is the newest one on the system."))
                explained = True
            else:
                out()
                out(text.para(f"Also: SELinux denied `{denials[0].get('comm', '?')}` recently. `pridwen why selinux` translates it."))
    if not explained:
        meaning = EXIT_MEANINGS.get(code, "a program-specific status; its man page lists what each code means")
        out(text.render(f"# Exit status {code}\n\nExit {code} means {meaning}. "
                        f"Run `pridwen explain {cmd.split()[0]}` for the command itself, and `man {cmd.split()[0]}` for the rest."))
    return 0


def cmd_explain(args, lib, store):
    if not args:
        out("usage: pridwen explain <command...>")
        return 2
    from .explain import explain
    rows = explain(" ".join(args), lib)
    if not rows:
        return 1
    use_colour = text.colour_enabled()
    for kind, key, body in rows:
        if kind == "command":
            k = f"{text.BOLD}{text.CREAM}{key}{text.RESET}" if use_colour else key
            out(f"  {k}  {body}")
        elif kind == "flag":
            k = f"{text.SAGE}{key}{text.RESET}" if use_colour else key
            out(text.wrap_coloured(text.code_spans(body, use_colour=use_colour), text.width(), f"    {k}  ", "          "))
        elif kind == "arg":
            k = f"{text.GREY}{key}{text.RESET}" if use_colour else key
            out(f"    {k}")
        elif kind == "node":
            out()
            out(text.para(f"Tree: {body}"))
        elif kind == "man":
            out(text.para(f"man: {key}"))
    return 0


def render_lesson(lib, lesson_id):
    path = lib.lesson_path(lesson_id)
    try:
        with open(path, encoding="utf-8") as f:
            md = f.read()
    except OSError:
        return False
    out(text.render(md))
    node = lib.lesson_node(lesson_id)
    if node:
        n = lib.node(node)
        out()
        out(text.para(f"Tree: {n.get('title', node)} ({node})  ·  lessons: {', '.join(n.get('lessons', []))}"))
    return True


def cmd_learn(args, lib, store):
    open_terminal = False
    if args and args[0] == "--open":
        open_terminal = True
        args = args[1:]
    if not args:
        fired = store.firings()
        use_colour = text.colour_enabled()
        for tier, nodes in (lib.tree.get("tiers") or {}).items():
            out(f"{text.BOLD}{text.CREAM}{tier.upper()}{text.RESET}" if use_colour else tier.upper())
            for nid in nodes:
                n = lib.node(nid)
                hits = sum(1 for r in lib.rules if r.node == nid and r.id in fired)
                mark = f"{text.SAGE}●{text.RESET}" if use_colour and hits else "○"
                lessons = ", ".join(n.get("lessons") or [])
                out(f"  {mark} {n.get('title', nid):<18} {text.GREY if use_colour else ''}{lessons}{text.RESET if use_colour else ''}")
            out()
        out(text.para("pridwen learn <lesson-id> reads one. A filled dot means the Coach has already pointed you at that node."))
        return 0
    target = args[0]
    if target in (lib.tree.get("nodes") or {}):
        lessons = lib.node(target).get("lessons") or []
        target = lessons[0] if lessons else target
    if open_terminal:
        # From a notification action: open a terminal with the lesson.
        for term in (["ptyxis", "--", "sh", "-c"], ["gnome-terminal", "--", "sh", "-c"]):
            try:
                subprocess.Popen(term + [f"/usr/bin/pridwen learn {target}; echo; read -p 'Enter to close' _"])
                return 0
            except OSError:
                continue
    if not render_lesson(lib, target):
        out(f"No lesson '{target}'. `pridwen learn` lists them.")
        return 1
    return 0


def cmd_quiet(args, lib, store):
    cfg = config.load()
    arg = (args[0] if args else "1h").lower()
    if arg in ("off", "on", "resume"):
        cfg["quiet_until"] = 0
        cfg["enabled"] = True
        config.save(cfg)
        out(text.hint("The coach is back.", None))
        return 0
    if arg == "forever":
        cfg["quiet_until"] = -1
        config.save(cfg)
        out(text.hint("Quiet until you say `pridwen quiet off`. Nothing is recorded differently; only the hints stop.", None))
        return 0
    units = {"h": 3600, "d": 86400, "m": 60, "w": 7 * 86400}
    try:
        n, u = int(arg[:-1]), arg[-1]
        seconds = n * units[u]
    except (ValueError, KeyError):
        out("usage: pridwen quiet [1h|1d|forever|off]")
        return 2
    cfg["quiet_until"] = int(time.time() + seconds)
    config.save(cfg)
    out(text.hint(f"Quiet for {arg}. `pridwen quiet off` ends it early.", None))
    return 0


def cmd_status(args, lib, store):
    cfg = config.load()
    quiet, why = config.quiet_state(cfg)
    sock = socket_path()
    daemon = "running" if os.path.exists(sock) else "not running (systemctl --user status pridwend)"
    out(f"  Pridwen {version()}")
    out(f"  daemon     {daemon}")
    out(f"  rules      {len(lib.rules)} in {len({r.source for r in lib.rules})} files, {len(lib.nudges)} nudges" + (f", {len(lib.errors)} load errors" if lib.errors else ""))
    out(f"  events     {store.count_events()} stored in {store.path}")
    out(f"  coach      {'quiet (' + why + ')' if quiet else 'on'}; quiet hours {cfg.get('quiet_hours') or 'none'}")
    out(f"  dispatch   {'on' if cfg.get('dispatch', True) else 'off'}; cap {cfg.get('daily_cap')} per day; "
        f"{store.nudges_sent_since(time.time() - 86400)} sent today")
    out(f"  selinux    {'enforcing' if selinux.enforcing() else 'not enforcing'}")
    if lib.errors:
        out()
        for e in lib.errors[:10]:
            out(f"  ! {e}")
    return 0


COMMANDS = {"why": cmd_why, "explain": cmd_explain, "learn": cmd_learn, "quiet": cmd_quiet, "status": cmd_status}


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        out(USAGE)
        return 0
    if argv[0] in ("version", "--version"):
        out(f"pridwen {version()}")
        return 0
    fn = COMMANDS.get(argv[0])
    if fn is None:
        out(f"pridwen: unknown command '{argv[0]}'\n")
        out(USAGE)
        return 2
    lib = Library()
    store = Store()
    try:
        return fn(argv[1:], lib, store)
    finally:
        store.close()
