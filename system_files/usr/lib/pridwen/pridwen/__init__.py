"""Pridwen OS teaching layer: Coach (shell hints), Dispatch (nudges), and the CLI.

See /usr/share/doc/pridwen/coach.md for the design and file layout.
"""
import os

SHARE = os.environ.get("PRIDWEN_SHARE", "/usr/share/pridwen")
VERSION_FILE = os.path.join(SHARE, "VERSION")


def version():
    try:
        with open(VERSION_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "dev"


def runtime_dir():
    base = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return os.path.join(base, "pridwen")


def socket_path():
    return os.path.join(runtime_dir(), "coach.sock")


def data_dir():
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "pridwen")


def config_dir():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "pridwen")
