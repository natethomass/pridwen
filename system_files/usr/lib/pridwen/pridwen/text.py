"""Terminal text: the Coach voice rendered in Cream Glass colours.

Hints are one paragraph with a mark in front; `why` and lessons are a small
markdown subset (headings, code spans, fenced blocks, numbered lists).
"""
import os
import re
import shutil
import textwrap

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
SLATE = "\033[38;2;143;176;204m"
SAGE = "\033[38;2;143;191;155m"
CLAY = "\033[38;2;217;148;111m"
CREAM = "\033[38;2;236;230;218m"
GREY = "\033[38;2;140;135;125m"

MARK = "◆ pridwen"
INDENT = "   "

_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")


def colour_enabled():
    return os.environ.get("NO_COLOR") is None and os.environ.get("TERM", "dumb") != "dumb"


def width(default=96):
    try:
        return max(60, min(shutil.get_terminal_size((default, 24)).columns, 120))
    except (ValueError, OSError):
        return default


def code_spans(s, colour=SAGE, use_colour=True):
    if not use_colour:
        return _BOLD.sub(r"\1", _CODE.sub(r"\1", s))
    s = _BOLD.sub(lambda m: f"{BOLD}{m.group(1)}{RESET}", s)
    return _CODE.sub(lambda m: f"{colour}{m.group(1)}{RESET}", s)


def _visible_len(s):
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


def wrap_coloured(text, cols, first_prefix, next_prefix):
    """Wrap on visible width while keeping ANSI escapes intact."""
    words = text.split()
    lines, cur, cur_len = [], first_prefix, _visible_len(first_prefix)
    for w in words:
        wl = _visible_len(w)
        if cur_len + 1 + wl > cols and cur_len > _visible_len(next_prefix):
            lines.append(cur.rstrip())
            cur, cur_len = next_prefix + w, _visible_len(next_prefix) + wl
        else:
            sep = "" if cur in (first_prefix, next_prefix) else " "
            cur += sep + w
            cur_len += (1 if sep else 0) + wl
    lines.append(cur.rstrip())
    return "\n".join(lines)


def hint(text, lesson=None, cols=None, use_colour=None):
    """The one-liner the shell prints after a command."""
    use_colour = colour_enabled() if use_colour is None else use_colour
    cols = cols or width()
    mark = f"{SLATE}{MARK}{RESET}" if use_colour else MARK
    body = code_spans(" ".join(text.split()), use_colour=use_colour)
    tail = ""
    if lesson:
        tail = f"  {DIM}Lesson: {lesson} · pridwen learn {lesson}{RESET}" if use_colour else f"  Lesson: {lesson} · pridwen learn {lesson}"
    return wrap_coloured(body + tail, cols, mark + "  ", INDENT)


def render(md, cols=None, use_colour=None):
    """Small markdown subset for `why` and lessons."""
    use_colour = colour_enabled() if use_colour is None else use_colour
    cols = cols or width()
    out, in_code = [], False
    for raw in md.splitlines():
        line = raw.rstrip("\n")
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            out.append(f"{INDENT}{SAGE}{line}{RESET}" if use_colour else f"{INDENT}{line}")
            continue
        if not line.strip():
            out.append("")
            continue
        m = re.match(r"^(#+)\s+(.*)$", line)
        if m:
            title = m.group(2)
            if use_colour:
                out.append(f"{BOLD}{CREAM}{code_spans(title, colour=SAGE + BOLD, use_colour=True)}{RESET}")
            else:
                out.append(code_spans(title, use_colour=False).upper())
            continue
        m = re.match(r"^(\s*)(\d+[.)]|[-*])\s+(.*)$", line)
        if m:
            lead, bullet, rest = m.groups()
            bullet = bullet if bullet[0].isdigit() else "•"
            body = code_spans(rest, use_colour=use_colour)
            out.append(wrap_coloured(body, cols, f"{lead}{INDENT}{bullet} ", f"{lead}{INDENT}  "))
            continue
        out.append(wrap_coloured(code_spans(line.strip(), use_colour=use_colour), cols, INDENT, INDENT))
    return "\n".join(out)


def para(text, cols=None):
    return textwrap.fill(" ".join(text.split()), width=cols or width(), initial_indent=INDENT, subsequent_indent=INDENT)
