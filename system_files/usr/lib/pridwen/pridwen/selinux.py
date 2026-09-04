"""SELinux denial translation: turn an AVC record into plain English.

Reads recent audit records from the journal (wheel members can) and explains
the most recent denial: who (source context) tried what (permission) on what
(target context and class), and the usual ways forward on Fedora.
"""
import re
import subprocess
import time

AVC_RE = re.compile(
    r"avc:\s+denied\s+\{\s*(?P<perms>[^}]+)\}\s+for\s+(?P<rest>.*)")
KV_RE = re.compile(r'(\w+)=("[^"]*"|\S+)')

TYPE_WORDS = {
    "httpd_t": "the web server (httpd)",
    "sshd_t": "the SSH daemon",
    "init_t": "systemd",
    "unconfined_t": "an unconfined process",
    "container_t": "a container",
    "container_runtime_t": "the container runtime",
    "chronyd_t": "the time daemon",
    "NetworkManager_t": "NetworkManager",
    "systemd_logind_t": "logind",
    "user_home_t": "a file in a home directory",
    "http_port_t": "a web port",
    "unreserved_port_t": "an unreserved port",
    "shadow_t": "the shadow password file",
    "etc_t": "a file in /etc",
    "var_log_t": "a log file",
    "tmp_t": "a temporary file",
    "container_file_t": "a container-labelled file",
    "default_t": "a file with no policy label",
    "admin_home_t": "root's home",
    "home_root_t": "/home itself",
}

CLASS_WORDS = {
    "file": "a file", "dir": "a directory", "lnk_file": "a symlink", "sock_file": "a socket file",
    "tcp_socket": "a TCP socket", "udp_socket": "a UDP socket", "unix_stream_socket": "a Unix socket",
    "process": "a process", "capability": "a kernel capability", "capability2": "a kernel capability",
    "chr_file": "a device", "blk_file": "a block device", "fifo_file": "a pipe", "key": "a kernel key",
}


def _type_of(ctx):
    parts = ctx.strip('"').split(":")
    return parts[2] if len(parts) >= 3 else ctx


def describe(ctx):
    t = _type_of(ctx)
    return TYPE_WORDS.get(t, t.replace("_t", "").replace("_", " "))


def recent_denials(since_seconds=600, limit=5):
    """Newest first. Returns [] when the journal is unreadable."""
    try:
        r = subprocess.run(
            ["journalctl", "-q", "--no-pager", "-o", "cat", "_TRANSPORT=audit", f"--since=-{int(since_seconds)}s"],
            capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return []
    out = []
    for line in r.stdout.splitlines():
        m = AVC_RE.search(line)
        if not m:
            continue
        kv = {k: v.strip('"') for k, v in KV_RE.findall(m.group("rest"))}
        kv["perms"] = m.group("perms").split()
        out.append(kv)
    return list(reversed(out))[:limit]


def translate(d):
    """One AVC dict -> markdown-ish explanation."""
    src, tgt = d.get("scontext", "?"), d.get("tcontext", "?")
    tclass = d.get("tclass", "file")
    perms = ", ".join(d.get("perms", []))
    comm = d.get("comm", "a process")
    name = d.get("name") or d.get("path") or d.get("dest") or ""
    what = CLASS_WORDS.get(tclass, tclass)
    where = f" `{name}`" if name else ""
    lines = [
        "# SELinux said no",
        "",
        f"`{comm}` (running as {describe(src)}, type `{_type_of(src)}`) tried to **{perms}** {what}{where} "
        f"labelled `{_type_of(tgt)}` ({describe(tgt)}). The targeted policy has no rule allowing that, so the kernel refused. "
        "The program usually reports it as Permission denied, which is why it looks like a file-mode problem and isn't.",
        "",
        "Ways forward:",
    ]
    n = 1
    if tclass in ("file", "dir", "lnk_file", "sock_file", "chr_file", "blk_file", "fifo_file"):
        lines.append(f"  {n}. `ls -Z{' ' + name if name else ''}`  see the label. If the file was moved or created somewhere unusual, "
                     "`restorecon -Rv <path>` puts the default label back.")
        n += 1
        if _type_of(tgt) in ("user_home_t", "admin_home_t", "default_t", "tmp_t"):
            lines.append(f"  {n}. Serving files from a home or tmp directory needs a label the service may read, "
                         "e.g. `semanage fcontext -a -t httpd_sys_content_t '/srv/site(/.*)?'` then `restorecon -Rv /srv/site`.")
            n += 1
    if tclass in ("tcp_socket", "udp_socket"):
        lines.append(f"  {n}. Non-standard ports need a port label: `semanage port -l | grep {_type_of(tgt).replace('_t', '')}` "
                     "and `semanage port -a -t http_port_t -p tcp 8081` for example.")
        n += 1
    lines.append(f"  {n}. `sudo ausearch -m AVC -ts recent` shows the raw record; `sudo sealert -a /var/log/audit/audit.log` "
                 "(setroubleshoot) proposes the exact fix, including a boolean if one exists (`getsebool -a | grep httpd`).")
    n += 1
    lines.append(f"  {n}. `setenforce 0` would make it work and teach you nothing. Fix the label or the boolean instead.")
    lines.extend(["", "man: selinux(8), restorecon(8), semanage-fcontext(8), setsebool(8)"])
    return "\n".join(lines)


def latest_explanation(since_seconds=600):
    d = recent_denials(since_seconds, 1)
    if not d:
        return None
    return translate(d[0])


def poll_new(state, since_seconds=30):
    """For the daemon: returns the newest denial not seen before (by raw tuple), else None."""
    for d in recent_denials(since_seconds, 3):
        sig = (d.get("scontext"), d.get("tcontext"), d.get("tclass"), tuple(d.get("perms", [])), d.get("comm"))
        if sig not in state:
            state.add(sig)
            if len(state) > 200:
                state.clear()
            return d
    return None


def enforcing():
    try:
        with open("/sys/fs/selinux/enforce") as f:
            return f.read().strip() == "1"
    except OSError:
        return False


_last_poll = 0.0


def throttle(seconds=20):
    global _last_poll
    now = time.monotonic()
    if now - _last_poll < seconds:
        return False
    _last_poll = now
    return True
