# Keys and the client

SSH, the secure shell, is how you reach a command line on another machine
without anyone on the network between you reading or changing what you type.
The program you run is the **client**, `ssh`; the program waiting on the other
machine is the **server**, `sshd`. Everything between them is encrypted. Before
the server gives you a shell it has to know who you are, and the strong way to
prove that is a **key pair** rather than a password. You generate a pair once,
keep the private half on your machine, and place the public half on each
server you want to reach.

On Pridwen your own `sshd` is off by default (the next lesson covers turning it
on), but the client is ready, and the Range labs, Ansible, and every server job
you will ever have run over SSH with keys. A password can be guessed by a
script that tries a million of them; a private key cannot, and it never travels
over the network. Keys are also what let automation log in without a human
typing anything.

## Words you'll meet

- **client**: the `ssh` program on your machine that opens the connection.
- **server** (`sshd`): the daemon on the remote machine that accepts connections and starts your shell.
- **key pair**: two matching files: a private key that proves who you are and a public key that anyone may see.
- **private key**: `~/.ssh/id_ed25519`, never copied anywhere, readable only by you.
- **public key**: `~/.ssh/id_ed25519.pub`, the half you give to servers.
- **ed25519**: the modern key type; short, fast, and the current default.
- **authorized_keys**: the file on a server, `~/.ssh/authorized_keys`, listing the public keys allowed to log in as that user.
- **host key**: the server's own key pair, which your client remembers in `~/.ssh/known_hosts` so an imposter cannot pretend to be it.
- **agent**: a background program that holds your unlocked private key so you type its passphrase once per session; GNOME provides one.

## How it works

Generate a key pair. `-t ed25519` picks the key type and `-C` attaches a
comment so you can tell keys apart later; the comment is not secret.

```
{user}@{host}:~$ ssh-keygen -t ed25519 -C "{user}@{host}"
Generating public/private ed25519 key pair.
Enter file in which to save the key ({home}/.ssh/id_ed25519):
Enter passphrase for "{home}/.ssh/id_ed25519" (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in {home}/.ssh/id_ed25519
Your public key has been saved in {home}/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:h1QkT9v2xW7pL0aZs4mNfE8cRbY3uKdJ6oHtV1gXqAo {user}@{host}
```

Press Enter to accept the default file. A passphrase encrypts the private key
on disk so that a stolen laptop does not hand out your servers; choose one, and
the GNOME keyring will remember it for the session. The last line is the key's
fingerprint, a short hash you can compare against what a server later shows.
Look at what was made: `ls -l` (long format: permissions, owner, size, date).

```
{user}@{host}:~$ ls -l {home}/.ssh
total 8
-rw-------. 1 {user} {user} 464 Sep  7 09:30 id_ed25519
-rw-r--r--. 1 {user} {user}  98 Sep  7 09:30 id_ed25519.pub
```

The private key is `-rw-------`, readable and writable by you alone (mode
600); the public key is world-readable (644), which is fine, it is public. The
directory itself must be `drwx------` (700). `ssh` refuses to use a private key
that other people can read, so if you ever copy one, fix the modes with
`chmod 600 ~/.ssh/id_ed25519` and `chmod 700 ~/.ssh`.

Install the public key on a Range host. `ssh-copy-id` logs in once with your
password and appends the `.pub` line to that user's `authorized_keys`.

```
{user}@{host}:~$ ssh-copy-id {user}@web-01
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
{user}@web-01's password:
Number of key(s) added: 1

Now try logging into the machine, with:   "ssh '{user}@web-01'"
and check to make sure that only the key(s) you wanted were added.
```

After that, the password prompt disappears because the server trusts your key.

```
{user}@{host}:~$ ssh {user}@web-01
Last login: Sun Sep  7 09:31:02 2026 from 192.168.56.1
[{user}@web-01 ~]$ hostname
web-01
[{user}@web-01 ~]$ exit
logout
Connection to web-01 closed.
```

The prompt changes to the remote machine's, `hostname` confirms where you are,
and `exit` comes home. The very first time you connect to any host, `ssh` shows
its host key fingerprint and asks `Are you sure you want to continue
connecting (yes/no/[fingerprint])?`; answering `yes` records it in
`known_hosts`. From then on, if that host's key ever changes, `ssh` warns
loudly, because a changed key can mean an imposter sitting between you and the
server. After a genuine rebuild, `ssh-keygen -R web-01` removes the old entry
so you can accept the new one.

Copying files uses the same trust. `scp -r` (recursive) copies a directory
tree; `rsync -a` (archive: keep permissions, times and links) copies a tree and
on the second run sends only what changed.

```
{user}@{host}:~$ rsync -a {home}/pridwen/ {user}@web-01:pridwen/
{user}@{host}:~$ rsync -a {home}/pridwen/ {user}@web-01:pridwen/
```

The first run copies everything; the second prints nothing and finishes in a
blink, because nothing changed. The trailing slash on the source means "the
contents of", not the directory itself.

## When it goes wrong

`Permissions 0644 for '{home}/.ssh/id_ed25519' are too open.` followed by
`This private key will be ignored.` means the private key is readable by
others. `chmod 600 {home}/.ssh/id_ed25519` and `chmod 700 {home}/.ssh` fix it.

`WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!` means the host key in
`known_hosts` does not match what the server presented. If you rebuilt that
host yourself, `ssh-keygen -R hostname` clears the old key. If you did not,
stop and find out why before typing a password into it.

`ssh: connect to host web-01 port 22: Connection refused` with exit status 255
means nothing is listening on port 22 there, or a firewall is dropping it.
`ssh -v {user}@web-01` (verbose) narrates each step of the attempt, and
`pridwen why` under the failed command names the usual causes. `scp: omitting
directory` means `scp` needs `-r` for a directory, or use `rsync -a`.

## Try it

1. Type `ssh-keygen -t ed25519 -C "{user}@{host}"`, accept the default file, and choose a passphrase.
2. Type `ls -l {home}/.ssh` and confirm the private key is `-rw-------` and the public key `-rw-r--r--`.
3. Type `cat {home}/.ssh/id_ed25519.pub` and read the single line: key type, the key itself, your comment.
4. On a Range host, type `ssh-copy-id {user}@web-01`, enter the password once, and expect `Number of key(s) added: 1`.
5. Type `ssh {user}@web-01 hostname` and expect `web-01` with no password prompt.
6. Type `rsync -a {home}/pridwen/ {user}@web-01:pridwen/` twice and notice the second run does nothing.

## Remember

- `ssh-keygen -t ed25519` makes a pair; the private key never leaves `~/.ssh`, the `.pub` goes to servers via `ssh-copy-id`.
- Private key 600, `.ssh` directory 700, or `ssh` ignores the key.
- A changed host key is a warning to read, not click past; `ssh-keygen -R host` only after a rebuild you know about.
