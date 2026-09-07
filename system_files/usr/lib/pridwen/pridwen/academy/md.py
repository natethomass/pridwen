"""Lesson and brief markdown -> GTK widgets (a small, predictable subset).

Headings, paragraphs, bullet and numbered lists, fenced code blocks, inline
code and bold. Anything else is shown as text.
"""
import re

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402

_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def inline(s):
    """Escape then mark up inline code and bold as Pango."""
    s = GLib.markup_escape_text(s)
    s = _BOLD.sub(r"<b>\1</b>", s)
    s = _CODE.sub(r'<tt><span foreground="#6E9E7A">\1</span></tt>', s)
    return s


def _label(markup, css=None, wrap=True):
    lab = Gtk.Label(xalign=0, wrap=wrap, use_markup=True, selectable=True)
    lab.set_markup(markup)
    lab.set_wrap_mode(2)  # WORD_CHAR
    if css:
        lab.add_css_class(css)
    return lab


def render(md):
    """-> Gtk.Box with the rendered content."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    para, code, in_code = [], [], False

    def flush_para():
        if para:
            box.append(_label(inline(" ".join(para)), "body"))
            para.clear()

    for raw in (md or "").splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            flush_para()
            if in_code:
                lab = _label("<tt>" + GLib.markup_escape_text("\n".join(code)) + "</tt>", "pridwen-code", wrap=False)
                frame = Gtk.ScrolledWindow(child=lab, hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                           vscrollbar_policy=Gtk.PolicyType.NEVER, propagate_natural_height=True)
                frame.add_css_class("card")
                frame.add_css_class("pridwen-codeframe")
                box.append(frame)
                code.clear()
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if not line.strip():
            flush_para()
            continue
        m = re.match(r"^(#+)\s+(.*)$", line)
        if m:
            flush_para()
            level = len(m.group(1))
            box.append(_label(inline(m.group(2)), "title-2" if level == 1 else "title-4"))
            continue
        m = re.match(r"^\s*(\d+)[.)]\s+(.*)$", line)
        if m:
            flush_para()
            row = Gtk.Box(spacing=8)
            row.append(_label(f"<b>{m.group(1)}.</b>", wrap=False))
            row.append(_label(inline(m.group(2)), "body"))
            box.append(row)
            continue
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m:
            flush_para()
            row = Gtk.Box(spacing=8)
            row.append(_label("•", wrap=False))
            row.append(_label(inline(m.group(1)), "body"))
            box.append(row)
            continue
        para.append(line.strip())
    flush_para()
    return box
