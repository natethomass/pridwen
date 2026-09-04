# Coach and Dispatch (M2)

The Coach is the shell that notices. A hook in bash and zsh sends one line per
command (command text, exit code, duration, working directory, never the
output) to a per-user daemon, `pridwend`. The daemon matches it against a rules
library and, when a rule fires, replies with one line that the shell prints
above the next prompt. Dispatch is the daemon's push side: earned nudges as
GNOME notifications. The pull side is the `pridwen` CLI.

Everything stays on the machine: `~/.local/share/pridwen/pridwen.db` (SQLite).

## Layout

| Path | What |
|---|---|
| `/usr/lib/pridwen/pridwen/` | Python package: `store`, `rules`, `daemon`, `cli`, `explain`, `selinux`, `dispatch`, `text` |
| `/usr/bin/pridwen` | CLI entry point |
| `/usr/libexec/pridwend` | daemon entry point (user service `pridwend.service`) |
| `/usr/libexec/pridwen-coach-send` | C client the hooks call: connect, send, wait ≤250 ms for a reply, print it |
| `/usr/share/pridwen/shell/coach.bash`, `coach.zsh` | the hooks |
| `/usr/share/pridwen/tree.yaml` | skill-tree nodes |
| `/usr/share/pridwen/rules/*.yaml` | Coach rules, one file per node |
| `/usr/share/pridwen/nudges.yaml` | Dispatch rules |
| `/usr/share/pridwen/lessons/<id>.md` | lesson text (`pridwen learn <id>`); Academy renders the same files in M3 |
| `/usr/share/pridwen/explain/<command>.yaml` | curated flag annotations for `pridwen explain` |
| `$XDG_RUNTIME_DIR/pridwen/coach.sock` | the socket |
| `~/.config/pridwen/coach.toml` | user settings (`enabled`, `quiet_until`, `quiet_hours`) |

## Event line (hook → daemon)

One JSON object per line:

```json
{"v":1,"cmd":"cat /etc/shadow","exit":1,"ms":12,"cwd":"/home/nate","shell":"bash","pid":4242}
```

The daemon scrubs anything that looks like a secret before storing
(`password=`, `-p<value>`, `Authorization:`, `token`, `key=`, long base64/hex
runs) and never stores output because it never sees it.

Reply (daemon → hook): zero or more lines of text, already coloured, ending in a
blank line. The client prints whatever arrives within 250 ms. No reply is the
common case.

## Tree

`tree.yaml` lists nodes. Ids are short kebab-case and stable; everything else
keys on them.

```yaml
tiers:
  roots:    [terminal, files, permissions, users]
  operate:  [processes, services, packages, networking, storage, boot]
  secure:   [sudo, selinux, firewall, logging, ssh, hardening]
  automate: [scripting, timers, containers, ansible]
  defend:   [log-analysis, detection, incident-response, forensics]
  attack:   [recon, web, credentials, privesc, persistence]
nodes:
  permissions:
    title: Permissions
    tier: roots
    summary: Who may read, write, and run what, and how to change it.
    requires: [files]
    lessons: [perm-01, perm-02, perm-03]
```

## Rule schema (`rules/<node>.yaml`)

A file is a list of rules. Fields:

```yaml
- id: perm-shadow-denied          # unique, kebab-case, prefixed by node
  node: permissions               # tree node id
  lesson: perm-02                 # lesson id; defaults to the node's first lesson
  when:
    command: '^(sudo\s+)?(cat|less|more|head|tail|vim?|nano)\s+.*(?P<path>/etc/shadow)\b'
    exit: [1, 2]                  # optional; omit = any non-zero; [0] = success only; "any"
    not_sudo: true                # optional: only when the command is not under sudo
    probe: unreadable:{path}      # optional, see Probes
  hint: >-                        # one or two sentences; backticks mark commands
    `/etc/shadow` is readable only by root. It holds password hashes, which is why.
    `ls -l /etc/shadow` shows the owner and mode.
  why: |                          # optional, for `pridwen why`; markdown-ish
    You asked to read a file whose mode is 0000 and owner is root ...
    Ways forward:
      1. `sudo cat /etc/shadow`  read it as root, on purpose
      2. `getent shadow $USER`   the API way, still needs root
  man: [shadow(5), chmod(1)]      # optional references
  cooldown: 3600                  # seconds before the same rule may fire again (default 3600)
  priority: 10                    # higher wins when several rules match (default 0)
```

