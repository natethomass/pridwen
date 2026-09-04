"""Dispatch: earned nudges as GNOME notifications.

Every nudge is earned: a counter crossed a threshold or an event happened.
Notifications carry actions (Learn, Snooze, Not this again), respect quiet
hours and `pridwen quiet`, and are capped per day. Uses libnotify through GI
when available; falls back to notify-send without actions.
"""
import subprocess
import sys
import time

from . import config

try:
    import gi
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify
    HAVE_NOTIFY = True
except (ImportError, ValueError):
    HAVE_NOTIFY = False

APP_NAME = "Pridwen"
ICON = "pridwen"
SNOOZE_S = 24 * 3600


def log(msg):
    print(f"pridwend dispatch: {msg}", file=sys.stderr, flush=True)


class Dispatch:
    def __init__(self, store, library):
        self.store = store
        self.lib = library
        self.live = {}   # keep Notify.Notification objects alive while shown
        if HAVE_NOTIFY:
            try:
                Notify.init(APP_NAME)
            except Exception as e:  # noqa: BLE001
                log(f"libnotify init failed: {e}")

    # ---- gating -------------------------------------------------------------
    def allowed(self):
        cfg = config.load()
        if not cfg.get("dispatch", True):
            return False
        quiet, _ = config.quiet_state(cfg)
        if quiet or config.in_quiet_hours(cfg):
            return False
        day_start = time.time() - 86400
        return self.store.nudges_sent_since(day_start) < int(cfg.get("daily_cap", 3))

    def nudge_ready(self, n):
        st = self.store.nudge(n["id"])
        if st is None:
            return True
        if st["disabled"]:
            return False
        if st["snoozed_until"] and st["snoozed_until"] > time.time():
            return False
        if st["sent_ts"]:
            rep = n.get("repeat")
            return bool(rep) and (time.time() - st["sent_ts"]) > int(rep)
        return True

    # ---- triggers -----------------------------------------------------------
    def on_command(self, cmd):
        """Bump count-based nudges; send the first one that crosses its threshold."""
        for n in self.lib.nudges:
            rx = n.get("_regex")
            if rx is None or not rx.search(cmd):
                continue
            count = self.store.bump(f"nudge:{n['id']}")
            threshold = int((n.get("count") or {}).get("threshold", 1))
            if count < threshold:
                continue
            # Once earned, a nudge that was held (quiet hours, daily cap) is
            # retried on later commands until it is actually sent.
            st = self.store.nudge(n["id"])
            unsent = st is None or not st["sent_ts"]
            if unsent or (n.get("repeat") and count % threshold == 0):
                self.maybe_send(n)

    def on_event(self, event_name, extra=None):
        for n in self.lib.nudges:
            if n.get("event") == event_name:
                self.maybe_send(n, extra)

    def maybe_send(self, n, extra=None):
        if not self.nudge_ready(n):
            return False
        if not self.allowed():
            log(f"held {n['id']}: quiet or capped")
            return False
        self.send(n, extra)
        self.store.nudge_sent(n["id"])
        return True

    # ---- sending ------------------------------------------------------------
    def send(self, n, extra=None):
        title = n.get("title", "Pridwen")
        body = n.get("body", "")
        if extra:
            body = f"{body}\n{extra}".strip()
        lesson = n.get("lesson")
        log(f"sending {n['id']}: {title}")
        if HAVE_NOTIFY:
            try:
                note = Notify.Notification.new(title, body, ICON)
                note.set_app_name(APP_NAME)
                note.set_timeout(20000)
                if lesson:
                    note.add_action("learn", "Learn", self._act_learn, (n["id"], lesson))
                note.add_action("snooze", "Snooze", self._act_snooze, n["id"])
                note.add_action("never", "Not this again", self._act_never, n["id"])
                note.connect("closed", self._closed, n["id"])
                note.show()
                self.live[n["id"]] = note
                return
            except Exception as e:  # noqa: BLE001
                log(f"libnotify failed: {e}; falling back to notify-send")
        try:
            subprocess.run(["notify-send", "-a", APP_NAME, "-i", ICON, title, body], timeout=5)
        except (OSError, subprocess.SubprocessError) as e:
            log(f"notify-send failed: {e}")

    def _closed(self, note, nid):
        self.live.pop(nid, None)

    def _act_learn(self, note, action, data):
        nid, lesson = data
        log(f"{nid}: learn {lesson}")
        try:
            subprocess.Popen(["/usr/bin/pridwen", "learn", "--open", lesson])
        except OSError as e:
            log(f"could not open lesson: {e}")
        note.close()

    def _act_snooze(self, note, action, nid):
        log(f"{nid}: snoozed")
        self.store.nudge_snooze(nid, time.time() + SNOOZE_S)
        note.close()

    def _act_never(self, note, action, nid):
        log(f"{nid}: disabled")
        self.store.nudge_disable(nid)
        note.close()
