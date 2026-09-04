# Reading a denial

When SELinux blocks something, it writes an AVC record to the audit log. Learning
to read that record turns a mysterious "Permission denied" into a specific,
fixable statement. The tool is `ausearch`, and Pridwen's `pridwen why` translates
the latest one into plain English.

`sudo ausearch -m avc -ts recent` shows denials from the last ten minutes. Each
record names the source context (`scontext`), the target context (`tcontext`),
the object class, and the permission that was denied. Read it as a sentence: this
type of process was denied this action on this type of object.

```
$ sudo ausearch -m avc -ts recent | tail
type=AVC ... denied { read } for pid=5120 comm="httpd"
  name="index.html" scontext=...:httpd_t tcontext=...:user_home_t tclass=file
```

That example says the web server (`httpd_t`) was denied read on a file labelled
`user_home_t`, which is the label home directories carry. The fix is not to
weaken SELinux but to give the file a label httpd is allowed to read, or to move
it under `/var/www`. Exit 1 from `ausearch` means no matching records, which is
good news; widen the window with `-ts today` if you expected some.

## Try it

1. Run `sudo ausearch -m avc -ts today` and see whether any denials exist.
2. If one exists, name its scontext, tcontext, and the denied permission.
3. Run `pridwen why` after a denial and compare it with the raw record.
4. Explain in one sentence what a chosen denial was actually blocking.
