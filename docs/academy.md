# Academy (M3)

Academy is where progress lives. The skill tree is the home screen; every node
is locked, available, in progress, or verified. Verified comes from a checker
that inspected real state on the host (Range targets arrive in M4), never from
a quiz. Tracks are ordered views over the tree.

Academy is a GTK4 + libadwaita app (`/usr/bin/pridwen-academy`, PyGObject) that
reads the same files the Coach uses (`tree.yaml`, `lessons/`) plus missions and
tracks, and the same SQLite store (`~/.local/share/pridwen/pridwen.db`). The
`pridwen` CLI exposes the same engine: `pridwen mission list|show|check`.

## Layout

| Path | What |
|---|---|
| `/usr/share/pridwen/missions/<id>.yaml` | one mission: brief, steps, checks |
| `/usr/share/pridwen/tracks/<id>.yaml` | ordered nodes and missions for a track |
| `/usr/share/pridwen/posture.yaml` | the hardening baseline as data (M6 grows it) |
| `/usr/lib/pridwen/pridwen/missions.py` | loader, checker runner, node/track state |
| `/usr/lib/pridwen/pridwen/posture.py` | baseline checks |
| `/usr/lib/pridwen/pridwen/academy/` | the app (`app.py`, pages) |
| `/usr/share/applications/org.pridwen.Academy.desktop` | launcher |

## Node state

- **locked**: a node in `requires` is not verified (roots are never locked).
- **available**: unlocked, nothing done yet.
- **in progress**: a lesson was opened, a Coach rule fired for it, or a mission was attempted.
- **verified**: every mission with `required: true` for the node is verified
  (a node with no required missions is verified when any of its missions is).

Tracks report `verified / total` nodes and the next thing to do.

## Over-explain, always

The owner's rule for all learning material (full text in `coach.md`, section
"Over-explain, always") applies to missions too:

- `brief`: three or four paragraphs. The situation in the learner's world, what
  they will be able to do afterwards and why it matters on a real job, what
  "done" looks like, and one sentence on how the check works (what file or
  state the checker looks at). Define every term the first time.
- `steps`: what to do, in order, each one saying what result to expect. Steps
  still do not hand over the exact command (the hints and lesson do), but they
  name the tool and the thing it acts on.
- `hints`: at least three, in escalating order: the idea, the shape of the
  command with its flags explained, then the exact command line to type.
- `fail`: what the checker found (`{actual}` where it helps), what it expected,
  and the single command or edit that gets there. Never just "Not yet".

## Mission schema (`missions/<id>.yaml`)

```yaml
id: core-05-permissions            # unique; prefix by track
node: permissions                  # tree node it verifies
title: Lock a file to yourself
track: core                        # primary track; tracks/*.yaml may list it too
required: true                     # counts toward node verification
minutes: 10                        # honest estimate
target: host                       # host (M3) | container | vm (M4)
brief: |                           # markdown; the situation, in the learner's world
  You keep notes in `~/pridwen/notes.txt` ...
steps:                             # what to do, not how (the lesson covers how)
  - Create the directory and file.
  - Make the file readable and writable by you only.
hints:                             # revealed one at a time on request
  - "`chmod` takes an octal mode; `ls -l` shows the result."
checks:                            # all must pass; run as the learner, no sudo
  - id: file-exists
    type: path_exists
    path: "{home}/pridwen/notes.txt"
    fail: "The file `~/pridwen/notes.txt` is not there yet."
  - id: mode
    type: path_mode
    path: "{home}/pridwen/notes.txt"
    mode: "0600"
    fail: "The mode is {actual}; it should be 0600 (owner read and write only)."
cleanup: |                         # optional shell to reset the mission
  rm -rf ~/pridwen
```

### Check types

All run as the learner, in their session, with `{home}`, `{user}`, `{host}`
filled in. A check may set `sudo: true`; those run through `pkexec` only when
the learner presses Check and confirms, and they are the exception.

