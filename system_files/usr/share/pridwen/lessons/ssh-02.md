# Running sshd on purpose

The previous lesson used `ssh` as a client to reach other machines. This one is
about the other direction: letting other machines reach yours. The program that
accepts SSH logins is `sshd`, the SSH daemon, and Pridwen ships it installed but
switched off. A laptop rarely needs to accept logins, and an open port 22 is the
first thing every scanner on every network tries, so the safe default is to
listen for nothing until you decide otherwise.

Turning it on is a deliberate two-step: start the daemon, then open the port in
the firewall. Both are explicit so that accepting logins is always a choice you
made, and turning it off again is just as short. This is the shape of running
any network service on Pridwen, and of the RHCSA "configure a service and make
it reachable" tasks: the service and the firewall are two separate decisions,
and forgetting the second one is the most common reason a service "does not
work".

## Words you'll meet

- **sshd**: the SSH server daemon; it listens on port 22 and starts a shell for whoever proves who they are.
- **daemon**: a program that runs in the background waiting for work, managed by systemd as a unit.
- **`systemctl enable --now`**: start a unit now and also start it at every boot; `disable --now` is the reverse.
- **listening**: a program has a socket open on a port and is waiting for connections.
- **port 22**: the TCP port SSH uses by convention; the firewall service named `ssh` opens it.
- **drop zone**: Pridwen's default firewalld zone, which discards every inbound packet not explicitly allowed.
- **`--permanent`**: a firewall change saved to disk; needs `--reload` to become live.
- **exit status 255**: what `ssh` returns when the connection itself failed, as opposed to the remote command failing.

## How it works

Confirm the starting state. `systemctl status` shows whether a unit is running
and whether it starts at boot.

```
{user}@{host}:~$ systemctl status sshd
○ sshd.service - OpenSSH server daemon
     Loaded: loaded (/usr/lib/systemd/system/sshd.service; disabled; preset: disabled)
     Active: inactive (dead)
```

`Loaded: ... disabled` means it will not start at boot, and `Active: inactive
(dead)` means it is not running now. Try to connect to your own machine; the
name `localhost` always means "this computer".

```
{user}@{host}:~$ ssh localhost
ssh: connect to host localhost port 22: Connection refused
{user}@{host}:~$ echo $?
255
```

`Connection refused` means the kernel answered "nothing is listening here", and
`echo $?` prints the exit status of the last command, 255, which is `ssh`
saying the connection itself failed. That is sshd being off, not a bug. The
Coach prints the same explanation under the failed command.

Step one: start the daemon and enable it. `--now` does both at once.

```
{user}@{host}:~$ sudo systemctl enable --now sshd
Created symlink '/etc/systemd/system/multi-user.target.wants/sshd.service' → '/usr/lib/systemd/system/sshd.service'.
{user}@{host}:~$ ss -tlnp | grep :22
LISTEN 0      128          0.0.0.0:22        0.0.0.0:*
LISTEN 0      128             [::]:22           [::]:*
```

The symlink line is systemd recording that sshd belongs to the set of services
started at boot. `ss -tlnp` (`-t` TCP, `-l` listening, `-n` numeric, `-p`
process) shows two listening sockets on port 22, one for IPv4 (`0.0.0.0`) and
one for IPv6 (`[::]`). Now `ssh localhost` works, because the loopback
interface is always trusted by the firewall.

```
{user}@{host}:~$ ssh localhost
The authenticity of host 'localhost (::1)' can't be established.
ED25519 key fingerprint is SHA256:Q7mR2kLs9vXc3pT1nWyA5bZ0eF8hJ4uD6oGiK2xVtYc.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added 'localhost' (ED25519) to the list of known hosts.
{user}@localhost's password:
Last login: Sun Sep  7 09:40:11 2026
{user}@{host}:~$ exit
logout
Connection to localhost closed.
```

The first connection asks you to accept the host key, your own machine's key,
then asks for your password because you have not installed your key on
yourself. Step two makes it reachable from other machines: the drop zone would
discard their packets even with sshd running.

```
{user}@{host}:~$ sudo firewall-cmd --add-service=ssh --permanent
success
{user}@{host}:~$ sudo firewall-cmd --reload
success
{user}@{host}:~$ sudo firewall-cmd --list-services
ssh
```

`--add-service=ssh` opens 22/tcp; `--permanent` saves it; `--reload` makes the
saved rules live; `--list-services` confirms `ssh` is now allowed. Test from
another machine on the network with `ssh {user}@{host}`, and if that works,
install your key with `ssh-copy-id` as in the previous lesson.

Turning it off is the same two steps in reverse.

```
{user}@{host}:~$ sudo systemctl disable --now sshd
Removed '/etc/systemd/system/multi-user.target.wants/sshd.service'.
{user}@{host}:~$ sudo firewall-cmd --remove-service=ssh --permanent
success
{user}@{host}:~$ sudo firewall-cmd --reload
success
{user}@{host}:~$ ss -tlnp | grep :22
```

The empty result from `ss` means nothing listens on 22 any more. Running a
service you understand, only when you mean to, and closing it when the job is
done, is the habit the whole secure tier is built around.

## When it goes wrong

`ssh: connect to host localhost port 22: Connection refused` after you enabled
sshd means it did not actually start. `systemctl status sshd` shows why, and
`journalctl -u sshd -n 20` shows its last twenty log lines; a broken
configuration file is the usual cause.

`ssh: connect to host {host} port 22: Connection timed out` from another
machine while `ssh localhost` works is the firewall. The daemon listens but the
drop zone discards the packets; run the `--add-service=ssh --permanent` and
`--reload` pair above and check `--list-services`.

`Permission denied (publickey,gssapi-keyex,gssapi-with-mic,password).` means
the connection worked but authentication failed: a wrong password, or the
server allows keys only and yours is not installed. `ssh -v` shows which
methods were tried, and `pridwen why` under the failure names the likely one.

## Try it

1. Type `ssh localhost` and confirm it fails with `Connection refused`; type `echo $?` and expect `255`.
2. Type `sudo systemctl enable --now sshd`, then `ss -tlnp | grep :22` and expect two `LISTEN` lines.
3. Type `ssh localhost`, accept the host key with `yes`, enter your password, and type `exit`.
4. Type `sudo firewall-cmd --add-service=ssh --permanent` then `sudo firewall-cmd --reload`, then `sudo firewall-cmd --list-services` and expect `ssh`.
5. If you have another machine or a Range host, type `ssh {user}@{host}` from it and log in.
6. Type `sudo systemctl disable --now sshd`, `sudo firewall-cmd --remove-service=ssh --permanent`, `sudo firewall-cmd --reload`, and confirm `ss -tlnp | grep :22` prints nothing.

## Remember

- sshd is installed but off; `Connection refused` on `ssh localhost` with exit 255 is that, not a bug.
- On is two steps: `sudo systemctl enable --now sshd`, then `sudo firewall-cmd --add-service=ssh --permanent && sudo firewall-cmd --reload`.
- Off is `disable --now` plus `--remove-service=ssh`; confirm with `ss -tlnp | grep :22`.
