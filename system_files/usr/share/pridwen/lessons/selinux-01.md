# What SELinux is

SELinux is a second layer of access control that sits under the ordinary
permission bits. The permission bits you met in the Permissions node ask one
question: does this user, or this group, own the file, and is the read, write
or execute bit set for them. SELinux asks a different question: is this **type**
of process allowed to do this action to this **type** of object. Every running
process and every file, directory, socket and port carries a label, and a
policy, a large set of rules written by the Fedora maintainers, says which
labels may interact. If the policy has no rule that allows an action, the kernel
refuses it, even for root.

Pridwen runs SELinux in enforcing mode as part of its baseline, and so does
every Red Hat, Rocky and Fedora server you will meet on a job. A web server that
gets compromised is still only allowed to touch web-server-labelled files, which
is why the label system exists. Reading labels and reading a denial is a core
RHCSA skill, and it is the skill that lets you keep the guard on instead of
switching it off the first time it says no.

## Words you'll meet

- **label** (also called a **context**): the string SELinux attaches to a process or object, with four fields separated by colons: user, role, type, and level.
- **type**: the third field of a label, always ending in `_t`, and the only field the day-to-day rules care about.
- **policy**: the compiled set of rules that says which process types may do which actions to which object types.
- **enforcing**: the mode where the kernel refuses anything the policy does not allow and records a denial.
- **permissive**: the mode where the kernel records the denial but lets the action through anyway, for the whole system.
- **denial** (an **AVC** record): one log line saying one process type was refused one set of permissions on one object type.
- **audit log**: the file auditd writes under `/var/log/audit/`, root-only, where every denial lands; a copy also reaches the journal.

## How it works

Start by asking which mode the system is in. `getenforce` prints one word and
needs no root.

```
{user}@{host}:~$ getenforce
Enforcing
```

`Enforcing` means the guard is on. The other two answers are `Permissive` (log
but allow) and `Disabled` (no labels at all). On Pridwen you should always see
`Enforcing`. `sestatus` gives the longer version: which policy is loaded and
whether the running mode matches the one written in `/etc/selinux/config`.

```
{user}@{host}:~$ sestatus
SELinux status:                 enabled
SELinuxfs mount:                /sys/fs/selinux
SELinux root directory:         /etc/selinux
Loaded policy name:             targeted
Current mode:                   enforcing
Mode from config file:          enforcing
Policy MLS status:              enabled
Policy deny_unknown status:     allowed
Memory protection checking:     actual (secure)
Max kernel policy version:      33
```

The two lines that matter are `Current mode` and `Mode from config file`. When
they agree, the system will come back up in the same mode after a reboot. The
policy name `targeted` means only certain daemons are confined by strict rules;
your own login shell runs unconfined, which is why SELinux rarely gets in your
way as a person and mostly gets in the way of services.

Now look at a label. `ls -Z` is the ordinary `ls` with `-Z`, which adds the
security context column.

```
{user}@{host}:~$ ls -Z /etc/passwd {home}/pridwen/notes.txt
system_u:object_r:passwd_file_t:s0 /etc/passwd
unconfined_u:object_r:user_home_t:s0 {home}/pridwen/notes.txt
```

Read the first label left to right: `system_u` is the SELinux user, `object_r`
is the role (files always have `object_r`), `passwd_file_t` is the type, and
`s0` is the level, which the targeted policy does not use. The type is the piece
to remember. `/etc/passwd` is `passwd_file_t`, and your notes file is
`user_home_t`, the type every file under a home directory gets. Processes carry
labels too: `ps -Z` shows them, and a web server runs as `httpd_t`.

Here is what a denial looks like when a web server is pointed at a file in a
home directory. The record is one line in the audit log; it is wrapped here so
you can read it.

```
{user}@{host}:~$ sudo ausearch -m avc -ts recent
type=AVC msg=audit(1757232841.512:3181): avc:  denied  { read } for
  pid=5120 comm="httpd" name="index.html" dev="dm-0" ino=262415
  scontext=system_u:system_r:httpd_t:s0
  tcontext=unconfined_u:object_r:user_home_t:s0 tclass=file permissive=0
```

Field by field: `denied { read }` is the permission that was refused. `comm`
is the program name and `pid` its process id. `name` is the object it touched.
`scontext` is the source context, the label of the process doing the asking,
and its type is `httpd_t`, the web server. `tcontext` is the target context,
the label of the thing being touched, and its type is `user_home_t`, a file in
someone's home. `tclass` says the target is a `file`. `permissive=0` confirms
the action was really blocked, not just logged. As a sentence: the web server
was refused read on a home-directory file. `pridwen why selinux` prints that
sentence for you from the newest denial, and the next lesson reads records in
detail.

A denial is narrow by nature: one process type, one object type, one set of
permissions. That is why the wrong response is `sudo setenforce 0`, which drops
the whole system to permissive and turns off the guard everywhere to fix one
thing. The right response is to read the one denial and answer it with a label,
a boolean, or a small policy rule, which the third lesson covers.

## When it goes wrong

`Permission denied` from a program whose file permissions look right is the
classic sign. The permission bits and the owner can be perfect and SELinux can
still say no. Run `pridwen why`; if a denial landed in the last few minutes it
will say so, and `pridwen why selinux` translates it.

`setenforce: SELinux is disabled` or `setenforce: setenforce() failed` means
either SELinux is not enabled at all (never the case on Pridwen) or you ran
`setenforce` without root. Changing the mode needs `sudo`, and on Pridwen it
should stay at 1. `getenforce` reads the mode without root.

`ls: cannot access '/root': Permission denied` when you add `-Z` is not an
SELinux error; it is the ordinary permission bits on root's home. `-Z` only adds
a column, it does not grant anything.

## Try it

1. Type `getenforce` and confirm the answer is `Enforcing`.
2. Type `sestatus` and find the lines `Current mode` and `Mode from config file`; confirm they match.
3. Type `ls -Z /etc/passwd /etc/shadow /etc/hostname` and read the type of each label; expect `passwd_file_t`, `shadow_t`, and `hostname_etc_t`.
4. Type `ls -Z {home}` and confirm your own files carry `user_home_t`.
5. Type `ps -Z | head -3` and find the type in your shell's label; expect `unconfined_t`.
6. Say out loud, in one sentence, why turning SELinux off to fix one denial is the wrong reflex.

## Remember

- SELinux checks types, not owners: the `_t` field in `ls -Z` is what the policy reads.
- A denial is one process type, one object type, one permission; fix that one thing, never `setenforce 0`.
- `getenforce` shows the mode, `sudo ausearch -m avc -ts recent` shows denials, and `pridwen why selinux` translates the newest one.
