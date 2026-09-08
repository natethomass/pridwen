# Names, time, and accounts

The last part of the baseline is plumbing: turning a name into an address, keeping the clock right, recording what happened, and refusing a guessed password. None of these is dramatic on its own. Each one, though, is something the other controls lean on. A firewall rule is only as good as the name lookup behind it, a log is only trustworthy if its timestamps are, and a strong password does nothing if someone can guess at it all night.

On a job these four are the first things a checklist asks about, and the answers have to come from commands, not assumptions. This lesson shows the command for each, what a healthy answer looks like, and what to do when an account locks itself. You have used `sudo` before; two of the commands here need it because they touch security state for every user on the machine.

## Words you'll meet

- **DNS**: the system that turns a name like `flathub.org` into the address the network needs.
- **DNS over TLS**: sending those lookups inside an encrypted connection, so nobody on the network can read or alter them.
- **systemd-resolved**: the service on Pridwen that does name lookups for every program.
- **NTP**: the network time protocol, how a machine keeps its clock matched to trusted time servers.
- **chrony**: the program on Pridwen that speaks NTP and adjusts the clock gently.
- **auditd**: the audit daemon, which records security-relevant events (logins, sudo, changes to protected files) in its own log.
- **pam_faillock**: the login module that counts failed passwords and locks the account for a while after too many.
- **pwquality**: the rules a new password must meet, such as length and mixed characters.

## How it works

Start with names. `resolvectl` is the command that talks to systemd-resolved, and `status` prints what it is doing for each network link.

```
{user}@{host}:~$ resolvectl status | grep -i tls
       Protocols: -LLMNR -mDNS +DNSOverTLS DNSSEC=no/unsupported
       Protocols: +DefaultRoute -LLMNR -mDNS +DNSOverTLS DNSSEC=no/unsupported
```

`grep -i tls` keeps only the lines containing "tls" (`-i` ignores case). Each `Protocols` line describes one link; a `+` before a name means on and a `-` means off. `+DNSOverTLS` is the answer you want: lookups leave this machine encrypted. Pridwen sets this because a coffee-shop network can otherwise see every site you look up and, worse, hand back a wrong address.

Next the clock. `timedatectl` shows the time and whether it is being kept in sync.

```
{user}@{host}:~$ timedatectl
               Local time: Mon 2026-09-07 09:14:02 UTC
           Universal time: Mon 2026-09-07 09:14:02 UTC
                 RTC time: Mon 2026-09-07 09:14:02
                Time zone: UTC (UTC, +0000)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
```

The two lines that matter are `System clock synchronized: yes` and `NTP service: active`. Together they say chrony is running and has matched the clock to a time server. An accurate clock is what makes a log timeline mean anything when you compare it with another machine's, and a TLS certificate has a valid-from and valid-to date, so a clock that is years off makes every secure website look expired. Setting the time by hand with `timedatectl set-time` fights chrony, which will pull it back; if the zone is wrong, change the zone instead with `timedatectl set-timezone`.

Now the audit trail. auditd writes to `/var/log/audit/audit.log`, and `ausearch` reads it. Both need root.

```
{user}@{host}:~$ sudo ausearch -m USER_LOGIN --start today | tail -3
----
time->Mon Sep  7 09:02:11 2026
type=USER_LOGIN msg=audit(1788850931.442:318): pid=1920 uid=0 auid=1000 ses=3 subj=system_u:system_r:xdm_t:s0-s0:c0.c1023 msg='op=login id=1000 exe="/usr/sbin/gdm-session-worker" hostname=? addr=? terminal=/dev/tty1 res=success'
```

`-m USER_LOGIN` picks one message type (logins), `--start today` limits the day, and `tail -3` shows the last three lines. In the record, `auid=1000` is the audit user id, the account that actually logged in, `exe` is the program that reported it, and `res=success` is the result. This record is written by the kernel's audit system, not by the program, which is why it is trusted even when a program is lying.

Finally, accounts. `faillock` shows the failed-password counter that pam_faillock keeps for each user.

```
{user}@{host}:~$ sudo faillock --user {user}
{user}:
When                Type  Source                                           Valid
2026-09-07 08:58:40 TTY   /dev/tty1                                            V
```

Each line is one failed attempt: when, from what kind of terminal, and from where. `V` in the last column means it still counts. After the limit set in `/etc/security/faillock.conf` (three by default) the account is locked for the lockout time (ten minutes by default). `sudo faillock --user {user} --reset` clears the counter, which is what you do when a colleague has typed their password wrong three times and cannot wait.

Password quality is set in `/etc/security/pwquality.conf`, and it applies to every account at once. Loosening it there is a change for a lab, not for a daily machine.

## When it goes wrong

`Failed to set time: Automatic time synchronization is enabled` comes from `timedatectl set-time`. It is refusing to let you fight chrony. The fix is almost always the zone, not the time: `timedatectl list-timezones | grep -i london` then `sudo timedatectl set-timezone Europe/London`.

`Error opening config file (Permission denied)` from `ausearch` means you ran it without `sudo`. The audit log is root-only because it is the record of everyone's actions. Add `sudo`.

`Account locked due to 3 failed logins` at a login prompt means pam_faillock has done its job. Wait ten minutes, or have someone in wheel run `sudo faillock --user name --reset`. `pridwen why` will explain a failed `faillock` command; `pridwen explain timedatectl` walks through its subcommands.

## Try it

1. Run `resolvectl status | grep -i tls` and expect `+DNSOverTLS` on every `Protocols` line.
2. Run `timedatectl` and expect `System clock synchronized: yes` and `NTP service: active`.
3. Run `sudo faillock --user {user}` and expect an empty table if you have not mistyped your password today.
4. Run `sudo -k` to forget your sudo ticket, then `sudo true` and type your password wrong once, then correctly. Run the `faillock` command again and expect one line with a `V`.
5. Run `sudo faillock --user {user} --reset` and confirm the table is empty again.
6. Run `sudo ausearch -m USER_AUTH --start today | tail -3` and find the `res=failed` record from step 4.

## Remember

- `resolvectl status` must show `+DNSOverTLS`; `timedatectl` must show synchronized and NTP active.
- auditd records what happened at the kernel level; `sudo ausearch` reads it.
- Three wrong passwords lock an account for ten minutes; `sudo faillock --user name --reset` clears it.
