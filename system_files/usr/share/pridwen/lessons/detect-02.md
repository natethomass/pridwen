# Baselines and anomalies

A detection is only as good as the baseline it compares against. To know that
something is abnormal you first have to write down what normal looks like: which
services listen, which units are enabled, which accounts exist, what runs on a
schedule. An anomaly is a departure from that recorded normal. Without the
record, every new listener looks the same as every old one, and you are back to
hoping you happen to notice.

This is how detection works on real fleets, where a tool compares each host to a
golden state and flags the drift. On Pridwen the idea is small enough to do by
hand with `diff`, which is the best way to understand what the big tools do. You
build the baseline on your own host now, and on Rocky 9 Range hosts you own,
arriving in milestone M4, where a scenario will plant the anomaly for your
comparison to catch.

## Words you'll meet

- **baseline**: a saved capture of a system's state taken when it is known to be good.
- **anomaly**: a difference between the current state and the baseline.
- **drift**: the slow accumulation of differences, some legitimate, some not.
- **diff**: the command that prints the lines that differ between two inputs.
- **unit file**: systemd's description of a service or timer; "enabled" means it starts at boot.
- **known good**: a moment when you are confident nothing is wrong, usually right after install or a checked update.

## How it works

Build the baseline from the same commands you would use to investigate, so that
the baseline and the later capture have the same shape and can be compared line
by line. Keep them in one directory.

```
{user}@{host}:~$ mkdir -p {home}/baseline
{user}@{host}:~$ sudo ss -tulnp | sort > {home}/baseline/listeners.txt
{user}@{host}:~$ systemctl list-unit-files --state=enabled | sort > {home}/baseline/enabled.txt
{user}@{host}:~$ getent passwd | sort > {home}/baseline/accounts.txt
{user}@{host}:~$ ls -l {home}/baseline
total 12
-rw-r--r--. 1 {user} {user} 1847 Sep  7 10:20 accounts.txt
-rw-r--r--. 1 {user} {user} 2210 Sep  7 10:20 enabled.txt
-rw-r--r--. 1 {user} {user}  402 Sep  7 10:20 listeners.txt
```

`mkdir -p` creates the directory and does not complain if it exists. `ss -tulnp`
lists listening TCP and UDP sockets with numeric ports and their process; `sudo`
lets it name processes owned by other users. `systemctl list-unit-files
--state=enabled` lists every unit set to start at boot. `getent passwd` prints
every account the system knows, from `/etc/passwd` and any other source. Each is
piped through `sort` before saving, because `diff` compares line by line and
order must be stable. `>` writes the output to a file, replacing it.

Now compare. `diff old new` prints only the lines that differ. A `-` as the
second file name means "read the new side from standard input", so the fresh
capture is compared without saving it.

```
{user}@{host}:~$ sudo ss -tulnp | sort | diff {home}/baseline/listeners.txt -
{user}@{host}:~$
```

No output is the good result: nothing has changed. To see what an anomaly looks
like, create one you control. `python3 -m http.server 4444` starts a small web
server on port 4444 in the foreground, so run it in a second Ptyxis tab and
compare from the first.

```
{user}@{host}:~$ sudo ss -tulnp | sort | diff {home}/baseline/listeners.txt -
3a4
> tcp   LISTEN 0      5          0.0.0.0:4444       0.0.0.0:*    users:(("python3",pid=7420,fd=3))
```

`3a4` is diff's shorthand: after line 3 of the old file, line 4 of the new one
was added. `>` marks a line that exists only in the new capture; `<` would mark
one that vanished. The line itself is a new listener on `0.0.0.0:4444`, every
address, owned by `python3`. On a Range scenario the same line would say
`nc` or a name you do not recognise, and the baseline makes it jump out where
reading `ss` cold would not.

Enabled units and accounts get the same treatment. A new line in `enabled.txt`
is a service someone arranged to start at every boot; a new line in
`accounts.txt` is a new login. Both are the classic footprints of an intruder
settling in, which the Persistence node covers from the other side.

```
{user}@{host}:~$ systemctl list-unit-files --state=enabled | sort | diff {home}/baseline/enabled.txt -
{user}@{host}:~$ getent passwd | sort | diff {home}/baseline/accounts.txt -
```

The judgement is in two places. First, choosing a baseline that is stable enough
to be meaningful but complete enough to matter: `ss` output includes process ids
that change at every boot, so on a busy host you might strip the `users:` column
with `awk` before saving, trading detail for fewer false differences. Second,
refreshing the baseline after legitimate changes. If you enable a backup service
on purpose and never re-capture, every future diff shows that line, you learn to
skip it, and the real anomaly hides in the noise you have trained yourself to
ignore. Recapture after each change you made on purpose, and only then.

## When it goes wrong

`diff: {home}/baseline/listeners.txt: No such file or directory`. The baseline
was never saved, or the path is different. Run the capture line again with `>`
to create it.

A diff full of changed `pid=` numbers after a reboot. The listeners are the same;
their process ids are not. Either accept the noise or capture without the process
column: `sudo ss -tuln | sort` drops `-p` and the `users:` part.

`diff` prints nothing but you know the listener is running. Check that the new
capture used the same flags and the same `sort` as the baseline, and that the
listener bound the port you expect (`sudo ss -tulnp | grep 4444`).

## Try it

1. Create `{home}/baseline` and save sorted captures of `sudo ss -tulnp`, enabled units, and `getent passwd`.
2. Run the listeners diff and confirm it prints nothing.
3. In a second tab, run `python3 -m http.server 4444`. Rerun the diff and read the `>` line: port, address, process.
4. Stop the server with Ctrl-C and rerun the diff; it should be silent again.
5. Start the server again and treat it as a service you added on purpose: recapture with `sudo ss -tulnp | sort > {home}/baseline/listeners.txt`, confirm the diff is silent, then stop the server and watch the diff report a `<` line for the listener that vanished.
6. Write one sentence on what happens to a diff you check weekly against a baseline you never refresh.

## Remember

- A baseline is the same command's output saved when the system is known good.
- `command | sort | diff baseline -` prints only what changed; silence is the good result.
- Refresh the baseline after every change you made on purpose, so real drift stays visible.
