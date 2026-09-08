# The baseline as data

Hardening means closing the small doors an attacker would use, before anyone tries them. On many systems hardening is a script somebody ran once, and nobody can say afterwards what it changed or why. Pridwen does it differently: every hardening decision is written down as configuration you can read, check against what it should be, and explain. That is what "the baseline as data" means, and it is why the Academy's posture panel can show you each control as a lesson rather than a mystery.

The kernel side of the baseline is a set of sysctl values. On a job, an auditor will ask "what is `kernel.kptr_restrict` set to and why", and the answer has to come from the system, not from memory. This lesson shows you how to read those values, how to change one, and where the permanent copy lives. You have already used `sudo` to run one command as root; you will need it again here, because writing a kernel setting is an administrator's job.

## Words you'll meet

- **kernel**: the core of the operating system, the program that owns the hardware and decides what every other program may do.
- **sysctl**: a kernel tunable, a named setting you can read and change while the system runs; also the command that reads and writes them.
- **baseline**: the agreed set of values a hardened system should have, written down so drift from it can be spotted.
- **ring buffer**: the kernel's own log of messages, the one `dmesg` prints.
- **persistent**: a change that survives a reboot because it is stored in a file the system reads at start-up.
- **drift**: any difference between the running system and its baseline.
- **posture**: Pridwen's word for the state of the baseline on your machine, shown in the Academy app.

## How it works

A sysctl has a dotted name. The part before the first dot is the subsystem (`kernel`, `net`, `fs`, `vm`), and the rest names one setting inside it. Reading one needs no root, because reading a value reveals nothing an ordinary user could not learn another way.

```
{user}@{host}:~$ sysctl kernel.dmesg_restrict
kernel.dmesg_restrict = 1
```

The output is the name, an equals sign, and the current value. A `1` here means only root may read the kernel ring buffer. That matters because kernel messages leak the addresses and driver details an exploit needs, so Pridwen keeps them from ordinary users. You can pass several names at once.

```
{user}@{host}:~$ sysctl kernel.kptr_restrict net.ipv4.ip_forward kernel.yama.ptrace_scope
kernel.kptr_restrict = 2
net.ipv4.ip_forward = 0
kernel.yama.ptrace_scope = 1
```

Read them back one line at a time. `kernel.kptr_restrict = 2` hides kernel memory addresses from everyone, even root, because a leaked address is the first step of most kernel exploits. `net.ipv4.ip_forward = 0` says this machine is not a router: packets that arrive for another address are dropped, not passed along, which stops a compromised desktop being used as a hop into the rest of the network. `kernel.yama.ptrace_scope = 1` means a process may only be inspected by its own parent, so a stray program cannot attach to your terminal or your password manager and read its memory. Each value is a small door, and each one is closed on purpose.

To change a value for the running kernel you use the `-w` flag, which means write. It needs root, so the command starts with `sudo`.

```
{user}@{host}:~$ sudo sysctl -w net.ipv4.ip_forward=1
net.ipv4.ip_forward = 1
```

The command echoes the new value. This change lives only in the running kernel: at the next reboot the kernel starts with its built-in defaults and reads the configuration files again, so the `-w` change is gone. That is by design, so that an experiment never quietly becomes permanent.

The permanent values live in files under `/etc/sysctl.d/`. Each file holds `name = value` lines, and the files are read in name order at boot, so a file named `99-local.conf` wins over one named `50-pridwen.conf`.

```
{user}@{host}:~$ ls /etc/sysctl.d/
50-pridwen-hardening.conf  99-sysctl.conf
{user}@{host}:~$ grep -v '^#' /etc/sysctl.d/50-pridwen-hardening.conf | head -5
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1
net.ipv4.ip_forward = 0
kernel.unprivileged_bpf_disabled = 1
```

`grep -v '^#'` hides comment lines (`-v` means invert, print lines that do not match, and `^#` matches a line starting with a hash) and `head -5` shows the first five. The file is the baseline written as data: one setting per line, readable by anyone. `sudo sysctl --system` reads every file in the directory and applies it to the running kernel, which is the way to make a file change take effect without rebooting.

Because `/etc` is kept across `bootc upgrade` with a three-way merge, a file you add there stays, and Pridwen's own file is updated when the image changes. The posture panel in Academy reads the same files and the same running values, and reports the difference, which is all drift detection is.

## When it goes wrong

`sysctl: permission denied on key "net.ipv4.ip_forward"` comes from `sysctl -w` without `sudo`. Reading is open to everyone; writing is root's job. Put `sudo` in front and try again.

`sysctl: cannot stat /proc/sys/kernel/dmesg_restric: No such file or directory` means the name is misspelled. Every sysctl is also a file under `/proc/sys/` with the dots turned into slashes, so a typo in the name is a missing file. Use `sysctl -a | grep dmesg` to list every name containing the word (`-a` means all).

The change you made with `-w` is gone after a reboot. That is not a failure; it is how `-w` works. Put the line in a file under `/etc/sysctl.d/` and run `sudo sysctl --system`. If the Coach printed a hint after your `sysctl` command, `pridwen why` explains it in full, and `pridwen explain sysctl` walks through the flags.

## Try it

1. Run `sysctl kernel.dmesg_restrict kernel.kptr_restrict net.ipv4.ip_forward` and expect `1`, `2` and `0`. Say out loud what each one protects.
2. Run `sudo sysctl -w net.ipv4.ip_forward=1`, then `sysctl net.ipv4.ip_forward`, and expect it to read `1` now.
3. Run `sudo sysctl --system` and read the lines it prints as it applies each file, then read the value again and expect it back at `0`.
4. Run `ls /etc/sysctl.d/` and `cat` the Pridwen file. Find the line for `kernel.yama.ptrace_scope`.
5. Run `sysctl -a | grep -c .` to count how many tunables the kernel exposes (`-c` counts matching lines).
6. Open the Academy app from the dock and find the sysctl control in the posture panel; it should show the same values you just read.

## Remember

- `sysctl name` reads, `sudo sysctl -w name=value` writes until the next reboot, and files in `/etc/sysctl.d/` are the permanent copy.
- Pridwen's hardening is written as data so you can read it, check it, and explain every value.
- A hardening value you turn off for a lab is a door you opened; know which one before you do it.
