# The journal

Every program on a Linux system writes messages about what it is doing: a
service started, a login succeeded, a disk complained, a network cable was
unplugged. On Pridwen, systemd collects all of those messages into one indexed
store called the **journal**, and `journalctl` is the command that reads it.
The journal replaces the old scatter of text files under `/var/log`; on Pridwen
those classic files mostly do not exist, because no syslog daemon is installed
to write them, and everything is in the one store instead.

Reading the journal is the first thing you do when anything is wrong, and the
first thing an employer expects you to know how to do. A service failed to
start, a laptop will not sleep, a user says "it was fine yesterday": the answer
is in the journal, and the skill is asking it a sharp enough question. This
lesson covers the store itself and the basic views; the next one covers
filtering.

## Words you'll meet

- **journal**: systemd's single log store, binary and indexed, kept under `/var/log/journal/`.
- **journald**: the daemon (`systemd-journald`) that receives messages and writes the journal.
- **`journalctl`**: the command that reads the journal and shows it as text.
- **boot**: one power-on-to-shutdown session; the journal remembers which boot each message belongs to.
- **unit**: a thing systemd manages, usually a service, with a name like `NetworkManager.service`.
- **priority**: how serious a message is, on a scale from `emerg` (0) to `debug` (7); `err` is 3.
- **pager**: the program (`less`) that `journalctl` hands long output to, so you can scroll; `q` leaves it.
- **rotation**: the journal trimming its oldest files automatically when it reaches its size limit.

## How it works

Run bare, `journalctl` shows everything the journal holds, oldest first, inside
the pager. On a system a few weeks old that is tens of thousands of lines, so
the useful views narrow it. `-b` limits to the current boot, and `-p err`
limits to priority `err` and worse.

```
{user}@{host}:~$ journalctl -b -p err
Sep 07 08:41:12 {host} kernel: usb 1-3: device descriptor read/64, error -71
Sep 07 08:41:30 {host} gdm-session-worker[1180]: gkr-pam: unable to locate daemon control file
Sep 07 09:02:55 {host} systemd[1]: Failed to start dnf-makecache.service - dnf makecache.
```

Each line has the same shape: the timestamp, the hostname, the program name with
its process id in brackets, then the message. The first line is the kernel
noticing a flaky USB device; the third is a service that failed to start, which
is exactly the kind of line you go looking for. A normal desktop shows a
handful of these per boot; a page of them is a system worth looking at.

`-r` reverses the order (newest first) and `-n 50` shows only the last fifty
lines. `-f` follows: it prints new messages as they arrive, like `tail -f` for
the whole system, until you press Ctrl-C.

```
{user}@{host}:~$ journalctl -f -u NetworkManager
Sep 07 09:14:02 {host} NetworkManager[912]: <info>  [1757236442.1180] device (wlp2s0): supplicant interface state: completed -> 4way_handshake
Sep 07 09:14:02 {host} NetworkManager[912]: <info>  [1757236442.4451] device (wlp2s0): state change: config -> ip-config
Sep 07 09:14:03 {host} NetworkManager[912]: <info>  [1757236443.0021] device (wlp2s0): state change: ip-config -> activated
```

`-u NetworkManager` limits the output to one unit, the network service, so the
three lines are a Wi-Fi connection coming up, step by step. Leave it running,
turn Wi-Fi off and on, and watch it narrate. Ctrl-C stops the follow; the exit
status is 130, which is bash's way of saying "interrupted", not an error.

Time windows are the other basic filter. `--since` takes a plain-English time.

```
{user}@{host}:~$ journalctl --since "10 min ago" -n 3 --no-pager
Sep 07 09:20:01 {host} systemd[1]: Started run-r4f2.service - /usr/bin/pridwend.
Sep 07 09:20:14 {host} sudo[7710]:    {user} : TTY=pts/0 ; PWD={home} ; USER=root ; COMMAND=/usr/bin/firewall-cmd --list-all
Sep 07 09:20:14 {host} sudo[7710]: pam_unix(sudo:session): session opened for user root(uid=0) by {user}(uid=1000)
```

`--no-pager` prints straight to the terminal instead of opening `less`, which
is what you want when piping into other commands. The middle line is worth
knowing: every `sudo` use is logged here with the terminal (`TTY`), the
directory (`PWD`), and the exact `COMMAND`, which is what the Sudo node meant by
"every use is recorded".

Who can read all this? Members of the `wheel` or `systemd-journal` groups see
the full journal; anyone else sees only messages from their own session. Your
account is in `wheel` (it is the admin account the welcome wizard created), so
you see everything without `sudo`. `-b -1` shows the previous boot, which is how
you read what happened right before a crash or a reboot.

The journal is binary rather than plain text, which is what makes filtering by
unit or priority fast: it is indexed. It also rotates on size automatically, so
it never fills the disk. `--disk-usage` shows how much it is keeping.

```
{user}@{host}:~$ journalctl --disk-usage
Archived and active journals take up 488.0M in the file system.
```

Half a gigabyte is typical after a few weeks. Trimming it (`--vacuum-size`)
writes to `/var/log/journal` and needs `sudo`; reading the size does not.
Everything the rest of this node teaches is a way of asking this one store a
sharper question.

## When it goes wrong

`Hint: You are currently not seeing messages from other users and the system.`
at the top of the output means your account is not in `wheel` or
`systemd-journal`, so you see only your own messages. On Pridwen the wizard's
account is in `wheel`; a second account you added is not until an admin puts
it there.

`No journal files were found.` or `Specifying boot ID or boot offset has no
effect, no persistent journal was found.` means the journal is running in
memory only. Pridwen keeps a persistent journal under `/var/log/journal/`, so
this points at a disk problem worth a look.

`-- No entries --` is not an error: nothing matched your filter. Widen the time
window or drop `-p err`. `pridwen explain journalctl` annotates any flag you
are unsure of, and `pridwen why` under a failed `journalctl` says which of
these it was.

## Try it

1. Type `journalctl -b -p err` and read any errors from this boot; press `q` to leave the pager.
2. Type `journalctl -r -n 20` and confirm the newest line is at the top.
3. Type `journalctl -f`, wait for a few lines to appear, and press Ctrl-C to stop.
4. Type `journalctl --since "1 hour ago" --no-pager | tail` and read the last ten lines of recent activity.
5. Type `journalctl -b -1 -n 5 --no-pager` and read the last five lines of the previous boot.
6. Type `journalctl --disk-usage` and note how much space the journal keeps.

## Remember

- The journal is one indexed store for everything; `journalctl` reads it, and `wheel` members see all of it.
- `-b` this boot, `-p err` errors and worse, `-u name` one service, `-f` follow, `--since "10 min ago"` a window.
- Classic files like `/var/log/messages` do not exist here; their lines are in the journal.
