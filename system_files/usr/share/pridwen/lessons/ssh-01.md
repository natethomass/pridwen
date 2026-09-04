# Keys and the client

SSH is how you reach a shell on another machine safely. The client is `ssh`, and
the strong way to authenticate is a key pair rather than a password. You generate
a pair once, keep the private half on your machine, and place the public half on
each server you want to reach.

`ssh-keygen -t ed25519` creates a modern key pair in `~/.ssh`. The private key
never leaves your machine; the `.pub` file is what you copy out. `ssh-copy-id
user@host` installs it into the server's `~/.ssh/authorized_keys`, after which
the password prompt disappears because the server trusts your key.

```
$ ssh-keygen -t ed25519 -C "nate@pridwen"
$ ssh-copy-id nate@web-01
$ ssh nate@web-01
[web-01]$ hostname
web-01
```

Two details prevent most trouble. A private key must not be readable by others,
so `chmod 600 ~/.ssh/id_ed25519` and `chmod 700 ~/.ssh`; ssh refuses a key with
loose permissions. And when a host key changes, ssh warns loudly because that can
mean an imposter; after a genuine rebuild, `ssh-keygen -R host` clears the old
key so you can accept the new one. Copying files uses the same trust: `scp -r`
for a tree, or `rsync -a` which only sends what changed.

## Try it

1. Generate an ed25519 key pair and look at both files in `~/.ssh`.
2. On a Range host, install your key with `ssh-copy-id` and log in without a password.
3. Fix a too-open key with `chmod 600` and confirm ssh stops complaining.
4. Copy a directory to the host with `rsync -a` and run it again to see nothing resends.
