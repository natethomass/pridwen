"""pridwend: the per-user Coach and Dispatch daemon.

Listens on $XDG_RUNTIME_DIR/pridwen/coach.sock. Each connection carries one
JSON event line from a shell hook; the reply (if any) is a coloured hint the
hook prints. Also watches for SELinux denials and staged bootc updates and
hands those to Dispatch. GLib main loop; no threads.
"""
import json
import os
import signal
import socket
import sys
import time

import gi
from gi.repository import GLib, Gio

from . import config, runtime_dir, socket_path, text, version
from .dispatch import Dispatch
from .rules import Library, scrub
from .store import Store
from . import selinux

gi.require_version("Gio", "2.0")


def log(msg):
    print(f"pridwend: {msg}", file=sys.stderr, flush=True)


class Daemon:
    def __init__(self):
        self.store = Store()
        self.lib = Library()
        self.dispatch = Dispatch(self.store, self.lib)
        self.seen_avc = set()
        self.last_bootc_check = 0.0
        self.staged_seen = None
        self.loop = GLib.MainLoop()
        self.service = None
        self.events = 0

    # ---- socket -------------------------------------------------------------
    def listen(self):
        os.makedirs(runtime_dir(), mode=0o700, exist_ok=True)
        path = socket_path()
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        addr = Gio.UnixSocketAddress.new(path)
        self.service = Gio.SocketService.new()
        self.service.add_address(addr, Gio.SocketType.STREAM, Gio.SocketProtocol.DEFAULT, None)
        self.service.connect("incoming", self.on_incoming)
        os.chmod(path, 0o600)
        self.service.start()
        log(f"listening on {path}; {len(self.lib.rules)} rules, {len(self.lib.nudges)} nudges, version {version()}")

    def on_incoming(self, _service, conn, _source):
        inp = Gio.DataInputStream.new(conn.get_input_stream())
        inp.read_line_async(GLib.PRIORITY_DEFAULT, None, self.on_line, conn)
        return True

    def on_line(self, inp, res, conn):
        try:
            line, _ = inp.read_line_finish_utf8(res)
        except GLib.Error as e:
            log(f"read failed: {e.message}")
            conn.close(None)
            return
        reply = ""
        if line:
            try:
                reply = self.handle(json.loads(line)) or ""
            except (ValueError, KeyError, TypeError) as e:
                log(f"bad event: {e}: {line[:120]!r}")
            except Exception as e:  # noqa: BLE001 - a bug must never break the shell
                log(f"handler error: {e!r}")
        try:
            out = conn.get_output_stream()
            if reply:
                out.write_all((reply + "\n").encode(), None)
            out.close(None)
        except GLib.Error:
            pass
        conn.close(None)

    # ---- events -------------------------------------------------------------
    def handle(self, ev):
        cmd = scrub(str(ev.get("cmd", ""))).strip()
        if not cmd:
            return None
        exit_code = int(ev.get("exit", 0))
        ms = int(ev.get("ms", 0))
        cwd = ev.get("cwd")
        shell = ev.get("shell")
        pid = ev.get("pid")
        self.events += 1
        eid = self.store.add_event(cmd, exit_code, ms, cwd, shell, pid)

        # Ignore what pridwen itself does.
        if cmd.startswith("pridwen"):
            return None

        quiet, _ = config.quiet_state()
        try:
            self.dispatch.on_command(cmd)
        except Exception as e:  # noqa: BLE001
            log(f"dispatch error: {e!r}")

        rule, groups = self.lib.match(cmd, exit_code, cwd, skip=lambda r: self.store.fired_recently(r.id, r.cooldown))
        if rule is None:
            self.background_checks(exit_code)
            return None
        self.store.record_firing(rule.id)
        self.store.set_event_rule(eid, rule.id)
        if quiet:
            return None
        from .rules import fill
        return text.hint(fill(rule.hint, groups), rule.lesson, cols=100, use_colour=True)

    def background_checks(self, exit_code):
        """Cheap, throttled checks after failures: new SELinux denial? staged update?"""
        if exit_code != 0 and selinux.enforcing() and selinux.throttle(20):
            d = selinux.poll_new(self.seen_avc, since_seconds=30)
            if d:
                log(f"new AVC: {d.get('comm')} {d.get('perms')} {d.get('tclass')}")
                self.dispatch.on_event("selinux_denial")

    def tick(self):
        """Every 10 minutes: has bootc staged an update?"""
        try:
            r = Gio.Subprocess.new(["bootc", "status", "--json"], Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE)
            ok, out, _ = r.communicate_utf8(None, None)
            if ok and out:
                st = json.loads(out)
                staged = (st.get("status") or {}).get("staged") or {}
                digest = (staged.get("image") or {}).get("imageDigest") or ""
                if digest and digest != self.staged_seen:
                    self.staged_seen = digest
                    if self.store.get("bootc_staged_notified") != digest:
                        self.store.set("bootc_staged_notified", digest)
                        ver = ((staged.get("image") or {}).get("version")) or "a new image"
                        self.dispatch.on_event("bootc_staged", f"Staged: {ver}. Reboot when you're ready.")
        except (GLib.Error, ValueError, OSError) as e:
            log(f"bootc check skipped: {e}")
        return True

    # ---- lifecycle ----------------------------------------------------------
    def run(self):
        self.listen()
        GLib.timeout_add_seconds(600, self.tick)
        GLib.timeout_add_seconds(30, lambda: (self.tick(), False)[1])
        for sig in (signal.SIGTERM, signal.SIGINT):
            GLib.unix_signal_add(GLib.PRIORITY_HIGH, sig, self.stop)
        self.loop.run()
        return 0

    def stop(self, *_):
        log("stopping")
        try:
            os.unlink(socket_path())
        except OSError:
            pass
        self.loop.quit()
        return False


def main():
    if os.environ.get("XDG_RUNTIME_DIR") is None:
        log("no XDG_RUNTIME_DIR; refusing to start")
        return 1
    return Daemon().run()
