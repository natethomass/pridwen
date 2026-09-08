# Idempotence and secrets

The property that makes Ansible safe to run on a live server is idempotence: running the same playbook twice changes nothing the second time, because the state it describes is already true. A playbook with that property can be run every night, run after every edit, and run by a nervous colleague, without fear. A playbook without it is a script in disguise, doing something every time whether or not it is needed, and one day the something will be wrong.

The other thing that separates real automation from a personal script is how it handles secrets. A database password has to reach the server, and the playbook that puts it there lives in a repository other people can read. Ansible Vault encrypts the secret at rest so the repository is safe and the playbook still works. You already know how to read a `PLAY RECAP`; this lesson uses its `changed` count as the measure of a good playbook.

## Words you'll meet

- **idempotence**: the property that repeating an action leaves the result unchanged after the first time.
- **check mode**: a run with `--check` that reports what would change without changing it; also called a dry run.
- **diff**: the `--diff` flag, which prints the line-by-line difference a file task would make.
- **changed count**: the `changed=` number in the `PLAY RECAP`; zero on a second run means the playbook is idempotent.
- **Ansible Vault**: the tool, `ansible-vault`, that encrypts files so they can be stored with the playbook.
- **vault password**: the passphrase that unlocks vaulted files, given at run time with `--ask-vault-pass`.
- **variables file**: a YAML file of `key: value` pairs a playbook reads; secrets go in a vaulted one.

## How it works

Start with check mode, inside the Distrobox where Ansible lives and in the `range` directory with your inventory and playbook. `--check` connects to the hosts and works out what each task would do, but does nothing; `--diff` adds the before-and-after of any file it would edit. Together they are how you preview a change on a machine you care about.

```
{user}@{host}:~$ distrobox enter dev
{user}@dev:~$ cd {home}/range
{user}@dev:~/range$ ansible-playbook -i inventory site.yml --check --diff

PLAY [Web servers are set up] **************************************************

TASK [Gathering Facts] *********************************************************
ok: [web-01]

TASK [nginx is installed] ******************************************************
ok: [web-01]

TASK [motd is set] *************************************************************
--- before: /etc/motd
+++ after: /etc/motd
@@ -0,0 +1 @@
+Managed by Ansible. Changes here will be overwritten.
changed: [web-01]

PLAY RECAP *********************************************************************
web-01                     : ok=3    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

The new task copies a login message to `/etc/motd`. The diff shows the file is empty now (`before`) and would gain one line (`after`); the `+` marks the added line. `changed: [web-01]` in check mode means "would change", and nothing on the host has moved. When the preview is what you intended, run without `--check`, then run once more.

```
{user}@dev:~/range$ ansible-playbook -i inventory site.yml | tail -2
PLAY RECAP *********************************************************************
web-01                     : ok=3    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
{user}@dev:~/range$ ansible-playbook -i inventory site.yml | tail -2
PLAY RECAP *********************************************************************
web-01                     : ok=3    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

`tail -2` keeps the last two lines. The first run shows `changed=1`, the second `changed=0`. That second number is the test. If a task reports `changed` every time, it is describing an action rather than a state. The usual culprit is the `command` or `shell` module: `command: systemctl restart nginx` restarts nginx on every run, and Ansible cannot know whether that was needed. Rewrite it as a state, `service: name=nginx state=started`, or, when a command truly is required, add `creates: /path/that/exists/afterwards` so Ansible skips it once the path exists.

Now the secret. `ansible-vault create` opens an editor for a new file and encrypts it when you save; the file on disk is unreadable without the vault password.

```
{user}@dev:~/range$ mkdir -p group_vars/webservers
{user}@dev:~/range$ ansible-vault create group_vars/webservers/vault.yml
New Vault password:
Confirm New Vault password:
```

In the editor, write one variable, `db_password: "a-strong-passphrase"`, and save. The directory name matters: Ansible reads `group_vars/<group>/*.yml` automatically for every host in that group, so no extra flag is needed to load it.

```
{user}@dev:~/range$ head -1 group_vars/webservers/vault.yml
$ANSIBLE_VAULT;1.1;AES256
```

The first line of the file says it is vaulted, and everything after it is ciphertext. A playbook uses the variable as `"{{ db_password }}"` in a task, exactly like any other, and at run time the vault must be unlocked.

```
{user}@dev:~/range$ ansible-playbook -i inventory site.yml --ask-vault-pass
Vault password:
```

`--ask-vault-pass` prompts once for the passphrase. `--vault-password-file ~/.vault-pass` reads it from a file instead, for unattended runs, and that file must then be protected with `chmod 600` and never committed. `ansible-vault edit` reopens a vaulted file and `ansible-vault view` prints it, both after asking for the password.

Between idempotence, check mode, and vault, a playbook becomes something you can run repeatedly, preview before trusting, and share without leaking. That is the difference between automation and a fragile script.

## When it goes wrong

`ERROR! Attempting to decrypt but no vault secrets found` means a vaulted file was loaded and no password was offered. Add `--ask-vault-pass` or `--vault-password-file`.

`ERROR! Decryption failed (no vault secrets were found that could decrypt)` means a password was given and it was wrong, or the file was encrypted with a different one. Try again, or `ansible-vault rekey` the file if the passphrase has changed.

A task that shows `changed` on every run is not idempotent. Look for `command` or `shell` in it, and replace the action with the module that describes the result, or add `creates:`. `pridwen explain ansible-vault` lists the subcommands, and `pridwen why` explains the last failure.

## Try it

1. Add a task to `site.yml` that uses `ansible.builtin.copy` with `content: "Managed by Ansible.\n"` and `dest: /etc/motd`, then run with `--check --diff` and read the diff.
2. Run the playbook for real and expect `changed=1`; run it again and expect `changed=0`.
3. Add a task `ansible.builtin.command: date`, run twice, and watch it report `changed` both times. Remove it.
4. Create `group_vars/webservers/vault.yml` with `ansible-vault create`, put `db_password` in it, and run `head -1` to see the `$ANSIBLE_VAULT` header.
5. Add a `debug` task with `msg: "{{ db_password }}"`, run without a vault flag, and read the `no vault secrets found` error.
6. Run again with `--ask-vault-pass` and see the value printed, then delete the debug task so the secret is never shown again.

## Remember

- A good playbook shows `changed=0` on its second run; a task that always changes is describing an action, not a state.
- `--check --diff` previews a run without changing anything.
- Secrets go in a vaulted file under `group_vars/`, unlocked at run time with `--ask-vault-pass`, and never in plain text.
