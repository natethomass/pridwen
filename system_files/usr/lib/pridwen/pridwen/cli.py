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
  pridwen why selinux          translate the newest SELinux denial
  pridwen quiet [1h|1d|forever|off]
  pridwen quiet hours off|22:00-08:00
  pridwen status               daemon, rules, events, quiet state
  pridwen dispatch test        send a test notification
  pridwen mission list [track] | show|start|check|reset <id>
  pridwen track [id]           track progress
  pridwen journal [note ...]   the journal, or add a note
  pridwen posture              the hardening baseline, pass/drift
  pridwen range list [track] | show|start|enter|check|reset|stop <id>
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
    out(text.render(fill(md)))   # {user}, {home}, {host} become the learner's own
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
        # From a notification action: Academy shows the lesson; a terminal is the fallback.
        try:
            subprocess.Popen(["/usr/bin/pridwen-academy", target], start_new_session=True)
            return 0
        except OSError:
            pass
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
    if arg == "hours":
        # pridwen quiet hours off | 22:00-08:00
        spec = (args[1] if len(args) > 1 else "").lower()
        if spec in ("off", "none", ""):
            cfg["quiet_hours"] = ""
            config.save(cfg)
            out(text.hint("Quiet hours are off. Nudges can arrive at any time (still capped per day).", None))
            return 0
        import re as _re
        if not _re.fullmatch(r"\d{1,2}:\d{2}-\d{1,2}:\d{2}", spec):
            out("usage: pridwen quiet hours off | HH:MM-HH:MM")
            return 2
        cfg["quiet_hours"] = spec
        config.save(cfg)
        out(text.hint(f"Quiet hours set to {spec}. Nudges wait until they end.", None))
        return 0
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


def cmd_dispatch(args, lib, store):
    """pridwen dispatch test: send a test notification through the same path the daemon uses."""
    if not args or args[0] != "test":
        out("usage: pridwen dispatch test")
        return 2
    from .dispatch import Dispatch, HAVE_NOTIFY
    d = Dispatch(store, lib)
    cfg = config.load()
    out(f"  libnotify  {'available' if HAVE_NOTIFY else 'missing (notify-send fallback)'}")
    out(f"  allowed    {'yes' if d.allowed() else 'no (quiet, quiet hours ' + str(cfg.get('quiet_hours')) + ', or daily cap)'}")
    d.send({"id": "test", "title": "Pridwen is listening", "body": "This is what a nudge looks like. Learn opens a lesson.", "lesson": "sudo-01"})
    out("  sent       a test notification (not counted against the cap)")
    if HAVE_NOTIFY:
        # Keep the process alive briefly so action callbacks can arrive.
        from gi.repository import GLib
        loop = GLib.MainLoop()
        GLib.timeout_add_seconds(20, loop.quit)
        out("  waiting    20 s for a button press; Ctrl-C to skip")
        try:
            loop.run()
        except KeyboardInterrupt:
            pass
    return 0


STATE_MARK = {"verified": "●", "in-progress": "◐", "available": "○", "locked": "·"}


def _progress(lib, store):
    from .missions import Catalog, Progress
    cat = Catalog()
    return cat, Progress(store, lib, cat)


