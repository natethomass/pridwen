# Audit and the old files

The journal holds most of what the system says about itself, but two other
places matter, and knowing which record lives where saves hours. The first is
the **audit log**, written by a daemon called auditd, which records
security-relevant events at the kernel level: every sudo command, every login,
every SELinux denial, every change to a watched file. The second is the classic
set of text files under `/var/log`, which on Pridwen exist only if some program
writes them directly, and most do not.

On a job, the audit log is where you go for a security question that the
journal answers too vaguely: who ran what as root, and when; which process was
denied by SELinux and on which file. It is also what compliance checks read.
And the old files matter because every tutorial ever written points at them,
so you need to know what replaced each one on a systemd system.

## Words you'll meet

- **auditd**: the audit daemon; it receives event records from the kernel and writes them to disk.
- **audit log**: `/var/log/audit/audit.log`, root-only, one record per line in a `key=value` format.
- **`ausearch`**: queries the audit log by type, time, user, or key.
- **`aureport`**: summarises the audit log into counts and tables.
- **`-m`**: the `ausearch` flag for message type; `USER_CMD` is a sudo command, `LOGIN` a login, `avc` an SELinux denial.
- **`-ts`**: time start; `today`, `recent` (ten minutes), `boot`, or a date and time.
- **`-i`**: interpret; turn numeric ids and timestamps into names and dates.
- **syslog**: the old logging protocol and the daemons (`rsyslog`) that wrote `/var/log/messages`; not installed on Pridwen.
- **wtmp**: the old binary login-history file; replaced by `wtmpdb` and `systemd-logind`.

## How it works

The audit log is root-only, so every `ausearch` needs `sudo`. Ask for commands
run under sudo since midnight, interpreted.

```
{user}@{host}:~$ sudo ausearch -m USER_CMD -ts today -i | tail -4
----
type=USER_CMD msg=audit(09/07/2026 09:20:14.101:2917) : pid=7710 uid={user} auid={user} ses=3 subj=unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023 msg='cwd={home} cmd=/usr/bin/firewall-cmd --list-all exe=/usr/bin/sudo terminal=pts/0 res=success'
```

Records are separated by `----`. Read the fields: `type=USER_CMD` is a command
run through sudo; the timestamp is inside `audit(...)`; `uid` and `auid` are
the user who typed it (`auid`, the audit user id, survives `su` and `sudo`, so
it always names the person who logged in); `cwd` is the directory they were in;
`cmd` is the command; `res=success` means sudo allowed it. Without `-i` the
`cmd` field is hex-encoded, which is why `-i` is worth typing.

`-m LOGIN` shows logins, and `-m avc` shows SELinux denials, which the SELinux
node reads in detail. `aureport --summary` gives the counts.

```
{user}@{host}:~$ sudo aureport --summary
Summary Report
======================
Range of time in logs: 09/01/2026 07:12:44.207 - 09/07/2026 09:20:14.101
Selected time for report: 09/01/2026 07:12:44 - 09/07/2026 09:20:14.101
Number of changes in configuration: 14
Number of changes to accounts, groups, or roles: 0
Number of logins: 6
Number of failed logins: 0
Number of authentications: 41
Number of failed authentications: 2
Number of users: 2
Number of terminals: 4
Number of host names: 1
Number of executables: 9
Number of commands: 7
Number of files: 0
Number of AVC's: 0
Number of MAC events: 6
Number of failed syscalls: 0
Number of anomaly events: 0
Number of responses to anomaly events: 0
Number of crypto events: 0
Number of integrity events: 0
Number of virus events: 0
Number of keys: 0
Number of process IDs: 38
Number of events: 512
```

The lines worth a glance each week: `failed logins`, `failed authentications`
(a mistyped sudo password counts), and `AVC's` (SELinux denials). Zero AVCs
means SELinux blocked nothing. `aureport -au` gives the authentication table
and `aureport -l` the login table when a count needs names.

Now the old files. Muscle memory from other systems points at
`/var/log/messages`, `/var/log/secure`, `/var/log/auth.log`, `/var/log/syslog`.
On Pridwen they are not there.

