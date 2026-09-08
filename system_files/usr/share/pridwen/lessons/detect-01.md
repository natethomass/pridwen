# Watching for change

Detection is noticing something before you would have stumbled on it. Log
analysis, the node before this one, answers questions you think to ask.
Detection turns one of those questions into a watch that answers itself, so the
system tells you when a specific, security-relevant thing happens instead of
waiting for you to go looking. The first kind of watch is for change in things
that should be stable.

On Pridwen the base image cannot change between boots, because `/usr` is
read-only and comes from a signed container image. That narrows the job. The
places worth watching are `/etc` (configuration), `/var` (data that persists),
user accounts, and what listens on the network. This lesson uses the audit
subsystem on your own host, and later on Rocky 9 Range hosts you own, arriving
in milestone M4, where a scenario will trip the watches you set.

## Words you'll meet

- **audit subsystem**: a part of the kernel that records security-relevant events; `auditd` is the daemon that writes them to `/var/log/audit/audit.log`.
- **watch**: an audit rule that says "record every access of this path".
- **key**: a short label you attach to a rule so you can search for its records later.
- **auditctl**: the tool that loads rules into the running kernel; they last until reboot.
- **rules.d**: the directory `/etc/audit/rules.d/`, whose files are loaded at boot to make rules permanent.
- **listener**: a program waiting for connections on a port; `ss` lists them.

## How it works

Start with the current audit rules. `auditctl -l` (list) prints what is loaded.
Rules are kernel state, so reading and changing them needs root, and `sudo` is
required.

```
{user}@{host}:~$ sudo auditctl -l
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d -p wa -k sudoers
-a always,exit -F arch=b64 -S execve -F auid>=1000 -F auid!=-1 -k exec
```

Pridwen ships a small set of rules as part of its hardening baseline; the exact
list on your host may differ. Reading the shape: `-w path` is a watch on a file
or directory. `-p wa` is the permissions to record, `w` for write and `a` for
attribute change (owner, mode, timestamps); `r` and `x` exist too. `-k name` is
the key. The third rule is a syscall rule rather than a watch and records every
program run by a real user, which is what fed the `aureport -x` summary in the
Log analysis node.

Add a watch on `/etc/passwd`, the file that lists every account.

```
{user}@{host}:~$ sudo auditctl -w /etc/passwd -p wa -k passwd_changes
{user}@{host}:~$ sudo auditctl -l | grep passwd
-w /etc/passwd -p wa -k passwd_changes
```

No output from the first command means it loaded. The second confirms it. Now
trip it. `touch` updates a file's timestamps, which counts as an attribute
change, so it is a safe way to trigger the watch without editing anything.

```
{user}@{host}:~$ sudo touch /etc/passwd
{user}@{host}:~$ sudo ausearch -k passwd_changes -ts today -i | grep -E '^type=(SYSCALL|PATH)'
type=SYSCALL msg=audit(09/07/2026 10:02:17.441:520) : arch=x86_64 syscall=utimensat success=yes exit=0 ... uid=root auid={user} ses=3 comm=touch exe=/usr/bin/touch key=passwd_changes
type=PATH msg=audit(09/07/2026 10:02:17.441:520) : item=0 name=/etc/passwd inode=262401 mode=file,644 ouid=root ogid=root ...
```

`ausearch -k` (key) pulls only records tagged `passwd_changes`, `-ts today`
bounds the time, and `-i` interprets numbers as names. Each event is several
records sharing one serial number, here `520`. The `SYSCALL` record says which
system call (`utimensat`, the one `touch` uses), whether it succeeded, who
did it (`auid` is the account that logged in, which survives `sudo`), and which
program. The `PATH` record names the file. A normal day has no records under this
key at all; one appearing is the detection.

Rules loaded with `auditctl` vanish at reboot. To keep one, write it to a file in
`/etc/audit/rules.d/` and `auditd` loads it at boot. `/etc` survives `bootc
upgrade` through a three-way merge, so the file persists across image updates.

```
{user}@{host}:~$ echo '-w /etc/passwd -p wa -k passwd_changes' | sudo tee /etc/audit/rules.d/50-passwd.rules
-w /etc/passwd -p wa -k passwd_changes
```

`tee` writes its input to the named file and echoes it back, and `sudo tee` is
how you write a root-owned file from a pipeline. The other stable thing to watch
is the network. `ss -tulnp` lists TCP (`-t`) and UDP (`-u`) sockets that are
listening (`-l`), with numeric ports (`-n`) and the owning process (`-p`, which
needs `sudo` to see other users' processes). Capture it now, and a later capture
compared against it shows any new listener; the next lesson makes that comparison
systematic.

```
{user}@{host}:~$ sudo ss -tulnp
Netid State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
udp   UNCONN 0      0          127.0.0.54:53         0.0.0.0:*    users:(("systemd-resolve",pid=901,fd=17))
tcp   LISTEN 0      4096       127.0.0.1:631        0.0.0.0:*    users:(("cupsd",pid=1210,fd=7))
```

Two listeners, both bound to `127.0.0.1`, meaning reachable only from this
machine: the DNS stub and the printing service. Nothing on `0.0.0.0` (all
addresses) is the normal picture for a Pridwen desktop with `sshd` off.

## When it goes wrong

`You must be root to run this program.` from `auditctl`. Audit rules are kernel
state, so they need root by design. Prefix `sudo`; `pridwen why` says the same.

`<no matches>` from `ausearch -k`. Either the rule is not loaded (check `sudo
auditctl -l`), nothing has touched the file since you added it, or the key is
spelled differently from the rule. Keys are exact.

`Error sending add rule data request (Rule exists)`. The rule is already loaded,
usually because you ran the command twice or a `rules.d` file already has it.
Nothing is wrong; `auditctl -l` will show it once.

## Try it

1. Run `sudo auditctl -l` and read one watch rule back: path, permissions, key.
2. Add `sudo auditctl -w /etc/passwd -p wa -k passwd_changes` and confirm it with `sudo auditctl -l | grep passwd`.
3. Run `sudo touch /etc/passwd`, then `sudo ausearch -k passwd_changes -ts today -i` and find the `comm=touch` record.
4. Capture `sudo ss -tulnp > {home}/pridwen/listeners-before.txt`.
5. Start a listener you control with `python3 -m http.server 8080 --bind 127.0.0.1` in a second Ptyxis tab, capture `sudo ss -tulnp` again, and spot the new line on port 8080. Stop it with Ctrl-C.
6. Write one sentence on why an immutable `/usr` means you do not need to watch it.

## Remember

- `auditctl -w path -p wa -k key` records every write and attribute change to a path, tagged with a key.
- `ausearch -k key -ts today -i` finds the records; a normal day has none.
- Watch what can change on Pridwen, which is `/etc`, `/var`, accounts, and listeners, not the read-only `/usr`.
