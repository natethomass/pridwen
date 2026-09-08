# Signals and kill

Stopping a process means sending it a signal. A signal is a small numbered
message that the kernel (the core of the operating system) delivers to a
process, and the process decides what to do about it. The command that sends
one is `kill`, and despite the name most signals are polite requests rather than
force. A process is a running program with a number called a pid, and `kill`
needs that number.

This matters because programs hang, loops run away, and on a real server a
stuck process can hold a port or a file everyone else needs. Knowing the
difference between asking a program to stop and forcing it to stop is the
difference between a clean recovery and lost data.

## Words you'll meet

- **signal**: a numbered message the kernel delivers to a process, such as "please stop".
- **pid**: process id, the number the kernel uses to name one running process.
- **SIGTERM**: signal 15, "terminate", the polite request to shut down; the program may save and close files first.
- **SIGKILL**: signal 9, which the kernel enforces itself; the process cannot catch it and ends at once.
- **catch**: when a program has asked to be told about a signal so it can react, rather than die immediately.
- **uid**: user id, the number behind your login name; the kernel compares uids to decide who may signal whom.
- **unit**: a service managed by systemd; a service is better stopped through its unit than by signal.

## How it works

`kill` takes a pid and sends it a signal. With no option it sends SIGTERM, number
15, which asks the program to shut down cleanly. Most programs catch SIGTERM,
finish what they were doing, save, and exit. To find the pid, use `pgrep`,
which searches the process list by name; `-a` makes it print the full command
line next to the pid so you can see exactly what you found.

```
{user}@{host}:~$ sleep 600 &
[1] 5001
{user}@{host}:~$ pgrep -a sleep
5001 sleep 600
{user}@{host}:~$ kill 5001
{user}@{host}:~$ pgrep sleep || echo gone
gone
```

The `&` after `sleep 600` starts it in the background so you get your prompt
back; the shell prints `[1] 5001`, job number one, pid 5001. `pgrep -a sleep`
confirms that pid 5001 is `sleep 600`. `kill 5001` prints nothing, which is
success: the signal was delivered. The last line uses `||`, which runs the
right-hand command only if the left one failed; `pgrep` fails when it finds
nothing, so `gone` means the process has ended.

To send a different signal, name it or number it: `kill -TERM 5001`,
`kill -15 5001` and plain `kill 5001` are the same. `kill -l` lists every
signal. The one you will hear about most is SIGKILL, number 9.

```
{user}@{host}:~$ kill -l | head -n 2
 1) SIGHUP       2) SIGINT       3) SIGQUIT      4) SIGILL       5) SIGTRAP
 6) SIGABRT      7) SIGBUS       8) SIGFPE       9) SIGKILL     10) SIGUSR1
```

SIGKILL cannot be caught. The kernel ends the process immediately, with no
chance to flush its buffers, remove its temporary files, or tell anyone it is
going. That is why `kill -9` is a last resort, used only after SIGTERM was sent
and ignored for a few seconds. Sending it first can leave half-written files
and lock files behind. `pridwen explain kill` annotates the signal flags.

`kill` wants a pid, not a name. To signal by name, use `pkill name`, which
sends the signal to every process whose name matches. Because it matches, look
first with `pgrep -a name` so you see everything that would be hit.

```
{user}@{host}:~$ sleep 300 & sleep 400 &
[1] 5120
[2] 5121
{user}@{host}:~$ pgrep -a sleep
5120 sleep 300
5121 sleep 400
{user}@{host}:~$ pkill sleep
[1]-  Terminated              sleep 300
[2]+  Terminated              sleep 400
```

Both sleeps are gone and the shell reports each one as `Terminated`, which is
the SIGTERM default doing its job. On Pridwen the older `killall` command from
the psmisc package is not in the image; `pkill`, from procps, does the same job
and is what to type.

Who may signal whom is decided by the kernel, not by `kill`. It compares your
uid with the uid of the target process. You may signal only processes that run
as you. A process owned by root or another user needs `sudo`, and a system
service is better stopped with `systemctl stop unit` so systemd knows it was
meant to stop and does not treat it as a crash. This rule is why one user's
runaway loop cannot take down another user's session or a system daemon.

## When it goes wrong

`kill: (5001): No such process` means there is no process with that pid any
more. It already exited, or the pid was typed wrong. Run `pgrep -a name` to
find the current pid and try again.

`kill: (1234): Operation not permitted` means the process runs as a different
user. `ps -o user=,comm= -p 1234` shows who owns it and what it is. If it is a
service, use `sudo systemctl stop unit`; if it is a plain process you really
mean to end, `sudo kill 1234`.

`bash: kill: firefox: arguments must be process or job IDs` means a name was
given where a pid belongs. Use `pkill firefox`, or find the pid with
`pgrep -a firefox` first. `pridwen why` explains whichever of these you just saw.

## Try it

1. Run `sleep 300 &` and write down the pid the shell prints after the job number.
2. Run `pgrep -a sleep` and confirm the pid matches.
3. Run `kill` followed by that pid, then `pgrep sleep || echo gone`, and expect `gone`.
4. Start two sleeps with `sleep 300 & sleep 400 &`, then stop both with `pkill sleep`.
5. Run `kill -l` and find the numbers for SIGTERM and SIGKILL.
6. Say out loud when `kill -9` is justified and what it costs the program.

## Remember

- `kill pid` sends SIGTERM, a polite request; `kill -9 pid` sends SIGKILL, which cannot be refused, so use it last.
- `pgrep -a name` finds pids by name and `pkill name` signals them; `killall` is not in the image.
- You can only signal your own processes; other users' need `sudo`, and services should be stopped with `systemctl`.
