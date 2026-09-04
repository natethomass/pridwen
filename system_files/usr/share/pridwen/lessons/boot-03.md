# Kernel arguments

Sometimes the kernel needs a setting passed on its command line, such as a
hardware quirk or a debug flag. On a traditional system you would edit GRUB; on a
bootc system that file is generated from the deployment, so editing it by hand is
overwritten. The supported path is `rpm-ostree kargs`.

Each deployment stores its own kernel arguments, so a change creates a new
deployment and applies at the next boot, keeping the current one as rollback.
`rpm-ostree kargs` with no action shows the current set; `--append`, `--delete`
and `--replace` change it. What the running kernel actually used is in
`/proc/cmdline`.

```
$ rpm-ostree kargs
rd.luks.uuid=... root=... rhgb quiet
$ sudo rpm-ostree kargs --append=systemd.log_level=debug
$ cat /proc/cmdline
```

The same reasoning rules out `grub2-mkconfig`, `grubby` and editing
`/etc/default/grub`: none of them are what regenerates the boot entries here.
Keeping kernel arguments as a property of the deployment means they roll back
with everything else, so a bad flag is undone by booting the previous entry
rather than by rescuing GRUB.

## Try it

1. Run `rpm-ostree kargs` and read the current arguments.
2. Compare them with `cat /proc/cmdline` from the running kernel.
3. On a test machine, append a harmless karg and see the new pending deployment.
4. Explain why editing `/etc/default/grub` would have no effect here.
