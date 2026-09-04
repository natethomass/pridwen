# Sudo as a path up

Sudo is the intended path to root, which makes a loose sudo rule one of the most
common ways attackers climb. Reading `sudo -l` the way an attacker would shows why
Pridwen grants whole-command sudo to trusted users rather than piecemeal rights.

The danger is granting sudo on a single program that can spawn a shell. Many
everyday tools can: an editor's shell escape, `find -exec`, an interpreter's `-c`.
If a user may run one of those as root without a password, they effectively have a
root shell. `sudo -l` reveals exactly what is allowed, and a `NOPASSWD` entry on
such a tool is the finding.

```
$ sudo -l
User web may run the following commands on web-01:
    (root) NOPASSWD: /usr/bin/find
$ # find can run arbitrary commands via -exec, so this is root
```

The defence is to grant sudo carefully. Prefer whole-command trust for people who
need it, avoid `NOPASSWD` on anything that can execute other programs, and always
edit sudoers with `visudo` so a typo does not widen access. On the Range you take a
too-generous rule, demonstrate the escalation it allows, then tighten it and show
the door is closed, which is the clearest possible argument for least privilege.

## Try it

1. On a Range host, read a crafted `sudo -l` and spot the dangerous grant.
2. Explain how a tool like `find` or an editor turns that grant into root.
3. Rewrite the rule to remove the escalation and validate with `visudo -c`.
4. Explain why `NOPASSWD` on an interpreter is especially risky.
