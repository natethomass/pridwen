# Reading a denial

When SELinux blocks something, it does not print an error to your terminal. The
program that was blocked sees `Permission denied`, the same words it would see
from a wrong permission bit, and SELinux writes one record to the audit log
describing exactly what it refused. Learning to read that record turns a vague
"it says permission denied" into a specific, fixable statement: this type of
process wanted this permission on this type of object.

On Pridwen the tool for the raw record is `ausearch`, and `pridwen why selinux`
translates the newest one into a plain sentence. On a job, an admin who can read
an AVC in thirty seconds fixes the label and moves on; one who cannot reaches
for `setenforce 0` and leaves the server unguarded. Reading denials is also the
part of the RHCSA SELinux objective that people fail most, because they never
looked at a real one.

## Words you'll meet

- **AVC**: access vector cache, the kernel part of SELinux that answers "may this happen"; a denial record is labelled `type=AVC`.
- **audit log**: `/var/log/audit/audit.log`, written by the auditd daemon, root-only, where AVC records land first.
- **journal**: systemd's log store; audit records are copied into it too, and `pridwen why` reads them from there.
- **scontext**: source context, the label of the process that asked.
- **tcontext**: target context, the label of the thing it asked about.
- **tclass**: target class, what kind of thing the target is: `file`, `dir`, `tcp_socket`, `process`, and so on.
- **`-ts`**: the `ausearch` flag for "time start"; `recent` means the last ten minutes, `today` since midnight.
- **`-m`**: the `ausearch` flag for message type; `avc` selects SELinux denials.

## How it works

The audit log is root-only, so the search needs `sudo`. `-m avc` selects SELinux
denial records and `-ts recent` limits them to the last ten minutes. The
`-i` flag, interpret, turns numbers like user ids and timestamps into names and
dates; it is optional but easier on the eyes.

```
{user}@{host}:~$ sudo ausearch -m avc -ts recent -i
----
type=AVC msg=audit(09/07/2026 09:14:01.512:3181) : avc:  denied  { read } for
  pid=5120 comm=httpd name=index.html dev="dm-0" ino=262415
  scontext=system_u:system_r:httpd_t:s0
  tcontext=unconfined_u:object_r:user_home_t:s0 tclass=file permissive=0
```

Read it in this order, every time. First the permissions inside the braces:
`{ read }` is what was refused; sometimes there are several, like `{ read
open }`. Then `comm`, the command name, `httpd`, the web server; `pid` is its
process id if you need to find it in `ps`. Then `name`, the object, here
`index.html`, with `dev` and `ino` (the disk and the inode number, the file's
identity on that disk) in case two files share a name.

Now the two contexts. `scontext` is the source, the process. Its label has four
colon-separated fields and the third one, `httpd_t`, is the type: the web
server. `tcontext` is the target, the object. Its type is `user_home_t`, the
label every file under a home directory carries. `tclass=file` says the target
is an ordinary file rather than a directory or a socket. `permissive=0` means
the kernel really blocked it; `permissive=1` would mean it was only logged.

Put together as a sentence: the web server (`httpd_t`) was denied read on a
file labelled as home-directory content (`user_home_t`). That sentence contains
the fix. The policy allows httpd to read `httpd_sys_content_t`, so either the
file needs that label or it needs to live under `/var/www`, where files get that
label automatically. Weakening SELinux never enters into it.

Let the system do the reading for you when you are in a hurry.

```
{user}@{host}:~$ pridwen why selinux
SELinux denied httpd read on a file in a home directory (index.html).
  Source:  httpd_t  (the web server)
  Target:  user_home_t  (a file in a home directory), class file
Ways forward:
1. sudo restorecon -Rv /var/www/html        relabel if the file is in the right place
2. sudo semanage fcontext ...               if the directory should be web content
3. sudo ausearch -m AVC -ts recent          the raw record
```

The translation names the same three things you just read by hand: source type,
target type, and the denied permission. Reading the raw record once, and then
letting `pridwen why selinux` do it on the next twenty, is the intended rhythm.

Denials also carry a `tclass` other than `file` and they read the same way. A
`tclass=tcp_socket` with `{ name_bind }` means a process tried to listen on a
port whose label the policy does not give it. A `tclass=dir` with `{ write }`
means it tried to create something in a directory of the wrong type.

## When it goes wrong

`<no matches>` with exit status 1 from `ausearch` means no record matched. That
is good news, not an error: nothing was denied in the window you asked for. If
you expected a denial, widen the window with `-ts today` or `-ts boot`, and check
the type is `avc` (ausearch accepts `avc` and `AVC`).

`Error opening /var/log/audit/audit.log (Permission denied)` means you ran
`ausearch` without `sudo`. The audit log is root-only on purpose: it is the
record an attacker would most like to edit.

`Permission denied` from a program with no matching AVC at all is not an
SELinux problem. Check the ordinary permission bits with `ls -l`, and run
`pridwen why` to see which it thinks it is. Some denials are also silenced by
the policy (a `dontaudit` rule); `sudo semodule -DB` turns those on temporarily
and `sudo semodule -B` turns them back off.

## Try it

1. Type `sudo ausearch -m avc -ts today` and note whether any denial exists on your system; expect `<no matches>` on a quiet desktop.
2. If a record exists, write down its `scontext` type, its `tcontext` type, its `tclass`, and the words inside the braces.
3. Type `pridwen why selinux` and compare its sentence with what you wrote down.
4. Type `sudo ausearch -m avc -ts today -i | grep -c denied` to count the denials since midnight.
5. Type `ls -Z {home}/pridwen` and confirm the type you see is the one a `tcontext` would show for those files.
6. Explain in one sentence what one chosen denial, real or the httpd example above, was actually blocking.

## Remember

- Read a denial in this order: permission in braces, `comm`, then the type inside `scontext`, the type inside `tcontext`, then `tclass`.
- `sudo ausearch -m avc -ts recent` shows the raw record; `pridwen why selinux` reads it back in English.
- Exit 1 from `ausearch` means nothing matched, which usually means nothing was denied.
