# Making scripts trustworthy

A script that works once on your machine is not the same as one you trust in a
timer or hand to a teammate. The gap is closed by checking, by clear failure, and
by not depending on where it happens to run.

`shellcheck` is the single most useful tool here; it reads a script and flags
quoting bugs, unset variables, and portability traps before they bite. It is not
in the base image, so layer it with `rpm-ostree install ShellCheck` or run it in
a Distrobox. Beyond that, make the script report what it did and exit non-zero
when it fails, so a timer or a caller can tell.

```
$ shellcheck deploy.sh
In deploy.sh line 8:
rm -rf $dir/*
       ^--^ SC2086: Double quote to prevent globbing and word splitting.
```

The other half is not assuming a working directory or a PATH. Reference files by
absolute path or compute a base from the script's own location, and call tools by
name knowing they are on PATH. When a script will run unattended, log a line at
the start and end so the journal tells the story later. A trustworthy script is
one whose success and failure are both visible.

## Try it

1. Run `shellcheck` on a script (from a Distrobox if needed) and fix one finding.
2. Add an explicit `exit 1` on a failure path and test that it triggers.
3. Add a `logger` line at the start and find it later with `journalctl`.
4. Change a relative path to an absolute one and explain why it is safer.
