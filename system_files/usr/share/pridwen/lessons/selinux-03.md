# Fixing without turning it off

Most denials come down to a wrong label, and the tool to fix a label is
`restorecon`, which resets a file to the type the policy expects for its path.
When the expected type itself needs to change, `semanage fcontext` records the
new rule and `restorecon` applies it.

```
$ matchpathcon /var/www/html/index.html
/var/www/html/index.html system_u:object_r:httpd_sys_content_t:s0
$ sudo restorecon -Rv /var/www/html
$ sudo semanage fcontext -a -t httpd_sys_content_t '/srv/web(/.*)?'
$ sudo restorecon -Rv /srv/web
```

`restorecon` is safe and idempotent: it only changes labels that differ from the
policy's expectation, and `-v` prints each change. Avoid `chcon`, which sets a
label that the next relabel silently undoes; use `semanage fcontext` so the
change is permanent. The other common fix is a boolean, a policy switch: `sudo
setsebool -P name on` toggles behaviour the policy already anticipates, like
letting httpd make network connections. The `-P` makes it persist; without it the
boolean resets at reboot. Note that `semanage` comes from a package the base
image does not carry, so layer `policycoreutils-python-utils` when you need it.

## Try it

1. Run `matchpathcon` on a file and compare it with `ls -Z` on the same file.
2. Deliberately mislabel a test file with `chcon`, then fix it with `restorecon -v`.
3. List booleans with `getsebool -a | grep httpd` and read a couple.
4. Explain why `semanage fcontext` outlasts `chcon` across a relabel.