def cmd_mission(args, lib, store):
    cat, prog = _progress(lib, store)
    if cat.errors:
        for e in cat.errors:
            out(f"  ! {e}")
    sub = args[0] if args else "list"
    if sub == "list":
        tid = args[1] if len(args) > 1 else None
        ids = cat.tracks[tid].missions if tid and tid in cat.tracks else sorted(cat.missions)
        for mid in ids:
            m = cat.missions.get(mid)
            if m:
                out(f"  {STATE_MARK[prog.mission_state(mid)]} {mid:<28} {m.title}  ({m.minutes} min, {m.node})")
        return 0
    if len(args) < 2 or args[1] not in cat.missions:
        out("usage: pridwen mission list [track] | show|check|reset|start <id>")
        return 2
    m = cat.missions[args[1]]
    if sub == "show":
        out(text.render(f"# {m.title}\n\n{m.brief}"))
        out(text.para("Steps:"))
        for i, s in enumerate(m.steps, 1):
            out(text.render(f"{i}. {s}"))
        out(text.para(f"Checks: {len(m.checks)}  ·  node {m.node}  ·  about {m.minutes} min  ·  state {prog.mission_state(m.id)}"))
        return 0
    if sub == "start":
        from .missions import run_shell
        rc, msg = run_shell(m.setup)
        out(text.hint("Mission set up. Read the brief with `pridwen mission show " + m.id + "`.", None) if rc == 0 else text.hint(f"Setup failed: {msg}", None))
        return 0 if rc == 0 else 1
    if sub == "reset":
        from .missions import run_shell
        rc, msg = run_shell(m.cleanup)
        store.mission_reset(m.id)
        out(text.hint("Mission reset." if rc == 0 else f"Cleanup returned {rc}: {msg}", None))
        return 0
    if sub == "check":
        allow_sudo = "--sudo" in args
        passed, results = prog.check(m.id, allow_sudo=allow_sudo)
        use_colour = text.colour_enabled()
        for cid, ok, msg in results:
            mark = (f"{text.SAGE}✓{text.RESET}" if ok else f"{text.CLAY}✗{text.RESET}") if use_colour else ("ok " if ok else "no ")
            out(text.wrap_coloured(text.code_spans(msg, use_colour=use_colour), text.width(), f"  {mark} {cid}: ", "       "))
        out()
        if passed:
            out(text.hint(f"Verified: {m.title}. Node `{m.node}` is now {prog.node_state(m.node)}.", None))
        else:
            out(text.hint("Not yet. Fix what is marked and check again; `pridwen mission show " + m.id + "` has hints.", None))
        return 0 if passed else 1
    out("usage: pridwen mission list [track] | show|check|reset|start <id>")
    return 2


def cmd_track(args, lib, store):
    cat, prog = _progress(lib, store)
    ids = [args[0]] if args and args[0] in cat.tracks else sorted(cat.tracks)
    for tid in ids:
        t = cat.tracks[tid]
        p = prog.track_progress(tid)
        out(f"  {t.title}: {p['verified']}/{p['total']} nodes verified")
        for n in t.nodes:
            out(f"    {STATE_MARK[p['nodes'][n]]} {lib.node(n).get('title', n)}")
        if p["next"]:
            out(text.para(f"Next up: {cat.missions[p['next']].title}  ·  pridwen mission show {p['next']}"))
        out()
    return 0


def cmd_journal(args, lib, store):
    if args:
        store.journal("note", None, " ".join(args))
        out(text.hint("Noted.", None))
        return 0
    day = None
    for e in store.journal_entries(60):
        d = time.strftime("%a %d %b", time.localtime(e["ts"]))
        if d != day:
            day = d
            out(f"\n  {d}")
        t = time.strftime("%H:%M", time.localtime(e["ts"]))
        kind = {"coach": "coach", "mission": "mission", "note": "note"}.get(e["kind"], e["kind"])
        out(text.wrap_coloured(text.code_spans(e["text"], use_colour=text.colour_enabled()), text.width(), f"    {t}  {kind:<8}", "                  "))
    return 0


def cmd_posture(args, lib, store):
    from .posture import evaluate
    use_colour = text.colour_enabled()
    for c in evaluate():
        if c["ok"]:
            mark = f"{text.SAGE}pass {text.RESET}" if use_colour else "pass "
        elif c.get("expected_drift"):
            mark = f"{text.GREY}later{text.RESET}" if use_colour else "later"
        else:
            mark = f"{text.CLAY}drift{text.RESET}" if use_colour else "drift"
        out(f"  {mark} {c.get('title', c['id']):<32} {'' if c['ok'] else c['message'][:70]}")
    out(text.para("later = planned for M6 and not yet shipped in the image. pridwen learn <lesson> explains each control."))
    return 0


