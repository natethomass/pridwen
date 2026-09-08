# Playbooks and inventory

An ad-hoc command does one task on the hosts you name. A playbook is a file that collects many tasks, in order, against named groups of hosts, so the whole job can be read, reviewed, kept in version control, and run again next month by someone else. The inventory grows to match: instead of one host per line, hosts are grouped under headings, so a play can say "all the web servers" and mean whatever that list contains today.

On a job, the playbook is the document. When a new server is added, it goes into the inventory group and the same playbook makes it match the others; when someone asks how a server was set up, the playbook is the answer. Both files are plain text. You already know from the previous lesson how to run a single module with `ansible` and why `-b` is needed; this lesson puts the same modules into a file.

## Words you'll meet

- **playbook**: a YAML file holding one or more plays.
- **play**: a section of a playbook that names a set of hosts and the tasks to run on them.
- **YAML**: the text format playbooks use; indentation with spaces shows structure, and a `-` starts a list item.
- **group**: a named set of hosts in the inventory, written as `[name]` above the hosts in it.
- **INI format**: the simple inventory style with `[group]` headings, like the file below.
- **syntax check**: reading a playbook for YAML and task errors without connecting to anything.
- **PLAY RECAP**: the summary Ansible prints at the end, with counts per host.

## How it works

Start with the inventory, now with a group. Everything here runs inside the Distrobox where Ansible is installed, so enter it first and go to the `range` directory from the previous lesson. The heading in square brackets is the group name, and every host under it belongs to the group until the next heading.

```
{user}@{host}:~$ distrobox enter dev
{user}@dev:~$ cd {home}/range
{user}@dev:~/range$ cat > inventory <<'EOF'
[webservers]
web-01 ansible_host=192.168.122.10
web-02 ansible_host=192.168.122.11

[webservers:vars]
ansible_user={user}
EOF
```

`[webservers:vars]` sets variables for every host in the group, so `ansible_user` is written once. `ansible-inventory -i inventory --list` prints how Ansible understood the file, which is the quick way to check a grouping.

Now the playbook. YAML is picky: two spaces per level, a colon and a space between a key and its value, and a `-` for each list item. Keep the file simple and the shape will become familiar.

```
{user}@dev:~/range$ cat > site.yml <<'EOF'
- name: Web servers are set up
  hosts: webservers
  become: true
  tasks:
    - name: nginx is installed
      ansible.builtin.dnf:
        name: nginx
        state: present

    - name: nginx is running and enabled
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true
EOF
```

Read it top down. The outer `-` starts one play. `name` is a human label printed when it runs. `hosts: webservers` is the inventory group. `become: true` is the `-b` from the previous lesson, applied to every task in the play. `tasks:` is a list, and each task has a `name`, a module, and the module's parameters indented beneath it. The two tasks describe a state, "installed" and "started and enabled", not a series of commands.

Check the file before running it. `--syntax-check` reads the playbook and reports problems without touching any host.

```
{user}@dev:~/range$ ansible-playbook -i inventory site.yml --syntax-check

playbook: site.yml
```

Silence, apart from the file name, is a pass. Then run it for real.

```
{user}@dev:~/range$ ansible-playbook -i inventory site.yml

PLAY [Web servers are set up] **************************************************

TASK [Gathering Facts] *********************************************************
ok: [web-01]
ok: [web-02]

TASK [nginx is installed] ******************************************************
ok: [web-01]
changed: [web-02]

TASK [nginx is running and enabled] ********************************************
changed: [web-01]
changed: [web-02]

PLAY RECAP *********************************************************************
web-01                     : ok=3    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web-02                     : ok=3    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Each `TASK` block shows one line per host. `ok` means the state was already right and nothing was done; `changed` means Ansible made it right. `Gathering Facts` is an automatic first task that collects details about each host. In the `PLAY RECAP`, `ok` counts tasks that succeeded (including changed ones), `changed` counts the ones that altered something, and `unreachable` and `failed` should be zero. web-01 already had nginx from the previous lesson, so only its service task changed; web-02 needed both. Running the playbook again would show `changed=0` on both, because everything it describes is now true.

## When it goes wrong

`ERROR! We were unable to read either as JSON nor YAML, these are the errors we saw in the last attempt:` followed by a line and column number is a YAML mistake, usually indentation or a missing space after a colon. Open the file at that line, compare with the shape above, and run `--syntax-check` again until it passes.

`[WARNING]: Could not match supplied host pattern, ignoring: webservers` followed by `skipping: no hosts matched` means the group name in `hosts:` does not match a heading in the inventory, or you forgot `-i inventory`. Check the spelling in both files, and use `ansible-inventory -i inventory --list` to see the groups Ansible found.

A run ending with `unreachable=1` and exit status 4 is SSH, almost always: the key is not on that host or the address is wrong. Go back to `ansible all -i inventory -m ping` and fix the host it names before rerunning the playbook. `pridwen why` explains the exit status, and `pridwen explain ansible-playbook` lists the flags.

## Try it

1. Write the inventory with a `[webservers]` group holding two Range hosts, and run `ansible-inventory -i inventory --list` to see them grouped.
2. Write `site.yml` as above and run `ansible-playbook -i inventory site.yml --syntax-check`; expect `playbook: site.yml` and nothing else.
3. Remove two spaces from in front of `name: nginx` under the `dnf` task, run the syntax check, and read the error and its line number. Put the spaces back.
4. Run the playbook for real and read the `PLAY RECAP`; note which hosts show `changed`.
5. Run it again and expect `changed=0` on every host.
6. On one Range host, run `systemctl is-active nginx` over SSH and expect `active`, confirming the playbook did what it said.

## Remember

- An inventory groups hosts under `[name]` headings; a play targets a group, not a list of addresses.
- Always `ansible-playbook --syntax-check` first; YAML errors are indentation or a missing space after a colon.
- Read the `PLAY RECAP`: `ok` is fine, `changed` is work done, `unreachable` and `failed` must be zero, and a second run should change nothing.
