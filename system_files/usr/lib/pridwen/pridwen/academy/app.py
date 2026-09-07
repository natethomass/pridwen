"""Pridwen Academy window: Tree, Tracks, Journal, Posture."""
import os
import subprocess
import threading
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .. import version  # noqa: E402
from ..missions import Catalog, Progress, run_shell  # noqa: E402
from ..posture import evaluate as posture_evaluate  # noqa: E402
from ..rules import Library, fill  # noqa: E402
from ..store import Store  # noqa: E402
from . import md  # noqa: E402

APP_ID = "org.pridwen.Academy"

CSS = b"""
.pridwen-code { padding: 12px 14px; }
.pridwen-codeframe { border-radius: 12px; }
.state-verified { color: #6E9E7A; }
.state-in-progress { color: #5F7E9B; }
.state-available { color: alpha(currentColor, 0.7); }
.state-locked { color: alpha(currentColor, 0.35); }
.pridwen-dot { font-size: 18px; }
.check-ok { color: #6E9E7A; }
.check-fail { color: #B9714E; }
.pridwen-lede { font-size: 15px; opacity: 0.8; }
"""

STATE_LABEL = {"verified": "Verified", "in-progress": "In progress", "available": "Available", "locked": "Locked"}
STATE_DOT = {"verified": "●", "in-progress": "◐", "available": "○", "locked": "·"}


def dot(state):
    lab = Gtk.Label(label=STATE_DOT.get(state, "○"), valign=Gtk.Align.CENTER)
    lab.add_css_class("pridwen-dot")
    lab.add_css_class(f"state-{state}")
    return lab


