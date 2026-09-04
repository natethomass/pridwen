# What sudo does

`sudo` runs one command as another user, by default root, after checking that
you are allowed and asking for your own password. That last part is the whole
point: there is no shared root password to leak, and every use is tied to a
named person.

Permission comes from being in the `wheel` group on Pridwen, which the sudoers
rule `%wheel ALL=(ALL) ALL` grants. `sudo -l` shows what you may run. Your
password is cached briefly per terminal, so a run of commands does not prompt
each time, and `sudo -k` clears the cache immediately.

```
$ sudo -l
User nate may run the following commands on pridwen:
    (ALL) ALL
$ sudo systemctl restart chronyd
$ journalctl _COMM=sudo -n 1
... nate : TTY=pts/0 ; PWD=/home/nate ; USER=root ; COMMAND=/usr/bin/systemctl restart chronyd
```

That journal line is the reason Pridwen uses sudo rather than a root login. It
records who ran what, from where, as whom. When sudo exits non-zero it is usually
the command that failed, but three wrong passwords or a user not in wheel also
exit 1, and both land in the log. Reading `sudo -l` and the journal turns sudo
from a magic word into an accountable tool.

## Try it

1. Run `sudo -l` and read what your account is allowed to run.
2. Run a harmless `sudo` command, then find it with `journalctl _COMM=sudo -n 3`.
3. Run `sudo -k`, then `sudo true`, and notice it prompts again.
4. Run `id` and confirm `wheel` is in your groups.
