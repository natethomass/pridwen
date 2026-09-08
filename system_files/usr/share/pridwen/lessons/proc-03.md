# Jobs and staying alive

The shell can run more than one thing at once. Normally a command takes over
the terminal until it finishes; that is a foreground command. A command
followed by `&` starts in the background and hands the prompt back at once.
The shell keeps a list of the commands it started and has not finished with,
and it calls them jobs. You can stop a job, move it between foreground and
background, and bring it back.

This matters because long commands are common: a download, a build, a backup.
On a server you may start something and need the terminal for other work while
it runs, and you need to know what happens to it when you log out. The habits
here are the ones that stop a closed window from silently ending a job you
needed.

## Words you'll meet

- **foreground**: the command currently holding the terminal; your keystrokes go to it and the prompt waits.
- **background**: a command running without the terminal; the prompt is free while it works.
- **job**: a command your current shell started and still tracks, numbered from 1.
- **Ctrl-Z**: the key that sends SIGTSTP, the "stop" signal, which pauses the foreground command.
- **SIGHUP**: the "hang up" signal, sent to a shell's jobs when the terminal closes; most programs exit on it.
- **nohup**: a wrapper that makes a command ignore SIGHUP so it survives the terminal closing.
- **unit**: a piece of work managed by systemd, the service manager; a transient unit is one created on the spot.

## How it works

Start a command with `&` and the shell prints two numbers: the job number in
square brackets and the pid, the process id the kernel gave it. `jobs` lists
the jobs of this shell with their state.

```
{user}@{host}:~$ sleep 300 &
[1] 5100
{user}@{host}:~$ jobs
[1]+  Running                 sleep 300 &
```

`[1]` is job one. The `+` marks the current job, the one `fg` and `bg` act on
if you name none. `Running` is its state, and the command follows. `fg %1`
brings job one to the foreground, where it holds the terminal again. Pressing
Ctrl-Z while it is there stops it: the shell shows `^Z` and reports the job as
`Stopped`. A stopped job is paused, not ended; it uses no CPU and waits.

```
{user}@{host}:~$ fg %1
sleep 300
^Z
[1]+  Stopped                 sleep 300
{user}@{host}:~$ bg %1
[1]+ sleep 300 &
{user}@{host}:~$ jobs
[1]+  Running                 sleep 300 &
```

`bg %1` resumes the stopped job in the background, and `jobs` shows it running
again. The `%1` is how you name a job; with only one job the number can be
left out. This stop-and-background dance is the everyday way to rescue a
terminal from a command you started without `&`.

Background jobs belong to the shell that started them. When you close the
terminal window or log out, the shell sends SIGHUP, the hang-up signal, to its
jobs, and most programs exit when they receive it. `nohup command &` starts
the command with SIGHUP ignored, so it survives, and because its output has
nowhere to go once the terminal is gone, `nohup` writes it to a file called
`nohup.out` in the current directory.

```
{user}@{host}:~$ nohup sleep 60 &
[1] 5230
nohup: ignoring input and appending output to 'nohup.out'
{user}@{host}:~$ ls nohup.out
nohup.out
```

The message is informational, not an error: it tells you where the output is
going. For anything that should really keep running, though, a systemd unit is
the better tool. systemd is the service manager that starts and watches every
service on the system, and it also runs a manager for your user session.
`systemd-run --user command` asks your user manager to run the command as a
transient unit, a unit that exists only until it finishes. The `--user` flag
means your own manager, no root needed. The unit gets a name, its output goes
to the journal (the system log, read with `journalctl`), and `systemctl --user
stop name` ends it cleanly. A bare background job has none of that.

```
{user}@{host}:~$ systemd-run --user --on-active=10s true
Running timer as unit: run-r3f7c1a2e.timer
Will run service as unit: run-r3f7c1a2e.service
{user}@{host}:~$ systemctl --user list-timers | head -n 2
NEXT                        LEFT LAST PASSED UNIT                 ACTIVATES
Mon 2026-09-07 10:20:15 UTC   9s -    -      run-r3f7c1a2e.timer  run-r3f7c1a2e.service
```

`--on-active=10s` turns the request into a timer that fires ten seconds after
it was created, and `true` is a command that does nothing and succeeds. The
first output line names the timer unit and the second names the service it
will start. `list-timers` shows NEXT, when it fires, LEFT, how long until
then, and which UNIT ACTIVATES which service. After it runs, both units
disappear because they were transient. The Services node covers units in full;
the one-sentence version is that a unit is systemd's name for a thing it
manages.

Finding out which process holds a file or a port is part of the same skill.
`lsof` is not in the Pridwen image; `ss -tlnp` lists listening TCP ports with
the owning process, and `fuser -v file` shows who has a file open.

## When it goes wrong

`bash: fg: current: no such job` means this shell has no stopped or background
job. Jobs belong to the shell that started them, so a job from another tab is
not visible here. Run `jobs` to see what this shell has.

`[1]+  Hangup                  sleep 300` after a terminal closed means the job
received SIGHUP and exited. Start it with `nohup`, or run it as a unit with
`systemd-run --user`, if it must outlive the terminal.

`Failed to connect to bus: No such file or directory` from `systemd-run --user`
means there is no user manager in this session, which happens over a bare
`sudo` shell. Run it as yourself, without `sudo`. `pridwen why` explains the
last of these you saw.

## Try it

1. Run `sleep 300 &`, then `jobs`, and read the job number and the word `Running`.
2. Run `fg`, press Ctrl-Z, and expect `[1]+  Stopped                 sleep 300`.
3. Run `bg`, then `jobs`, and see it `Running` again; end it with `kill %1`.
4. Run `nohup sleep 60 &`, read the message, and `cat nohup.out` after a minute (it will be empty, because `sleep` prints nothing).
5. Run `systemd-run --user --on-active=10s true` and find the timer in `systemctl --user list-timers`.
6. Run `ss -tlnp` and read which process, if any, is listening on a port.

## Remember

- `&` starts a job in the background; Ctrl-Z stops the foreground one; `jobs`, `fg` and `bg` manage them.
- Jobs die with the terminal unless started with `nohup`; output then goes to `nohup.out`.
- Anything that should really keep running belongs in a systemd unit, and `systemd-run --user` makes one on the spot.