| type | fields | passes when |
|---|---|---|
| `path_exists` | `path` | the path exists |
| `path_missing` | `path` | the path does not exist |
| `path_mode` | `path`, `mode` (octal string) | permission bits equal `mode` |
| `path_owner` | `path`, `owner` (user), optional `group` | owner (and group) match |
| `path_contains` | `path`, `regex` | file text matches the regex |
| `path_type` | `path`, `kind` (file, dir, symlink) | it is that kind |
| `cmd_exit` | `cmd` (argv list or string), `exit` (default 0) | exit status matches |
| `cmd_output` | `cmd`, `regex` | stdout matches the regex |
| `unit_active` | `unit`, optional `scope: user` | `systemctl is-active` says active |
| `unit_enabled` | `unit`, optional `scope: user` | `systemctl is-enabled` says enabled |
| `unit_inactive` | `unit`, optional `scope: user` | not active |
| `user_exists` | `user` | `getent passwd` finds it |
| `group_member` | `user`, `group` | the user is in the group |
| `sysctl` | `key`, `value` | `/proc/sys` value equals |
| `selinux` | `mode` (enforcing, permissive) | `getenforce` matches |
| `firewalld_zone` | `zone` | default zone equals |
| `bootc_rollback` | | `bootc status` shows a rollback deployment |
| `journal_has` | `regex`, optional `unit`, `since` (e.g. `-1h`) | the journal matches |
| `env_shell` | `regex` | `$SHELL` matches |

`fail` messages may use `{actual}` where the check produces one. A check's
`sudo: true` is honoured only for `cmd_exit`, `cmd_output`, `path_*`,
`journal_has`.

## Track schema (`tracks/<id>.yaml`)

```yaml
id: core
title: Pridwen Core
lede: Daily-drive Linux and fix it when it breaks.
maps_to: Living on Pridwen without a safety net
nodes: [terminal, files, permissions, users, processes, services, packages,
        networking, storage, boot, sudo, firewall, selinux, logging, ssh,
        containers, scripting, timers]
missions: [core-01-terminal, core-02-files, ...]   # in order; 20 for Core
capstone: core-20-fix-this-host
```

## Journal

Entries come from three places, all in the store's `journal` table:
Coach firings (rule id, hint, command), mission results (pass/fail, which
check), and notes the learner writes in Academy. Academy shows them newest
first, grouped by day; `pridwen journal` prints the same.

## Posture panel (`posture.yaml`)

A list of controls, each with a check from the table above, a lesson, and the
documented way to loosen it. M3 ships the panel and ten controls read-only;
M6 makes them the source of truth for the build.

```yaml
- id: selinux-enforcing
  title: SELinux enforcing
  lesson: selinux-01
  check: {type: selinux, mode: enforcing}
  loosen: "`sudo setenforce 0` until reboot; `pridwen learn selinux-02` first."
```

## App structure

`Adw.ApplicationWindow` with an `Adw.NavigationSplitView`: sidebar (Tree,
Tracks, Journal, Posture) and a content `Adw.NavigationView`.

- **Tree**: one section per tier, node cards with a state dot (sage verified,
  slate in progress, cream available, grey locked) and the count of missions.
- **Node**: summary, lessons (rendered markdown), missions with state, the Coach
  hints that fired here.
- **Mission**: brief, steps, hints (reveal one at a time), a Check button that
  runs the checks and lists each result, Reset (runs `cleanup`).
- **Track**: progress bar, ordered missions, "next up".
- **Journal**: entries by day, a note entry at the top.
- **Posture**: controls with pass/drift chips and the loosen text.

Cream Glass: follows the system light/dark preference through libadwaita;
accent slate; verified sage; drift clay. No custom CSS beyond a few classes.

## CLI

| Command | Does |
|---|---|
| `pridwen mission list [track]` | missions with state |
| `pridwen mission show <id>` | brief, steps, checks |
| `pridwen mission check <id>` | run the checks, print each result, record the outcome |
| `pridwen mission reset <id>` | run `cleanup` |
| `pridwen track [id]` | track progress |
| `pridwen journal [note ...]` | print the journal or add a note |
| `pridwen posture` | the baseline with pass/drift per control |
