# Fixing without turning it off

Most SELinux denials come down to a wrong label. A file was created somewhere,
moved from somewhere else, or restored from a backup, and it carries a type the
policy does not expect for that path. The fix is to put the expected label back,
and the tool that does that is `restorecon`. When the expected label itself
needs to change, because you are serving web pages from a new directory, for
example, `semanage fcontext` records the new expectation and `restorecon`
applies it. The third kind of fix is a **boolean**, a switch the policy already
provides for behaviour it anticipated.

These three tools cover nearly every denial you will meet on Pridwen or on a
Rocky server, and none of them weakens SELinux. Knowing them is the difference
between an admin who keeps enforcing mode on a production host and one who
quietly runs permissive because "it kept breaking things". The RHCSA exam asks
for exactly these: relabel a path, make it permanent, flip a boolean.

## Words you'll meet

- **file context**: the label the policy expects a path to carry, kept as a set of regular-expression rules.
- **`restorecon`**: resets a file's label to what the file-context rules say it should be.
- **`matchpathcon`**: prints what the rules say a path should be labelled, without changing anything.
- **`chcon`**: changes a label directly, without changing the rules, so the change is undone by the next relabel.
- **`semanage fcontext`**: adds, changes or lists file-context rules, so the change survives relabels.
- **boolean**: a named on/off switch inside the policy that enables an optional behaviour, like letting httpd open network connections.
- **relabel**: walking the filesystem and setting every file's label from the rules; `restorecon -R` does it for one tree.
- **layering**: `rpm-ostree install` adding an RPM on top of the immutable image, which slows every update, so it is a last resort.

## How it works

Ask what a path should be labelled before you change anything. `matchpathcon`
reads the rules and prints the answer; `ls -Z` (the `-Z` flag adds the security
context column) shows what the file actually carries.

```
{user}@{host}:~$ matchpathcon /var/www/html/index.html
/var/www/html/index.html	system_u:object_r:httpd_sys_content_t:s0
{user}@{host}:~$ ls -Z /var/www/html/index.html
unconfined_u:object_r:user_home_t:s0 /var/www/html/index.html
```

The rule says `httpd_sys_content_t`; the file says `user_home_t`. That mismatch
is the whole problem: someone copied the file from a home directory with a
command that preserved its label (`mv` keeps labels; `cp` gives the new file
the label of its destination). Fix it with `restorecon`. `-R` recurses through
a directory, `-v` is verbose and prints each label it changed.

```
{user}@{host}:~$ sudo restorecon -Rv /var/www/html
Relabeled /var/www/html/index.html from unconfined_u:object_r:user_home_t:s0 to unconfined_u:object_r:httpd_sys_content_t:s0
```

Each output line names the file, the old label and the new one. No lines means
nothing needed changing. `restorecon` is safe to run as often as you like: it
only touches labels that differ from the rules.

When you want a directory the rules do not know about, say `/srv/web`, to be
web content, add a rule. `-a` adds, `-t` names the type, and the path is a
regular expression: `(/.*)?` means "and anything under it, optionally".

```
{user}@{host}:~$ sudo semanage fcontext -a -t httpd_sys_content_t '/srv/web(/.*)?'
{user}@{host}:~$ sudo restorecon -Rv /srv/web
Relabeled /srv/web from unconfined_u:object_r:var_t:s0 to unconfined_u:object_r:httpd_sys_content_t:s0
Relabeled /srv/web/index.html from unconfined_u:object_r:var_t:s0 to unconfined_u:object_r:httpd_sys_content_t:s0
```

`semanage fcontext` only writes the rule; nothing changes on disk until
`restorecon` applies it. `sudo semanage fcontext -l | grep /srv/web` lists the
rule back. Avoid `chcon`: it changes the label on the file but not the rule, so
the next `restorecon`, or a full relabel after an update, silently puts the old
label back and the denial returns weeks later with no obvious cause.

A boolean is the fix when the denial is about behaviour, not a path. `getsebool`
reads them; `-a` lists all of them.

```
{user}@{host}:~$ getsebool -a | grep httpd_can_network
httpd_can_network_connect --> off
httpd_can_network_connect_db --> off
{user}@{host}:~$ sudo setsebool -P httpd_can_network_connect on
```

Each line is a name, an arrow, and `on` or `off`. `setsebool` flips one; `-P`,
persistent, writes it into the policy so it survives a reboot. Without `-P` the
boolean resets at the next boot, which is fine for a quick test and wrong for a
fix. Booleans need `sudo`; reading them does not.

One Pridwen detail: `semanage` comes from the package
`policycoreutils-python-utils`, which the base image does not carry.
`restorecon`, `matchpathcon`, `getsebool` and `setsebool` are all present. When
you need `semanage` on the host, `sudo rpm-ostree install
policycoreutils-python-utils` layers it and takes effect after a reboot; on a
Range host you install it with `dnf` the ordinary way. Until then `pridwen why
selinux` still translates the denial and tells you which fix it is.

## When it goes wrong

`bash: semanage: command not found` (exit 127) is the missing package above.
`restorecon` may be enough: if `matchpathcon` already says the right type, no
new rule is needed, just `sudo restorecon -Rv path`.

`restorecon: lstat(/var/www/html) failed: Permission denied` or a label that
will not change means you ran it without `sudo`. You may relabel your own files;
anything under `/etc`, `/var`, or another user's home needs root.

`ValueError: File context for /srv/web(/.*)? already defined` from
`semanage fcontext -a` means the rule exists. Use `-m` (modify) instead of `-a`
to change its type, or `-d` (delete) to remove it.

`Permission denied` that comes back after an upgrade on a file you fixed with
`chcon` is the relabel undoing your change. Redo it the permanent way with
`semanage fcontext` then `restorecon`. `pridwen explain chcon` and
`pridwen explain restorecon` annotate the flags.

## Try it

1. Type `mkdir -p {home}/pridwen/lab && touch {home}/pridwen/lab/test.txt`, then `ls -Z {home}/pridwen/lab/test.txt`; expect the type `user_home_t`.
2. Type `matchpathcon {home}/pridwen/lab/test.txt` and confirm the rule agrees with what the file carries.
3. Type `chcon -t httpd_sys_content_t {home}/pridwen/lab/test.txt` then `ls -Z` again; the type is now wrong on purpose.
4. Type `restorecon -v {home}/pridwen/lab/test.txt` and read the `Relabeled ... from ... to ...` line; `ls -Z` shows `user_home_t` again.
5. Type `getsebool -a | grep httpd | head -5` and read five booleans with their on or off state.
6. Explain why `semanage fcontext` outlasts `chcon` across a relabel.

## Remember

- `matchpathcon` says what a path should be; `restorecon -Rv` makes it so and prints what it changed.
- `semanage fcontext -a -t type 'path(/.*)?'` then `restorecon` is permanent; `chcon` is undone by the next relabel.
- `sudo setsebool -P name on` flips a policy switch for good; without `-P` it resets at reboot.
