# Idempotence and secrets

The property that makes Ansible trustworthy is idempotence: running the same
playbook twice should change nothing the second time, because the state is
already as described. Check mode and the changed count are how you confirm it.

`ansible-playbook --check --diff` performs a dry run, reporting what would change
without changing it, and showing the diff of file edits. A run reports `ok`,
`changed`, and `failed` counts per host; a well-written playbook run twice shows
zero changed the second time. If it always reports changed, a task is describing
an action rather than a state, which is the usual bug.

```
$ ansible-playbook -i inventory site.yml --check --diff
$ ansible-playbook -i inventory site.yml
PLAY RECAP
web-01 : ok=4 changed=1 unreachable=0 failed=0
```

Secrets do not belong in plain text in a playbook. `ansible-vault` encrypts a
file at rest in the repository, and `--ask-vault-pass` or a vault-id file unlocks
it at run time, so a password can be referenced without ever sitting readable on
disk. Between idempotence, check mode, and vault, a playbook becomes something you
can run repeatedly and share safely, which is the difference between automation
and a fragile script.

## Try it

1. Run a playbook with `--check --diff` and read what it would change.
2. Run it for real, then again, and confirm the second run shows zero changed.
3. Encrypt a variables file with `ansible-vault create` and reference it.
4. Explain what makes a task idempotent versus one that always reports changed.
