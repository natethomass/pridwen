# Changing permissions and ownership

Two commands change what the mode describes. `chmod` sets the permission bits,
and `chown` sets the owner and group. The owner of a file may change its mode;
changing ownership to another user is reserved for root.

`chmod` takes either symbolic or numeric forms. Symbolic edits one part, like
`chmod u+x file` to add execute for the owner or `chmod go-w file` to remove
write for group and other. Numeric sets all three at once, like `chmod 644 file`
for readable data or `chmod 755 script` for a runnable program.

```
$ chmod +x deploy.sh
$ ls -l deploy.sh
-rwxr-xr-x. 1 nate nate 500 Sep  4 09:30 deploy.sh
$ sudo chown root:root /usr/local/bin/tool
```

Resist the reflex to `chmod 777`, which lets every account on the machine write
and run the file; it fixes the symptom and opens a hole. The real fix is usually
ownership or group membership. To share a file with a team, put them in a group
and use `chmod g+w` plus `chgrp team file`, which grants exactly the access you
mean and no more.

## Try it

1. Create a script, run it and watch it fail, then `chmod +x` it and run it again.
2. Set a file to `644` with the numeric form, then to `640` and read the change.
3. Run `chgrp` to change a file to a group you belong to (`id` lists them).
4. Try `chown` to another user without sudo, read the refusal, then reason about why.