def cmd_range(args, lib, store):
    from .missions import Progress
    from .range import runner
    cat = runner.catalog()
    prog = Progress(store, lib, cat)
    if cat.errors:
        for e in cat.errors:
            out(f"  ! {e}")
    sub = args[0] if args else "list"
    if sub == "list":
        tid = args[1] if len(args) > 1 else None
        ids = [m.id for m in cat.for_track(tid)] if tid else sorted(cat.missions)
        for mid in ids:
            m = cat.missions.get(mid)
            if not m:
                continue
            sid, _chair = cat.mission_scenario[mid]
            sc = cat.scenarios[sid]
            out(f"  {STATE_MARK[prog.mission_state(mid)]} {mid:<28} {m.title}  ({sc.kind}, {m.minutes} min, {m.node})")
        return 0
    if sub == "status":
        rows = runner.status(cat)
        if not rows:
            out(text.para("Nothing is running. `pridwen range start <id>` brings a scenario up."))
            return 0
        for r in rows:
            out(f"  {r['scenario']:<28} {r['target']:<14} {r['state']}")
        return 0
    if len(args) < 2 or args[1] not in cat.missions:
        out("usage: pridwen range list [track] | show|start|enter|check|reset|stop <id> | status")
        return 2
    mid = args[1]
    m = cat.missions[mid]
    sid, _chair = cat.mission_scenario[mid]
    sc = cat.scenarios[sid]
    if sub == "show":
        out(text.render(f"# {m.title}\n\n{m.brief}"))
        out(text.para("Steps:"))
        for i, s in enumerate(m.steps, 1):
            out(text.render(f"{i}. {s}"))
        out(text.para(f"Checks: {len(m.checks)}  ·  target {sc.kind}  ·  node {m.node}  ·  about {m.minutes} min  ·  state {prog.mission_state(mid)}"))
        return 0
    if sub == "start":
        try:
            name = runner.start(mid, cat)
        except runner.RunnerError as e:
            out(text.hint(str(e), None))
            return 1
        out(text.hint(f"{sid} is up. `pridwen range enter {mid}` gets you a root shell on {name}.", None))
        return 0
    if sub == "enter":
        target = args[2] if len(args) > 2 else None
        try:
            runner.enter(mid, target, cat)
        except runner.RunnerError as e:
            out(text.hint(str(e), None))
            return 1
        return 0
    if sub == "check":
        allow_sudo = "--sudo" in args
        try:
            results = runner.check(mid, allow_sudo=allow_sudo, store=store, lib=lib, cat=cat)
        except runner.RunnerError as e:
            out(text.hint(str(e), None))
            return 1
        use_colour = text.colour_enabled()
        for cid, ok, msg in results:
            mark = (f"{text.SAGE}✓{text.RESET}" if ok else f"{text.CLAY}✗{text.RESET}") if use_colour else ("ok " if ok else "no ")
            out(text.wrap_coloured(text.code_spans(msg, use_colour=use_colour), text.width(), f"  {mark} {cid}: ", "       "))
        out()
        passed = all(ok for _, ok, _ in results)
        if passed:
            # Not node_state(): this catalog only knows Range missions, and a node can
            # also carry a host mission that this Progress instance cannot see (see
            # CLAUDE.md, M4 status, "known integration gap" — the host and Range
            # catalogs are not yet merged), so a combined node state would risk being
            # wrong. Recorded in the same store either way; only the printed summary
            # is scoped back to what this command actually knows.
            out(text.hint(f"Verified: {m.title}.", None))
        else:
            out(text.hint("Not yet. Fix what is marked and check again; `pridwen range show " + mid + "` has hints.", None))
        return 0 if passed else 1
    if sub == "reset":
        target = args[2] if len(args) > 2 else None
        try:
            runner.reset(mid, target, cat)
        except runner.RunnerError as e:
            out(text.hint(str(e), None))
            return 1
        out(text.hint(f"{sid} is back to :seeded.", None))
        return 0
    if sub == "stop":
        try:
            runner.stop(mid, cat)
        except runner.RunnerError as e:
            out(text.hint(str(e), None))
            return 1
        out(text.hint(f"{sid} stopped; the seeded image is kept.", None))
        return 0
    out("usage: pridwen range list [track] | show|start|enter|check|reset|stop <id> | status")
    return 2


COMMANDS = {"why": cmd_why, "explain": cmd_explain, "learn": cmd_learn, "quiet": cmd_quiet, "status": cmd_status,
            "dispatch": cmd_dispatch, "mission": cmd_mission, "track": cmd_track, "journal": cmd_journal,
            "posture": cmd_posture, "range": cmd_range}


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
