# Describing desired state

Ansible is a tool for managing other machines over SSH. Instead of logging in to each one and typing commands, you write down what should be true, "this package is installed", "this file has these contents", "this service is running", and Ansible connects to every machine, checks, and changes only what does not match. If a machine is already right, it does nothing there. That way of working, describing a state rather than listing steps, is what lets one person look after hundreds of servers.

On Pridwen you run Ansible against the Range, the Rocky 9 lab machines you own, not against the desktop itself. The desktop's `/usr` is a read-only image that changes only through `bootc upgrade`, so a playbook that tried to install a package here would fail, and that is the design working: the host is managed by its image, the lab is managed by Ansible. You already have SSH keys installed on a Range host from the SSH node; Ansible uses exactly that access.

## Words you'll meet

- **Ansible**: a tool that applies a described state to remote machines over SSH, from a control machine to targets.
- **control node**: the machine you run Ansible on, your Pridwen desktop here.
- **target**: a machine Ansible manages; a Range host in these lessons.
- **inventory**: a text file listing the targets, and later grouping them.
- **module**: one kind of thing Ansible knows how to do, such as `ping`, `dnf`, or `copy`; each takes parameters describing the goal.
- **task**: one module call with its parameters.
- **ad-hoc command**: a single task run from the command line with `ansible`, without a playbook.
- **become**: running a task through `sudo` on the target, turned on with `-b`.
- **idempotent**: an action that can be repeated safely because it only changes what is not already right.

## How it works

Ansible is not in the Pridwen image, and it is a Python tool with many dependencies, so it belongs in its own environment rather than layered on the host. A Distrobox is the sure way: the box's `dnf` installs it from Fedora's repositories, and because the box shares your home, your inventory, playbooks and SSH keys are all there.

```
{user}@{host}:~$ distrobox enter dev
{user}@dev:~$ sudo dnf install -y ansible-core
{user}@dev:~$ ansible --version | head -1
ansible [core 2.17.5]
```

`pipx install ansible-core` is the other route, giving the command its own isolated Python environment on the host, if `pipx` is available to you. Either way, the rest of this lesson runs the same. The prompt shows `dev` because the commands below are typed inside the box.

Write the inventory. The simplest one is a file with one host per line. `ansible_host` gives the address to connect to when the name is not in DNS, and `ansible_user` the login name on the target.

```
{user}@dev:~$ mkdir -p {home}/range && cd {home}/range
{user}@dev:~/range$ cat > inventory <<'EOF'
web-01 ansible_host=192.168.122.10 ansible_user={user}
EOF
```

Prove connectivity before anything else. The `ping` module does not send a network ping; it logs in over SSH, runs a tiny Python program on the target, and reports back. `-i inventory` names the inventory file, `all` is the pattern meaning every host in it, and `-m ping` picks the module.

```
{user}@dev:~/range$ ansible all -i inventory -m ping
web-01 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
```

Read it back. `web-01 | SUCCESS` is the host and the result. `"changed": false` says nothing was altered, which is right for a check. `"ping": "pong"` is the module's answer. The `discovered_interpreter_python` line says Ansible found Python on the target, which every module needs. If this command works, SSH, the inventory, and the target are all right, and every later failure is something else.

Now a real task: make sure a package is present. `-a` passes the module's parameters as `key=value` pairs, and `-b` means become, so the task runs through `sudo` on the target, because installing a package needs root there just as it would here.

```
{user}@dev:~/range$ ansible web-01 -i inventory -m ansible.builtin.dnf -a "name=nginx state=present" -b
web-01 | CHANGED => {
    "changed": true,
    "msg": "",
    "rc": 0,
    "results": [
        "Installed: nginx-1:1.20.1-20.el9.x86_64"
    ]
}
```

`CHANGED` and `"changed": true` say the package was not there and now is. `"rc": 0` is the return code of the underlying `dnf`. Run the identical command again and it prints `SUCCESS` with `"changed": false`, because `state=present` is already true; that is the idempotence that makes Ansible safe to rerun. The full module name, `ansible.builtin.dnf`, says which collection it comes from; the short `dnf` still works for built-in modules.

If sudo on the target asks for a password, add `-K` (capital), which prompts once for the become password before the run. The target user must be in `wheel` on the Rocky host, the same rule as on Pridwen.

## When it goes wrong

`bash: ansible: command not found` is exit 127 on the host. Ansible lives in the box; `distrobox enter dev` first, or install it with `pipx`.

`web-01 | UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh: {user}@192.168.122.10: Permission denied (publickey,gssapi-keyex,gssapi-with-mic,password).", "unreachable": true}` means SSH itself was refused: your key is not on the target, or `ansible_user` is wrong. Fix it the SSH way, `ssh-copy-id {user}@192.168.122.10`, then run `ssh` by hand once, then `ping` again.

`web-01 | FAILED! => {"msg": "Missing sudo password"}` means `-b` needed a password and none was given. Add `-K`, or configure passwordless sudo for that user on the Range host. If Ansible is aimed at this desktop and fails on a task that writes to `/usr`, that is the immutable image refusing, not a bug; point it at a Range host. `pridwen why` explains the last failure, and `pridwen explain ansible` walks through the flags.

## Try it

1. Enter your Distrobox, install `ansible-core`, and run `ansible --version` to see the core version.
2. Write the one-line inventory for your Range host with its address and your user name.
3. Run `ansible all -i inventory -m ping` and expect `SUCCESS` with `"ping": "pong"`.
4. Change `ansible_user` to a name that does not exist, run `ping` again, and read the `UNREACHABLE` message. Put it back.
5. Run the `dnf` task with `-b` and expect `CHANGED`. Run it a second time and expect `SUCCESS` with `"changed": false`.
6. Run the same task without `-b` and read the error; say in one sentence why `-b` is needed.

## Remember

- Ansible describes a state and changes only what does not match; a second run of the same task changes nothing.
- Always `ansible all -i inventory -m ping` first; if that works, SSH and the inventory are right.
- `-b` runs a task through `sudo` on the target; Ansible manages the Range, and the Pridwen host is managed by its image.
