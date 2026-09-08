# Seeing what runs

A process is a running program. Every time you start something, whether by
typing a command or clicking an icon, the kernel (the core of the operating
system that hands out CPU time and memory) creates a process for it and gives it
a number called a pid, short for process id. Your terminal is a process, your
shell is a process, and so is every window on the screen. Two tools show them to
you: `ps` takes a snapshot and prints it, and `top` keeps updating on screen.

This matters on Pridwen because a lot of what the system does happens in the
background, and the first question in almost any problem is "what is running
and what is it costing". On a job, a slow server, a stuck update, or a strange
program nobody recognises all start with the same look at the process list.

## Words you'll meet

- **process**: a program that is running right now, with its own memory and its own pid.
- **pid**: process id, the number the kernel uses to name one process; nothing else has that number while the process lives.
- **kernel**: the core of Linux that starts processes, shares the CPU between them, and keeps them apart.
- **snapshot**: a picture of the process list at one instant, which is what `ps` prints.
- **load average**: how many processes wanted the CPU on average over the last one, five, and fifteen minutes.
- **core**: one CPU that can run one process at a time; `nproc` counts how many you have.
- **Distrobox**: a mutable container that shares your home directory, where `dnf install` works when a tool is not in the Pridwen image.

## How it works

`ps` with no options shows only the processes attached to your current
terminal, which is usually just your shell and `ps` itself. The phrase to
remember is `ps aux`: `a` means every user's processes, not only yours, `u`
means the user-oriented format that adds the owner and the CPU and memory
percentages, and `x` includes processes that have no terminal at all, which is
most of the system. These three letters are written without a dash because
`ps` accepts the old BSD style as well as the dashed style.

```
{user}@{host}:~$ ps aux | head -n 4
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root           1  0.1  0.3  25460 14212 ?        Ss   09:00   0:02 /usr/lib/systemd/systemd
root           2  0.0  0.0      0     0 ?        S    09:00   0:00 [kthreadd]
{user}      1955  1.2  4.1 1234567 165432 ?      Ssl  09:01   0:41 /usr/bin/gnome-shell
```

`head -n 4` keeps the first four lines so the output fits on the screen. Read
the columns left to right. USER is who the process runs as. PID is its number;
pid 1 is always systemd, the first process, which starts everything else. %CPU
and %MEM are the share of the processor and of memory it is using. VSZ and RSS
are memory sizes in kilobytes; RSS, the resident set, is the one that is really
in RAM. TTY is the terminal it is attached to, and `?` means none. STAT is the
state: `S` sleeping, waiting for something to happen, `R` running, `Z` zombie,
finished but not yet collected by its parent. START and TIME are when it began
and how much CPU time it has used in total. COMMAND is the program, and a name
in square brackets like `[kthreadd]` is a kernel thread, not a program you can
find on disk.

You can pick your own columns with `-o` and limit the list to one user with
`-u`. Here `comm` is the short command name without its arguments.

```
{user}@{host}:~$ ps -o pid,user,%cpu,comm -u $USER | head -n 4
    PID USER     %CPU COMMAND
   1820 {user}      0.0 systemd
   1955 {user}      1.2 gnome-shell
   4242 {user}      0.0 bash
```

The first line is the header. The `systemd` at the top is your own user
manager, a copy of systemd that runs your session; `gnome-shell` is the desktop;
`bash` is the shell reading this terminal. A normal desktop has a few hundred
processes and nearly all of them are sleeping.

Piping `ps` into other tools narrows it. `--sort=-%mem` sorts by memory with the
largest first (the minus sign means descending), so `ps aux --sort=-%mem | head`
names your biggest memory users. `pridwen explain ps` annotates any flag you
meet.

```
{user}@{host}:~$ ps aux --sort=-%mem | head -n 3
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
{user}      2210  2.3  9.8 4501234 398765 ?      Sl   09:02   1:12 /usr/bin/firefox
{user}      1955  1.2  4.1 1234567 165432 ?      Ssl  09:01   0:41 /usr/bin/gnome-shell
```

`top` shows the same information live and refreshes every three seconds.
Inside it, press `M` to sort by memory, `P` to sort by CPU, `k` to send a
signal to a pid (the next lesson explains signals), and `q` to quit. Its first
line is the same as the output of `uptime`.

```
{user}@{host}:~$ uptime
 10:14:02 up  1:14,  1 user,  load average: 0.52, 0.71, 0.66
{user}@{host}:~$ nproc
4
```

The three load numbers are the load average over one, five, and fifteen
minutes. Compare them with `nproc`, the number of cores. A load of 0.52 on four
cores means the machine is mostly idle; a load that stays above 4 means
processes are queueing for the CPU and the machine is overloaded, not merely
busy.

`htop` is a friendlier `top`, but it is not in the Pridwen image, because the
base is a read-only image and only what is shipped is present. Run it from a
Distrobox, or layer it with `rpm-ostree install htop` if you want it on the
host after a reboot.

## When it goes wrong

`bash: htop: command not found` means the program is not in the image. Use
`top`, or `distrobox enter` a box and `sudo dnf install htop` there.

`ps: user name does not exist` appears when `-u` is given a name that is not an
account on this machine; check the spelling, or use `-u $USER` for yourself.

`error: garbage option` from `ps` usually means the BSD and dashed styles were
mixed, such as `ps -aux`. Write `ps aux` without the dash, or `ps -e -o
pid,user,comm` with it. `pridwen why` translates the message when it appears.

## Try it

1. Run `ps aux | head` and point to the USER column and the COMMAND column in the header.
2. Run `ps aux --sort=-%mem | head` and say which program is using the most memory.
3. Run `ps -o pid,user,comm -u $USER` and find the `bash` line; that is the shell you are typing into.
4. Open `top`, press `M`, then `P`, watch the order change, and quit with `q`.
5. Run `uptime` and `nproc` and decide whether your machine is busy or idle.

## Remember

- A process is a running program with a pid; `ps aux` lists them all, `top` watches them live.
- USER, PID, %CPU, %MEM and COMMAND are the columns that answer most questions.
- Load average above the core count from `nproc` means overloaded; below it means busy at most.
