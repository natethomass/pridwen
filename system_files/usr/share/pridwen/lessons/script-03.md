# Making scripts trustworthy

A script that worked once on your machine, run by you, from your home directory, is not the same thing as a script you can hand to a systemd timer or a teammate. Those run it unattended, from a different directory, with a different set of environment variables, and nobody is watching the screen. A trustworthy script is one that has been checked by a tool, reports what it did, and does not depend on where it happens to run.

On a job, the difference shows up at three in the morning when a backup silently did nothing for a month. On Pridwen you will put scripts under timers in the next node, so this is the moment to make them honest. You already know the safety line `set -euo pipefail` and that `$?` is the exit status; this lesson adds checking, logging, and paths.

## Words you'll meet

- **shellcheck**: a program that reads a script and points out quoting bugs, unset variables, and constructs that behave differently across shells.
- **linter**: the general name for a tool like shellcheck that reads code and reports likely mistakes without running it.
- **Distrobox**: a container that shares your home directory and lets you install packages with a normal package manager, used on Pridwen for tools that are not in the image.
- **layering**: adding a package to the immutable image with `rpm-ostree install`; it works but slows every update, so Pridwen avoids it.
- **journal**: the system log kept by systemd, read with `journalctl`.
- **logger**: a command that writes one line into the journal.
- **working directory**: the directory a program is standing in when it runs; relative paths are read from there.
- **absolute path**: a path that starts at `/`, so it means the same thing from any working directory.

## How it works

Start with checking. shellcheck is not in the Pridwen image, and the right place for a development tool is a Distrobox, where the box's own `dnf` works normally and nothing touches the host. Layering with `rpm-ostree install ShellCheck` also works, but every layered package makes `bootc upgrade` slower, so keep that for things the host itself must have.

```
{user}@{host}:~$ distrobox enter dev
{user}@dev:~$ sudo dnf install -y ShellCheck
{user}@dev:~$ shellcheck deploy.sh

In deploy.sh line 8:
rm -rf $dir/*
       ^--^ SC2086: Double quote to prevent globbing and word splitting.

For more information:
  https://www.shellcheck.net/wiki/SC2086 -- Double quote to prevent globbing ...
{user}@dev:~$ exit
```

Because a Distrobox shares your home directory, `deploy.sh` is the same file inside and outside the box. shellcheck names the file and line, draws a caret under the exact text, and gives a code, `SC2086`, that you can look up. This one is the bug from the previous lesson: if `$dir` is empty, `rm -rf $dir/*` becomes `rm -rf /*`. The fix is `rm -rf "${dir:?}"/*`, where `:?` makes the script stop with a message if `dir` is unset or empty. Run shellcheck until it prints nothing; silence is the pass mark.

Next, reporting. A script that runs from a timer has no screen. It should say when it started and how it ended, in the place a later reader will look, which is the journal.

```
{user}@{host}:~$ cat > {home}/.local/bin/backup <<'EOF'
#!/usr/bin/bash
set -euo pipefail
base="$(dirname "$(readlink -f "$0")")"
logger -t backup "start from $base"
if ! rsync -a "$HOME/Documents/" "$HOME/backup/Documents/"; then
    logger -t backup "rsync failed"
    exit 1
fi
logger -t backup "done"
EOF
{user}@{host}:~$ chmod +x {home}/.local/bin/backup
{user}@{host}:~$ backup
{user}@{host}:~$ journalctl -t backup --since -5min
Sep 07 09:40:12 {host} backup[4123]: start from {home}/.local/bin
Sep 07 09:40:12 {host} backup[4127]: done
```

`logger -t backup` writes a line with the tag `backup` (`-t` sets the tag), and `journalctl -t backup` reads back only lines with that tag; `--since -5min` limits it to the last five minutes. Each journal line shows the time, the host, the tag with the process id in brackets, and the message. The `if ! rsync ...` shape runs the copy and, if it fails, logs why and exits with `1`, so a timer can see the failure as well as a person. `rsync -a` copies a directory tree keeping permissions and times (`-a` is archive mode).

The third line is the path trick. `$0` is the script's own name as it was invoked, `readlink -f` turns that into an absolute path, and `dirname` strips the file name, leaving the directory the script lives in. Files the script needs can then be named as `"$base/config"` and found from any working directory. The other habit is calling tools by bare name, `rsync` not `./rsync`, and trusting PATH, which systemd sets to the standard system directories for a unit.

## When it goes wrong

`bash: shellcheck: command not found` is exit 127 on the host: the tool is not in the image. Enter a Distrobox and install it there, or run it from the box with `distrobox enter dev -- shellcheck deploy.sh` (everything after `--` runs inside the box).

`rsync: change_dir "/Documents" failed: No such file or directory` in the journal means `$HOME` was empty when the script ran. A timer's environment is not your login shell's; either set `HOME` in the unit, or compute paths from `$base` and from `{home}` written out in full.

A journal with a `start` line and no `done` line is the script telling you it failed between them. `journalctl --user -u backup.service` shows the exit status when it ran under systemd, and `pridwen why` explains the last failure you saw at the prompt.

## Try it

1. Enter a Distrobox with `distrobox enter dev` (create one first with `distrobox create -n dev -i fedora:43` if you have not), install ShellCheck, and run `shellcheck` on `greet.sh` from the previous lesson. Expect no output if the script is clean.
2. Add a line `echo $name` without quotes, run shellcheck again, and read the `SC2086` finding. Fix it and re-run until silent.
3. Create the `backup` script above, make it executable, and run it. Expect no output on screen.
4. Run `journalctl -t backup --since -5min` and expect the `start` and `done` lines.
5. Change the source directory to one that does not exist, run again, and expect `rsync failed` in the journal and `echo $?` to print `1`.
6. Run `cd /tmp` then `backup` and confirm from the journal that `$base` still points at `{home}/.local/bin`.

## Remember

- Run shellcheck from a Distrobox until it prints nothing; every finding has a code you can look up.
- Log a start line and an end line with `logger -t tag`, and exit non-zero on failure so a timer can tell.
- Never assume a working directory or your own environment; compute paths from the script's own location.
