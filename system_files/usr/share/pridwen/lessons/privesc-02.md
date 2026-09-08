# Sudo as a path up

Sudo is the intended path to root: it lets a trusted person run a command as
root, on purpose, with a record of it. That is also why a loose sudo rule is one
of the most common ways an attacker climbs. This lesson is about reading a sudo
policy the way an attacker would, so you can spot the grant that quietly hands
out a root shell and write rules that do not.

Reading your own `sudo -l` on your Pridwen host is safe and worth doing. The part
where you actually exploit a loose rule to become root runs only against Range
targets you own (Rocky 9 labs you start with `pridwen enter rocky`). On a real
job this is why you grant whole-command trust to the few people who need it,
rather than sprinkling narrow per-program rights that turn out to be doors.

## Words you'll meet

- **sudo**: the tool that runs a single command as another user, normally root, for people the policy allows.
- **sudoers**: the policy file (`/etc/sudoers` and drop-ins) that says who may run what as whom.
- **sudo -l**: a command that lists exactly what the current user is allowed to run under sudo.
- **NOPASSWD**: a sudoers option that lets a command run under sudo without asking for a password.
- **shell escape**: a feature in an everyday tool that lets it launch a shell or run an arbitrary command.
- **wheel**: the group whose members Pridwen allows to use sudo; membership is the whole grant.

## How it works

To work on a Range host you first connect to it from your own Pridwen machine
with SSH, which opens a command line on the far end and changes your prompt to
that host's name:

```
{user}@{host}:~$ ssh labuser@range-01
labuser@range-01:~$
```

The prompt now reads `labuser@range-01`, so the commands below run on the Range
target as a low-privilege account with a foothold.

The first move, attacker or defender, is to ask sudo what you are allowed to do.
The `-l` flag lists your permissions from the policy:

```
labuser@range-01:~$ sudo -l
User labuser may run the following commands on range-01:
    (root) NOPASSWD: /usr/bin/find
```

Read that back. The line says the account `labuser` may run `/usr/bin/find` as
root (`(root)`) without a password (`NOPASSWD`). At a glance that looks narrow,
just one program. The danger is that `find` has a shell escape: its `-exec` test
runs any command you name. So a rule that lets you run `find` as root lets you
run anything as root:

```
labuser@range-01:~$ sudo find . -maxdepth 0 -exec whoami \;
root
```

Here `-exec whoami \;` tells find to run `whoami` (which prints the current
user) for the match, and because find is running as root, `whoami` prints
`root`. That single line proves the escalation: a "narrow" grant on `find` was
actually a root shell in disguise. Editors, `awk`, `python`, and several other
everyday tools carry the same kind of escape, which is why granting any of them
through `NOPASSWD` is so risky.

The defence is to grant sudo carefully. On Pridwen the rule is simple: members
of the `wheel` group get whole-command sudo, and everyone else gets none, so
there are no clever per-program grants to get wrong. When you must write a
specific rule on a Range host, avoid `NOPASSWD` on anything that can execute
other programs, and always edit the policy with `visudo`, which checks your
syntax before saving so a typo cannot widen access or lock everyone out. On the
Range you take a too-generous rule, show the escalation it allows, then tighten
it and prove the door is shut.

## When it goes wrong

`labuser is not allowed to run sudo on range-01. This incident will be reported.`
means the account is not in the policy at all; that is the locked-down default,
not a bug. Add the account to `wheel` on the Range host if it genuinely needs
sudo.

`>>> /etc/sudoers.d/labuser: syntax error near line 2 <<<` from `visudo` means
your edit is malformed; `visudo` refuses to save it, which is the safety net
working. Fix the line it names and save again.

`sudo: a password is required` where you expected `NOPASSWD` means the rule does
not actually carry that option; re-read `sudo -l` and `pridwen explain sudo` to
see exactly what is granted.

## Try it

1. On a Range host, read a crafted `sudo -l` and point at the dangerous grant.
2. Explain in one sentence how a tool like `find` turns that grant into a root shell.
3. Demonstrate the escalation with `sudo find . -maxdepth 0 -exec whoami \;` and read the `root` output.
4. Rewrite the rule to remove the escalation and validate it with `visudo -c`.
5. Explain why `NOPASSWD` on a program that can run other programs is especially risky.

## Remember

- Sudo is the intended road to root, so a loose sudo rule is a loose door to root.
- A grant on any tool with a shell escape (`find -exec`, an editor, an interpreter) is a full root shell, however narrow it looks.
- Pridwen grants whole-command sudo to `wheel` and nothing to anyone else, and every sudoers edit should go through `visudo`.
