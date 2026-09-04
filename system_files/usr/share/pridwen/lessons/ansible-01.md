# Describing desired state

Ansible applies a described state to machines over SSH. Instead of a script of
steps, you write tasks that say what should be true, and Ansible makes it so,
skipping anything already correct. On Pridwen you use it to manage Range hosts,
not the immutable desktop itself.

Ansible is not in the base image; install it in its own environment with `pipx
install ansible-core`, or run it from a Distrobox. It needs SSH access to the
targets, so your key must be installed on them, exactly the setup from the SSH
node. A task uses a module, like `dnf` or `copy`, with the parameters that
describe the goal.

```
$ pipx install ansible-core
$ ansible all -i inventory -m ping
web-01 | SUCCESS => {"ping": "pong"}
$ ansible web-01 -i inventory -m dnf -a "name=nginx state=present" -b
```

The `-b` flag means become, running the task through sudo on the target, so the
target user needs to be in wheel there just as on Pridwen. Running Ansible
against the local immutable host fails on anything that writes to `/usr`, which is
why the targets are Range machines. Start every project by proving connectivity
with the `ping` module before writing real tasks.

## Try it

1. Install ansible-core with pipx and confirm `ansible --version`.
2. Write a two-line inventory listing a Range host.
3. Run the `ping` module against it and read the SUCCESS line.
4. Explain why `-b` is needed for a task that installs a package.
