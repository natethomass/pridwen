# Playbooks and inventory

A playbook collects tasks into a repeatable file, and an inventory lists the
hosts to run them on. Together they turn one-off commands into something you can
review, version, and run again with confidence.

The inventory groups hosts under names, so a play can target `webservers` rather
than a list of addresses. A playbook is YAML: a play names its hosts and lists
tasks, each with a module and its parameters and a human name. Because YAML is
picky about indentation, checking syntax before running saves time.

```
# inventory.ini
[webservers]
web-01
web-02

# site.yml
- hosts: webservers
  become: true
  tasks:
    - name: nginx is installed
      ansible.builtin.dnf: { name: nginx, state: present }
```

`ansible-playbook --syntax-check site.yml` catches YAML and task errors before
anything runs, and exit 4 from a run means hosts were unreachable, almost always
SSH or an inventory typo, so `ansible all -m ping` is the first thing to try.
Building the inventory into groups is what lets one playbook scale from one host
to many without change, which is the payoff over running commands by hand.

## Try it

1. Write an inventory with a group holding two Range hosts.
2. Write a short playbook that ensures a package is present.
3. Run `ansible-playbook --syntax-check` and fix any indentation error.
4. Run it for real with `-b` and confirm the change on the target.