```
{user}@{host}:~$ ls /var/log/messages /var/log/secure
ls: cannot access '/var/log/messages': No such file or directory
ls: cannot access '/var/log/secure': No such file or directory
{user}@{host}:~$ ls /var/log
audit  journal  private  README
```

They were written by a syslog daemon, `rsyslog`, which Pridwen does not ship.
Their contents are in the journal. What `/var/log/messages` held is
`journalctl`; the kernel lines are `journalctl -k` (`-k` is kernel messages
only, the same as `dmesg`, which is root-only here); what `/var/log/secure`
held is `journalctl _COMM=sudo` for the sudo lines and `journalctl -u sshd` for
the ssh daemon. `/var/log/README` says the same in its own words.

```
{user}@{host}:~$ journalctl -k -n 3 --no-pager
Sep 07 08:41:12 {host} kernel: usb 1-3: new high-speed USB device number 4 using xhci_hcd
Sep 07 08:41:12 {host} kernel: usb 1-3: device descriptor read/64, error -71
Sep 07 08:41:13 {host} kernel: usb 1-3: New USB device found, idVendor=0781, idProduct=5591
```

Three kernel lines: a USB stick arriving, a read error, then success. Login
history, once in `/var/log/wtmp` and read with `last`, now comes from `wtmpdb`
and `systemd-logind`.

```
{user}@{host}:~$ wtmpdb last -n 3
{user}    tty2         pridwen          Sun Sep  7 07:58   still logged in
reboot    system boot  6.16.5-200.fc43  Sun Sep  7 07:57   still running
{user}    tty2         pridwen          Sat Sep  6 18:02 - 22:40  (04:38)
```

Each line is a user, the terminal they logged in on (`tty2` is the graphical
session), where from, and the times. `journalctl -u systemd-logind` shows the
same sessions as they opened and closed. Knowing where each kind of record
actually lives saves a lot of `cat`-ing files that were never written.

## When it goes wrong

`cat: /var/log/secure: No such file or directory` is the old-file reflex. The
lines are in the journal: `journalctl _COMM=sudo` and `journalctl -u sshd`.
The Coach says this under the failed command, and `pridwen why` repeats the
mapping.

`Error opening /var/log/audit/audit.log (Permission denied)` means `ausearch`
or `cat` ran without `sudo`; the audit log is root-only because it is the
record an intruder would most like to edit. Put `sudo` in front and use
`ausearch` rather than `cat`, since the raw file is hex-encoded in places.

`dmesg: read kernel buffer failed: Operation not permitted` means the kernel
ring buffer is restricted to root on Pridwen (`kernel.dmesg_restrict=1`, one
of the hardening sysctls). `journalctl -k` shows the same messages to `wheel`
members, or `sudo dmesg -T` prints them with readable timestamps.

## Try it

1. Type `sudo ausearch -m USER_CMD -ts today -i | tail -4` and read the `cmd=` and `auid=` fields of your most recent sudo command.
2. Type `sudo aureport --summary` and find the `failed logins`, `failed authentications`, and `AVC's` lines.
3. Type `ls /var/log/secure` and confirm it is absent, then type `journalctl _COMM=sudo --since today --no-pager | tail -3` to find the same content.
4. Type `journalctl -k -n 10 --no-pager` and read ten kernel messages.
5. Type `wtmpdb last -n 5` and read your recent logins and reboots.
6. Type `sudo ausearch -m LOGIN -ts today -i | tail -3` and compare it with the `wtmpdb` output.

## Remember

- The audit log is root-only; `sudo ausearch -m USER_CMD -ts today -i` reads sudo commands, `-m avc` denials, `-m LOGIN` logins, and `aureport --summary` counts them.
- `/var/log/messages` and `/var/log/secure` are not written here; the journal has their lines (`journalctl`, `-k`, `_COMM=sudo`, `-u sshd`).
- Login history is `wtmpdb last`, not `/var/log/wtmp`.
