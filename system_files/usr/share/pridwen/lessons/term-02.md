# Exit codes and history

Every command you run is a small program, and when a program finishes it hands one number back to the shell. That number is its exit code (also called exit status). Zero means "it worked". Anything else means "something went wrong", and the value says roughly what. You do not usually see the number, because a command that worked simply prints its result and a command that failed usually prints an error message, but the number is always there underneath.

This matters on Pridwen because the Coach, the helper that prints one line under a failed command, decides that a command failed by reading its exit code. It matters on a real job because scripts and automation tools make every decision the same way: `if this command exited zero, carry on; otherwise stop`. Learning to read exit codes now means your future scripts will fail loudly instead of silently. The second half of this lesson is history, the shell's memory of what you typed, which turns retyping into recalling.

## Words you'll meet

- **exit code**: the number a program returns when it finishes; 0 is success, anything else is a failure.
- **`$?`**: a special shell variable that holds the exit code of the last command.
- **variable**: a named slot the shell stores text in; you read it by putting `$` in front of the name.
- **signal**: a short message the system sends to a running program, such as "stop now".
- **SIGINT**: signal number 2, the interrupt that Ctrl-C sends to the program in front of you.
- **history**: the list of command lines you have typed, kept by the shell in `{home}/.bash_history`.
- **PATH**: the list of directories the shell searches when you type a command name.

## How it works

Run a command that cannot work, then ask the shell for the code. `echo` prints whatever you give it, and `$?` is replaced by the last exit code before `echo` runs.

```
{user}@{host}:~$ ls /nope
ls: cannot access '/nope': No such file or directory
{user}@{host}:~$ echo $?
2
```

The first line of output is `ls` complaining: it tried to open `/nope` and the system said no such thing exists. The `2` on the next line is the exit code `ls` chose for that kind of trouble. Now run something that works. `true` is a tiny program whose only job is to succeed.

```
{user}@{host}:~$ true; echo $?
0
```

The semicolon lets you put two commands on one line; the second runs after the first. Because `$?` is overwritten by every command, you must read it immediately, before running anything else. Even `ls` would replace it.

A few values recur often enough to learn by heart. `1` is a general failure with no more detail. `2` from the GNU tools (`ls`, `grep`, `cp` and friends) usually means a usage problem or a path that does not exist. `126` means the file was found but could not be run, most often because it lacks the execute permission. `127` means the command was not found anywhere on your PATH, which usually means a typo. Values above 128 mean a signal stopped the program: subtract 128 to get the signal number. So `130` is 128 plus 2, and signal 2 is SIGINT, the one Ctrl-C sends.

```
{user}@{host}:~$ sleep 60
^C
{user}@{host}:~$ echo $?
130
```

`sleep 60` waits for sixty seconds and does nothing else. The `^C` is the terminal showing that you pressed Ctrl-C. The code `130` says the program did not fail on its own; you stopped it. That is a normal thing to do and nothing on the system is wrong.

History is the second tool. `history` lists what you have typed, numbered, oldest first.

```
{user}@{host}:~$ history | tail -n 4
   41  ls /nope
   42  echo $?
   43  true; echo $?
   44  sleep 60
```

The `|` (pipe) sends the output of `history` into `tail`, and `tail -n 4` (`-n` for number of lines) keeps only the last four. Each line is a number and the command you typed. The up arrow walks back through this list one line at a time, and Ctrl-R searches it: press Ctrl-R, type a few letters of an earlier command, and the shell shows the most recent match. Press Enter to run it or Esc to edit it first.

Two shortcuts pay off constantly. `!!` is replaced by the whole previous command line, which is why `sudo !!` is the classic move after a "Permission denied" message. `!$` is replaced by the last word of the previous line.

```
{user}@{host}:~$ ls /etc/ssh
ssh_config  ssh_config.d  sshd_config  sshd_config.d
{user}@{host}:~$ cd !$
cd /etc/ssh
{user}@{host}:/etc/ssh$
```

The shell echoed `cd /etc/ssh` to show what `!$` became, then ran it. Your prompt now shows the new working directory.

## When it goes wrong

`bash: lss: command not found` and `$?` is `127`. The shell searched every directory on your PATH and found no program named `lss`. Check the spelling. If the name is right, the program is not installed on the host; on Pridwen, software arrives as a Flatpak, inside a Distrobox, or through the image, and `pridwen why` will walk you through those choices.

`bash: ./script.sh: Permission denied` and `$?` is `126`. The file exists but is not marked as runnable. The Permissions node covers the execute bit; the quick fix for a script you wrote is `chmod +x script.sh`.

`$?` shows `0` right after a command that plainly failed. You probably ran something in between, even a harmless `ls`, and it overwrote the value. Run the failing command again and read `$?` on the very next line.

## Try it

1. Type `ls /nope` and press Enter. Read the error message, then type `echo $?` and confirm it prints `2`.
2. Type `true; echo $?` and confirm it prints `0`. Then try `false; echo $?`, which should print `1`.
3. Type `sleep 30`, wait a second, press Ctrl-C, then `echo $?`. Expect `130`, and work out the signal number by subtracting 128.
4. Type `nosuchcommand` and then `echo $?`. Expect `127`.
5. Press the up arrow three times and watch earlier commands reappear. Press Enter on one of them.
6. Press Ctrl-R, type `sle`, and see `sleep 30` appear. Press Esc to keep it on the line without running it, then clear the line with Ctrl-C.
7. Type `ls /etc/ssh`, then `cd !$`. The shell should print `cd /etc/ssh` and your prompt should change. Type `cd` to go home.

## Remember

- Every command returns an exit code; 0 is success, and `echo $?` on the very next line reads it.
- 127 is "command not found", 126 is "found but not runnable", 130 is "you pressed Ctrl-C".
- The up arrow, Ctrl-R, `!!` and `!$` recall what you already typed so you never retype a long line.