def scroll(child):
    sw = Gtk.ScrolledWindow(child=child, hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
    return sw


def clamp(child, maximum=760):
    c = Adw.Clamp(child=child, maximum_size=maximum, tightening_threshold=560)
    c.set_margin_top(24)
    c.set_margin_bottom(32)
    c.set_margin_start(20)
    c.set_margin_end(20)
    return c


class Academy(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.store = Store()
        self.lib = Library()
        self.cat = Catalog()
        self.prog = Progress(self.store, self.lib, self.cat)
        self.win = None
        self.nav = None
        self.start_page = None

    # ---- lifecycle ----------------------------------------------------------
    def do_startup(self):
        Adw.Application.do_startup(self)
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        for name, cb in (("quit", lambda *_: self.quit()), ("about", self.on_about)):
            a = Gio.SimpleAction.new(name, None)
            a.connect("activate", cb)
            self.add_action(a)
        self.set_accels_for_action("app.quit", ["<primary>q"])

    def do_command_line(self, cmdline):
        args = cmdline.get_arguments()[1:]
        self.activate()
        if args:
            self.open_ref(args[0])
        return 0

    def do_activate(self):
        if self.win is None:
            self.build_window()
        self.win.present()

    def on_about(self, *_):
        Adw.AboutDialog(application_name="Pridwen Academy", application_icon="pridwen", version=version(),
                        developer_name="Pridwen OS", comments="The skill tree. Verified means a checker saw it.",
                        website="https://github.com/natethomass/pridwen").present(self.win)

    # ---- window -------------------------------------------------------------
    def build_window(self):
        self.win = Adw.ApplicationWindow(application=self, title="Academy", default_width=1080, default_height=720)
        self.win.set_icon_name("pridwen")
        split = Adw.NavigationSplitView()
        self.sidebar_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.sidebar_list.add_css_class("navigation-sidebar")
        for key, title, icon in (("tree", "Skill tree", "view-list-symbolic"), ("tracks", "Tracks", "emblem-ok-symbolic"),
                                 ("journal", "Journal", "document-edit-symbolic"), ("posture", "Posture", "security-high-symbolic")):
            row = Gtk.ListBoxRow()
            row.key = key
            box = Gtk.Box(spacing=10, margin_top=6, margin_bottom=6, margin_start=6)
            box.append(Gtk.Image.new_from_icon_name(icon))
            box.append(Gtk.Label(label=title, xalign=0))
            row.set_child(box)
            self.sidebar_list.append(row)
        self.sidebar_list.connect("row-selected", self.on_sidebar)
        side_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header = Adw.HeaderBar()
        menu = Gio.Menu()
        menu.append("About Academy", "app.about")
        menu.append("Quit", "app.quit")
        header.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu))
        side_box.append(header)
        side_box.append(scroll(self.sidebar_list))
        foot = Gtk.Label(label=f"Pridwen {version()}", xalign=0, margin_start=14, margin_bottom=10)
        foot.add_css_class("dim-label")
        side_box.append(foot)
        split.set_sidebar(Adw.NavigationPage(title="Academy", child=side_box))

        self.nav = Adw.NavigationView()
        split.set_content(Adw.NavigationPage(title="Content", child=self.nav))
        self.win.set_content(split)
        self.sidebar_list.select_row(self.sidebar_list.get_row_at_index(0))

    def on_sidebar(self, _list, row):
        if row is None:
            return
        page = {"tree": self.page_tree, "tracks": self.page_tracks, "journal": self.page_journal, "posture": self.page_posture}[row.key]()
        self.nav.replace([page])

    def push(self, page):
        self.nav.push(page)

    def refresh(self):
        """Rebuild the current stack after state changed."""
        row = self.sidebar_list.get_selected_row()
        if row is not None:
            self.on_sidebar(self.sidebar_list, row)

    def open_ref(self, ref):
        """Open a mission, node or lesson id from the command line / notifications."""
        if ref in self.cat.missions:
            self.push(self.page_mission(ref))
        elif ref in (self.lib.tree.get("nodes") or {}):
            self.push(self.page_node(ref))
        elif self.lib.lesson_node(ref):
            self.push(self.page_lesson(ref))

    def page(self, title, child, tag=None):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(Adw.HeaderBar(show_title=False))
        box.append(scroll(clamp(child)))
        p = Adw.NavigationPage(title=title, child=box)
        if tag:
            p.set_tag(tag)
        return p

    # ---- Tree ---------------------------------------------------------------
    def page_tree(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        t = Gtk.Label(label="Skill tree", xalign=0)
        t.add_css_class("title-1")
        box.append(t)
        lede = Gtk.Label(label="Verified means a checker saw it on a real system. Locked nodes open when what they build on is verified.", xalign=0, wrap=True)
        lede.add_css_class("pridwen-lede")
        box.append(lede)
        for tier, nodes in (self.lib.tree.get("tiers") or {}).items():
            group = Adw.PreferencesGroup(title=tier.capitalize())
            for nid in nodes:
                n = self.lib.node(nid)
                state = self.prog.node_state(nid)
                missions = self.cat.for_node(nid)
                verified = sum(1 for m in missions if self.prog.mission_state(m.id) == "verified")
                row = Adw.ActionRow(title=n.get("title", nid), subtitle=n.get("summary", ""), activatable=True)
                row.add_prefix(dot(state))
                tail = Gtk.Label(label=f"{STATE_LABEL[state]}" + (f" · {verified}/{len(missions)} missions" if missions else ""))
                tail.add_css_class("dim-label")
                row.add_suffix(tail)
                row.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
                row.connect("activated", lambda _r, nid=nid: self.push(self.page_node(nid)))
                group.add(row)
            box.append(group)
        return self.page("Skill tree", box, "tree")

    # ---- Node ---------------------------------------------------------------
    def page_node(self, nid):
        n = self.lib.node(nid)
        state = self.prog.node_state(nid)
        self.store.touch_node(nid)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        head = Gtk.Box(spacing=12)
        head.append(dot(state))
        t = Gtk.Label(label=n.get("title", nid), xalign=0)
        t.add_css_class("title-1")
        head.append(t)
        box.append(head)
        s = Gtk.Label(label=n.get("summary", ""), xalign=0, wrap=True)
        s.add_css_class("pridwen-lede")
        box.append(s)
        if n.get("requires"):
            req = ", ".join(self.lib.node(r).get("title", r) for r in n["requires"])
            box.append(Gtk.Label(label=f"Builds on: {req}", xalign=0, css_classes=["dim-label"]))

        lessons = Adw.PreferencesGroup(title="Lessons")
        for lid in n.get("lessons") or []:
            title = self.lesson_title(lid)
            row = Adw.ActionRow(title=title, subtitle=lid, activatable=True)
            row.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
            row.connect("activated", lambda _r, lid=lid: self.push(self.page_lesson(lid)))
            lessons.add(row)
        box.append(lessons)

        missions = self.cat.for_node(nid)
        if missions:
            mg = Adw.PreferencesGroup(title="Missions", description="Verified by a checker, never by a quiz.")
            for m in missions:
                ms = self.prog.mission_state(m.id)
                row = Adw.ActionRow(title=m.title, subtitle=f"{m.minutes} min · {m.track}" + ("" if m.required else " · optional"), activatable=True)
                row.add_prefix(dot(ms))
                row.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
                row.connect("activated", lambda _r, mid=m.id: self.push(self.page_mission(mid)))
                mg.add(row)
            box.append(mg)

        fired = [e for e in self.store.journal_entries(300) if e["kind"] == "coach" and e["node"] == nid][:8]
        if fired:
            cg = Adw.PreferencesGroup(title="What the Coach said here")
            for e in fired:
                when = time.strftime("%d %b %H:%M", time.localtime(e["ts"]))
                row = Adw.ActionRow(title=GLib.markup_escape_text(e["text"].split("  ->  ", 1)[-1]), subtitle=when)
                cg.add(row)
            box.append(cg)
        return self.page(n.get("title", nid), box)

    def lesson_title(self, lid):
        try:
            with open(self.lib.lesson_path(lid), encoding="utf-8") as f:
                first = f.readline().strip()
            return first.lstrip("# ").strip() or lid
        except OSError:
            return lid

    # ---- Lesson -------------------------------------------------------------
    def page_lesson(self, lid):
        try:
            with open(self.lib.lesson_path(lid), encoding="utf-8") as f:
                text = fill(f.read())
        except OSError:
            text = f"# {lid}\n\nNo lesson text yet."
        nid = self.lib.lesson_node(lid)
        if nid:
            self.store.touch_node(nid)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.append(md.render(text))
        return self.page(self.lesson_title(lid), box)

    # ---- Mission ------------------------------------------------------------
    def page_mission(self, mid):
        m = self.cat.missions[mid]
        state = self.prog.mission_state(mid)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        head = Gtk.Box(spacing=12)
        head.append(dot(state))
        t = Gtk.Label(label=m.title, xalign=0, wrap=True)
        t.add_css_class("title-1")
        head.append(t)
        box.append(head)
        meta = Gtk.Label(label=f"{STATE_LABEL[state]} · about {m.minutes} min · {self.lib.node(m.node).get('title', m.node)} · on this computer",
                         xalign=0, css_classes=["dim-label"])
        box.append(meta)
        box.append(md.render(fill(m.brief)))

        steps = Adw.PreferencesGroup(title="Steps")
        for i, s in enumerate(m.steps, 1):
            steps.add(Adw.ActionRow(title=md.inline(fill(s)), use_markup=True, title_lines=0))
            steps.get_last_child()
        box.append(steps)

        if m.hints:
            hints = Adw.PreferencesGroup(title="Hints", description="One at a time. Try first.")
            hint_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            btn = Gtk.Button(label="Show a hint", halign=Gtk.Align.START)
            shown = {"n": 0}

            def reveal(*_):
                if shown["n"] < len(m.hints):
                    lab = Gtk.Label(label="", xalign=0, wrap=True, use_markup=True)
                    lab.set_markup(md.inline(fill(m.hints[shown["n"]])))
                    hint_box.append(lab)
                    shown["n"] += 1
                if shown["n"] >= len(m.hints):
                    btn.set_sensitive(False)
                    btn.set_label("No more hints")
            btn.connect("clicked", reveal)
            wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=6)
            wrap.append(hint_box)
            wrap.append(btn)
            hints.add(wrap)
            box.append(hints)

        results = Adw.PreferencesGroup(title="Checks")
        for c in m.checks:
            row = Adw.ActionRow(title=c.get("id", "check"), subtitle="Not run yet")
            row.check = c
            results.add(row)
        box.append(results)

        actions = Gtk.Box(spacing=10)
        check = Gtk.Button(label="Check my work")
        check.add_css_class("suggested-action")
        check.add_css_class("pill")
        status = Gtk.Label(label="", xalign=0, wrap=True)
        actions.append(check)
        if m.setup:
            start = Gtk.Button(label="Set up the scenario")
            start.add_css_class("pill")
            start.connect("clicked", lambda *_: self.run_script(m.setup, status, "Scenario ready. Go break-fix it."))
            actions.append(start)
        if m.cleanup:
            reset = Gtk.Button(label="Reset")
            reset.add_css_class("pill")
            reset.connect("clicked", lambda *_: (self.run_script(m.cleanup, status, "Reset done."), self.store.mission_reset(mid)))
            actions.append(reset)
        box.append(actions)
        box.append(status)

        def do_check(*_):
            check.set_sensitive(False)
            status.set_label("Checking…")

            def work():
                # Only the checks run off the main thread; the store (SQLite,
                # main-thread only) is touched in done().
                try:
                    res = self.prog.run_checks(mid, allow_sudo=False)
                except Exception as e:  # noqa: BLE001
                    res = e
                GLib.idle_add(done, res)

            def done(res):
                if isinstance(res, Exception):
                    status.set_label(f"The checker crashed: {res!r}. Try `pridwen mission check {mid}` in a terminal.")
                    check.set_sensitive(True)
                    return False
                passed = self.prog.record(mid, res)
                rows = {}
                # PreferencesGroup nests rows; walk to find our ActionRows.
                for row in self._iter_rows(results):
                    rows[row.check.get("id", "check")] = row
                for cid, ok, msg in res:
                    row = rows.get(cid)
                    if row is not None:
                        row.set_subtitle(GLib.markup_escape_text(msg))
                        row.remove_css_class("check-ok")
                        row.remove_css_class("check-fail")
                        row.add_css_class("check-ok" if ok else "check-fail")
                        row.set_title(("✓ " if ok else "✗ ") + cid)
                if passed:
                    status.set_markup(f'<span foreground="#6E9E7A"><b>Verified.</b></span> {GLib.markup_escape_text(self.lib.node(m.node).get("title", m.node))} is now {self.prog.node_state(m.node)}.')
                else:
                    status.set_label("Not yet. Fix what is marked and check again.")
                check.set_sensitive(True)
                return False
            threading.Thread(target=work, daemon=True).start()
        check.connect("clicked", do_check)
        return self.page(m.title, box)

    @staticmethod
    def _iter_rows(group):
        """Yield the Adw.ActionRows inside a PreferencesGroup."""
        stack = [group]
        while stack:
            w = stack.pop()
            if isinstance(w, Adw.ActionRow) and hasattr(w, "check"):
                yield w
            child = w.get_first_child()
            while child is not None:
                stack.append(child)
                child = child.get_next_sibling()

    def run_script(self, script, status, ok_text):
        status.set_label("Running…")

        def work():
            rc, msg = run_shell(script)
            GLib.idle_add(lambda: (status.set_label(ok_text if rc == 0 else f"Script returned {rc}: {msg[:200]}"), False)[1])
        threading.Thread(target=work, daemon=True).start()

    # ---- Tracks -------------------------------------------------------------
    def page_tracks(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        t = Gtk.Label(label="Tracks", xalign=0)
        t.add_css_class("title-1")
        box.append(t)
        for tid, tr in sorted(self.cat.tracks.items()):
            p = self.prog.track_progress(tid)
            group = Adw.PreferencesGroup(title=tr.title, description=tr.lede)
            bar = Gtk.ProgressBar(fraction=(p["verified"] / p["total"]) if p["total"] else 0, show_text=True,
                                  text=f"{p['verified']} of {p['total']} nodes verified", margin_bottom=8)
            group.add(bar)
            for mid in tr.missions:
                m = self.cat.missions.get(mid)
                if m is None:
                    continue
                ms = p["missions"][mid]
                row = Adw.ActionRow(title=m.title, subtitle=f"{self.lib.node(m.node).get('title', m.node)} · {m.minutes} min", activatable=True)
                row.add_prefix(dot(ms))
                if mid == p["next"]:
                    nxt = Gtk.Label(label="Next up")
                    nxt.add_css_class("accent")
                    row.add_suffix(nxt)
                row.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
                row.connect("activated", lambda _r, mid=mid: self.push(self.page_mission(mid)))
                group.add(row)
            box.append(group)
        if not self.cat.tracks:
            box.append(Gtk.Label(label="No tracks installed.", xalign=0))
        return self.page("Tracks", box, "tracks")

    # ---- Journal ------------------------------------------------------------
    def page_journal(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        t = Gtk.Label(label="Journal", xalign=0)
        t.add_css_class("title-1")
        box.append(t)
        entry = Gtk.Entry(placeholder_text="Write a note about what you learned…")
        entry.connect("activate", self.on_note)
        box.append(entry)
        day = None
        group = None
        for e in self.store.journal_entries(150):
            d = time.strftime("%A %d %B", time.localtime(e["ts"]))
            if d != day:
                day = d
                group = Adw.PreferencesGroup(title=d)
                box.append(group)
            when = time.strftime("%H:%M", time.localtime(e["ts"]))
            kind = {"coach": "Coach", "mission": "Mission", "note": "Note"}.get(e["kind"], e["kind"])
            row = Adw.ActionRow(title=GLib.markup_escape_text(e["text"]), subtitle=f"{when} · {kind}" + (f" · {e['node']}" if e["node"] else ""), title_lines=0)
            group.add(row)
        if day is None:
            box.append(Gtk.Label(label="Nothing yet. The Coach writes here when it helps you; missions write their results; you can write notes.", xalign=0, wrap=True))
        return self.page("Journal", box, "journal")

    def on_note(self, entry):
        textv = entry.get_text().strip()
        if textv:
            self.store.journal("note", None, textv)
            entry.set_text("")
            self.refresh()

    # ---- Posture ------------------------------------------------------------
    def page_posture(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        t = Gtk.Label(label="Posture", xalign=0)
        t.add_css_class("title-1")
        box.append(t)
        lede = Gtk.Label(label="The hardening baseline, checked live. Every control is a lesson and has a documented way to loosen it.", xalign=0, wrap=True)
        lede.add_css_class("pridwen-lede")
        box.append(lede)
        group = Adw.PreferencesGroup(title="Controls")
        placeholder = Gtk.Label(label="Checking…", xalign=0)
        box.append(group)
        box.append(placeholder)

        def work():
            res = posture_evaluate()
            GLib.idle_add(done, res)

        def done(res):
            placeholder.set_visible(False)
            for c in res:
                state = "pass" if c["ok"] else ("later" if c.get("expected_drift") else "drift")
                row = Adw.ActionRow(title=c.get("title", c["id"]), subtitle=("" if c["ok"] else GLib.markup_escape_text(c["message"])) or "", activatable=True)
                chip = Gtk.Label(label={"pass": "Pass", "later": "Planned", "drift": "Drift"}[state])
                chip.add_css_class({"pass": "check-ok", "later": "dim-label", "drift": "check-fail"}[state])
                row.add_suffix(chip)
                row.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
                lid = c.get("lesson")
                if lid:
                    row.connect("activated", lambda _r, lid=lid: self.push(self.page_lesson(lid)))
                group.add(row)
            return False
        threading.Thread(target=work, daemon=True).start()
        return self.page("Posture", box, "posture")


def main(argv):
    return Academy().run(argv)
