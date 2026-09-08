# Keys and secrets that hold

The way out of the guessing game is to stop relying on a secret small enough to
guess. An SSH key, a second factor, and a lockout each change the attacker's
arithmetic, and understanding why is the payoff of this whole node. The goal is
a login that has nothing worth guessing at, and a secret that cannot be stolen
from the server because it was never on the server.

Everything here runs only against Range targets you own: Rocky 9 lab hosts you
start with `pridwen enter rocky`, where you may turn SSH on and off and edit its
config freely. You never change the login config of a system you do not control.
On a real job this is the single change that makes the endless password-guessing
noise in your logs simply stop finding a door.

## Words you'll meet

- **key pair**: two matched files, a private key you keep secret and a public key you can hand out; what one locks, the other unlocks.
- **SSH**: Secure Shell, the service that gives you an encrypted command line on another machine.
- **ed25519**: a modern, compact key type that is fast and strong; the sensible default for a new key.
- **authorized_keys**: the file on the server listing the public keys allowed to log in as an account.
- **PasswordAuthentication**: the sshd setting that decides whether passwords are accepted at all.
- **revoke**: to cancel a credential, here by deleting a public key from `authorized_keys`.

## How it works

A key pair replaces a guessable password with a secret far too large to guess.
You generate the pair once. The `-t ed25519` flag picks the key type; ed25519 is
the modern default:

```
{user}@{host}:~$ ssh-keygen -t ed25519 -f {home}/.ssh/range_key
Generating public/private ed25519 key pair.
Your identification has been saved in {home}/.ssh/range_key
Your public key has been saved in {home}/.ssh/range_key.pub
```

Read that back. `-f` names the output file, so the private key lands at
`{home}/.ssh/range_key` and the public half at `{home}/.ssh/range_key.pub` with
the `.pub` suffix. Only the public half ever leaves your machine. You copy it to
the Range host with `ssh-copy-id`, which appends it to that account's
`authorized_keys`:

```
{user}@{host}:~$ ssh-copy-id -i {home}/.ssh/range_key.pub labuser@range-01
Number of key(s) added: 1
```

Here `-i` names the public key file to install. Now the account can log in with
the key. The last step is to shut the password door on the Range host so online
guessing has nothing to aim at. You drop a small config file into sshd's
drop-in directory, which is read on top of the main config:

```
labuser@range-01:~$ sudo tee /etc/ssh/sshd_config.d/20-nopw.conf <<'EOF'
PasswordAuthentication no
EOF
labuser@range-01:~$ sudo systemctl reload sshd
```

The `tee` command writes what the here-document (`<<'EOF' ... EOF`) feeds it
into the file, and `systemctl reload sshd` tells the running service to re-read
its config. With `PasswordAuthentication no`, sshd stops accepting passwords
entirely, so the guessing attempts that used to fill the log now hit a service
with no password field. Revocation is just as direct: delete the public key line
from `authorized_keys` and that key can no longer log in, which you cannot do
with a shared password nobody can rotate.

## When it goes wrong

`Permission denied (publickey)` after you turn passwords off means the key is
not being offered or is not in `authorized_keys`. Confirm the public key is
installed for that account, and that the private key's permissions are tight
(`chmod 600` on the private file), which sshd insists on.

`sign_and_send_pubkey: no mutual signature algorithm` usually means the key type
is not accepted by the server config; generate an `ed25519` key, which modern
sshd accepts by default.

`Could not open a connection to your authentication agent` when adding keys
means no ssh-agent is running; that is about convenience, not the login itself,
and `pridwen explain ssh` walks through the pieces.

## Try it

1. On your host, generate an `ed25519` key pair with `ssh-keygen -t ed25519 -f {home}/.ssh/range_key`.
2. Install the public half on a Range host with `ssh-copy-id` and log in once to confirm the key works.
3. Set `PasswordAuthentication no` in a drop-in on the Range host and reload sshd.
4. Confirm a password login is now refused while the key login still works.
5. Remove the key line from `authorized_keys` and explain how that revokes access.

## Remember

- A key pair keeps the private secret off the server, so a secret that was never there cannot be stolen from there.
- `PasswordAuthentication no` removes online password guessing against SSH completely, which is why the SSH node teaches keys first.
- Keys are revocable one at a time by editing `authorized_keys`, unlike a shared password that nobody can rotate.