`command` is a Python regex matched with `re.search` against the scrubbed
command line. Named groups are available as `{name}` in `probe`, `hint`, and
`why`. `{cmd}` is the first word (after `sudo`).

### Probes

Probes make rules precise without seeing output. Each is evaluated by the
daemon in the user's context:

| Probe | True when |
|---|---|
| `unreadable:<path>` | path exists and `access(R_OK)` fails |
| `unwritable:<path>` | path exists and `access(W_OK)` fails |
| `missing:<path>` | path does not exist |
| `exists:<path>` | path exists |
| `is_dir:<path>` | path is a directory |
| `no_command:<name>` | not found on `PATH` |
| `no_unit:<name>` | `systemctl cat <name>` fails (system and user) |
| `ostree` | running on an image-based (bootc) host |
| `selinux_enforcing` | `getenforce` says Enforcing |
| `in_container` | inside a container (`/run/.containerenv` or `/.dockerenv`) |
| `not <probe>` | negation |

A rule with no `exit` matches only failures (exit ≠ 0). Success rules must say
`exit: [0]` or `exit: any`. Rules fire at most once per cooldown, and the
daemon prints at most one hint per command (highest priority, then first
loaded). Rules never fire while the coach is quiet.

## Nudges (`nudges.yaml`)

Dispatch rules count events and send one notification when a threshold is
crossed. Each nudge fires once per install unless `repeat: <seconds>` is set.

```yaml
- id: sudo-ten
  node: sudo
  lesson: sudo-01
  count:
    command: '^sudo\b'
    threshold: 10
  title: Ten sudos in
  body: You've run sudo ten times. Want to see what it actually does?
- id: selinux-first-denial
  node: selinux
  lesson: selinux-01
  event: selinux_denial            # events raised by the daemon itself
  title: SELinux just said no
  body: Something was blocked by SELinux. Want it translated?
- id: bootc-staged
  node: packages
  lesson: pkg-03
  event: bootc_staged
  title: An update is staged
  body: A new Pridwen image is ready for the next boot. See what changed?
```

A nudge that is earned during quiet hours or over the cap is retried on later commands
until it is sent. Notifications carry actions: Learn (`pridwen learn <lesson>` in Academy later,
terminal now), Snooze (a day), Not this again (disables that nudge). Cap: 3 per
day. Quiet hours default 22:00–08:00. `pridwen quiet` silences both Coach and
Dispatch.

## CLI

| Command | Does |
|---|---|
| `pridwen why` | Explains the last failed command: the matching rule's `why`, else a recent SELinux denial translated, else a generic reading of the exit code |
| `pridwen explain <command...>` | Annotates the command word and each flag from `explain/<cmd>.yaml`, falling back to the man page, and names the tree node |
| `pridwen learn [id]` | Prints a lesson; with no id, lists nodes and lessons with what has fired |
| `pridwen why selinux` | Translates the newest SELinux denial (last 24 h) |
| `pridwen quiet [1h\|1d\|forever\|off]` | Silence the coach |
| `pridwen quiet hours off\|HH:MM-HH:MM` | Change or drop Dispatch's quiet hours (default 22:00-08:00) |
| `pridwen status` | Daemon, rules loaded, events stored, quiet state |
| `pridwen dispatch test` | Send a test notification through Dispatch (not counted against the cap) |

## Lessons (`lessons/<id>.md`)

Short markdown with a title line, 150–400 words, ending in "Try it" steps that a
checker can verify later (M3). Ids: `<node-prefix>-NN`, where prefixes are the
node id or its usual short form (`perm`, `svc`, `pkg`, `net`, `proc`, `user`,
`file`, `term`, `store`, `boot`, `sudo`, `selinux`, `fw`, `log`, `ssh`, `hard`,
`script`, `timer`, `ctr`, `ansible`, `logan`, `detect`, `ir`, `forensics`,
`recon`, `web`, `cred`, `privesc`, `persist`).

## Voice

One line, plain English, no exclamation marks, no "oops". Say what the system
did and why, then the smallest next step. Name the man page. Never scold.
