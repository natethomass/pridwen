# What SELinux is

SELinux is a second layer of access control that sits under the ordinary
permission bits. Where permissions ask "does this user own the file", SELinux
asks "is this type of process allowed to do this to this type of object". Every
process and file carries a label, and a policy says which labels may interact.

Pridwen runs SELinux in enforcing mode, part of its baseline. `getenforce`
reports the mode; `sestatus` shows the policy and both the configured and running
modes. The label is the extra column in `ls -Z`, and the piece that matters most
is the type, which ends in `_t`.

```
$ getenforce
Enforcing
$ ls -Z /etc/passwd
system_u:object_r:passwd_file_t:s0 /etc/passwd
```

A denial means one labelled process tried something the policy did not allow. It
is narrow by nature: one process, one object, one permission. The wrong response
is to switch enforcing off for the whole system with `setenforce 0`, which turns
off the guard everywhere to fix one thing. The right response is to read the one
denial and address it with a label, a boolean, or a small policy rule, which the
next two lessons cover.

## Try it

1. Run `getenforce` and confirm the system is enforcing.
2. Run `ls -Z` on a few files in `/etc` and read their types.
3. Run `sestatus` and compare the current mode with the config file mode.
4. Explain why turning SELinux off to fix one error is the wrong reflex.
