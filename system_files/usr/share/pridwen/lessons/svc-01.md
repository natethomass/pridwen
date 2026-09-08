# Units and systemctl

A service is a program that runs in the background without a window or a
terminal: the thing that keeps the clock right, the one that hands out network
addresses, the login screen. On a modern Fedora system, and so on Pridwen,
services are managed by systemd, the first process to start at boot, which then
starts everything else and keeps watch over it. Each thing systemd manages is
described by a unit file, a short text file that says what to run and when.
`systemctl` is the one command you use to ask systemd about units and to
control them.

This matters because almost every "is it running" and "why did it not come up
after the reboot" question on a Linux machine is answered with `systemctl`. On
Pridwen, reading state never needs root, so you can look at everything from the
first day; only changing it needs `sudo`.

## Words you'll meet

- **service**: a program that runs in the background and is started and watched by systemd rather than by you.
- **systemd**: the service manager; pid 1, the first process, which starts and supervises all the others.
- **unit**: one thing systemd manages, named with a suffix such as `.service`, `.timer`, `.socket`, or `.mount`.
- **unit file**: the text file that describes a unit; what to run, who as, and what it depends on.
- **loaded**: systemd has read the unit file and knows about the unit.
- **active**: the unit is running right now.
- **enabled**: the unit is set to start at boot; the next lesson is about this word.
- **drop-in**: a small extra file that changes a few lines of a shipped unit without replacing it.
- **daemon-reload**: telling systemd to reread all unit files after one changed on disk.

## How it works

`systemctl status name` is the most useful view. Here it asks about chronyd,
the service that keeps the clock synchronised over the network.

```
{user}@{host}:~$ systemctl status chronyd
* chronyd.service - NTP client/server
     Loaded: loaded (/usr/lib/systemd/system/chronyd.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-09-07 09:00:11 UTC; 1h 12min ago
       Docs: man:chronyd(8)
   Main PID: 912 (chronyd)
      Tasks: 1 (limit: 4562)
     Memory: 2.1M
        CPU: 48ms
     CGroup: /system.slice/chronyd.service
             └─912 /usr/sbin/chronyd -F 2

Sep 07 09:00:11 {host} chronyd[912]: chronyd version 4.5 starting
Sep 07 09:00:16 {host} chronyd[912]: Selected source 192.0.2.10
```

Read it top down. The first line is the unit's name and its description. The
Loaded line says systemd found the unit file, where it is, and that it is
`enabled`, meaning set to start at boot. The Active line says whether it is
running right now and since when. Main PID is the process id of the program
itself, the same number `ps` would show. Memory and CPU are what it costs. The
last lines are the most recent entries the unit wrote to the journal, the
system log. A healthy service reads `loaded`, `enabled`, `active (running)`,
and no error lines at the bottom. You gave no suffix, so systemd assumed
`.service`; `chronyd` and `chronyd.service` mean the same thing.

Two list commands show the whole picture. `systemctl list-units` shows what
systemd has loaded right now; `systemctl list-unit-files` shows every unit file
installed and its enabled state, whether or not it is loaded.

```
{user}@{host}:~$ systemctl list-unit-files --type=service | head -n 4
UNIT FILE                              STATE           PRESET
NetworkManager.service                 enabled         enabled
auditd.service                         enabled         enabled
chronyd.service                        enabled         enabled
```

`--type=service` limits the list to services. UNIT FILE is the file name, STATE
is whether it will start at boot, and PRESET is what the distribution wanted
the state to be, so a difference between the two columns means someone changed
it on this machine. `systemctl --failed` lists only units that tried to start
and could not; an empty list is the normal, good result. `pridwen explain
systemctl` annotates any of these flags.

Unit files live in three places, and systemd searches them in this order:
`/etc/systemd/system` for local changes, `/run/systemd/system` for units
created at runtime and lost at reboot, and `/usr/lib/systemd/system` for the
units shipped in the image. A file in an earlier directory hides one with the
same name in a later one. On Pridwen, `/usr` is read-only because it is part of
the container image the system boots from; that is what makes updates and
rollbacks whole and safe. So your changes always go in `/etc`. `systemctl cat
name` prints the unit file systemd actually loaded, with its path on the first
line.

```
{user}@{host}:~$ systemctl cat chronyd | head -n 6
# /usr/lib/systemd/system/chronyd.service
[Unit]
Description=NTP client/server
Documentation=man:chronyd(8) man:chrony.conf(5)
After=network.target nss-lookup.target
Conflicts=systemd-timesyncd.service
```

The comment line is the path. `[Unit]` is the section with the description
and ordering; a `[Service]` section further down says what to run. To change
a shipped unit, do not copy it; run `sudo systemctl edit name`, which opens an
editor on a drop-in file under `/etc/systemd/system/name.service.d/` holding
only the lines you set. If you ever place or edit a unit file by hand, run
`sudo systemctl daemon-reload` so systemd rereads it; until then it keeps
using the old copy in memory.

## When it goes wrong

`Unit foo.service could not be found.` means no file with that name exists in
any of the three directories. Check the spelling, or run `systemctl
list-unit-files | grep -i foo` for near misses. On Pridwen the package that
provides a service may simply not be in the image.

`Failed to start chronyd.service: Interactive authentication required.` means
you tried to change a system unit without root. Reading never needs `sudo`;
starting, stopping, enabling and editing do, so `sudo systemctl start chronyd`.

`Warning: The unit file, source configuration file or drop-ins of foo.service
changed on disk. Run 'systemctl daemon-reload' to reload units.` is systemd
telling you a file changed since it last read it; run `sudo systemctl
daemon-reload`. `pridwen why` explains whichever of these you just saw.

## Try it

1. Run `systemctl status chronyd` and read the Loaded line and the Active line aloud.
2. Run `systemctl --failed` and expect the line `0 loaded units listed`.
3. Run `systemctl list-unit-files --state=enabled | head` and count how many services start at boot.
4. Run `systemctl cat chronyd` and find the path on the first line and the `ExecStart=` line.
5. Run `systemctl status sshd` and notice it is `inactive (dead)` and `disabled`; Pridwen ships with remote login off on purpose.

## Remember

- systemd manages units; `systemctl status name` shows loaded, enabled, active, and the last log lines.
- Reading state needs no root; changing state needs `sudo`.
- Shipped units live in read-only `/usr/lib/systemd/system`; your changes go in `/etc`, and `daemon-reload` makes systemd see them.
