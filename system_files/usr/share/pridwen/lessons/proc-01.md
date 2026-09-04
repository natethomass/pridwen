# Seeing what runs

A process is a running program with a number, its pid. Two tools show them.
`ps` takes a snapshot and prints it; `top` updates live. Between them you can
answer what is running, who started it, and what it is costing.

`ps aux` is the phrase to remember: every process, with the user, pid, CPU and
memory percentages, and the command. Piping it to `grep` or `sort` narrows it,
as in `ps aux --sort=-%mem | head` for the biggest memory users.

```
$ ps -o pid,user,%cpu,comm -u $USER | head -n 4
    PID USER     %CPU COMMAND
   1820 nate      0.0 systemd
   1955 nate      1.2 gnome-shell
   4242 nate      0.0 bash
```

`top` is interactive: `M` sorts by memory, `P` by CPU, `k` sends a signal, and
`q` quits. The load average on its first line counts processes wanting the CPU,
averaged over one, five, and fifteen minutes; compared against `nproc` cores it
tells you whether the machine is merely busy or actually overloaded. `htop` is
nicer but is not in the base image, so layer it or run it from a Distrobox.

## Try it

1. Run `ps aux | head` and identify the user and command columns.
2. Run `ps aux --sort=-%mem | head` and name your top memory user.
3. Open `top`, press `M` then `P`, and quit with `q`.
4. Run `uptime` and compare the load average against `nproc`.
