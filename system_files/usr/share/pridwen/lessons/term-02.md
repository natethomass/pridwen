# Exit codes and history

Every command hands back a number when it finishes: zero means success, anything
else means a failure of some kind. The shell keeps the last one in `$?`, and
reading it is how scripts and the Coach both decide whether something worked.

A few values recur. 1 is a general failure. 2 is often a usage or syntax
problem. 126 means a file was found but could not be run. 127 means the command
was not found at all. Values above 128 mean a signal stopped the process, so 130
is Ctrl-C (128 plus signal 2, SIGINT).

```
$ ls /nope
ls: cannot access '/nope': No such file or directory
$ echo $?
2
$ true; echo $?
0
```

History is the shell's memory of what you typed. `history` lists it, the up
arrow walks back through it, and Ctrl-R searches it as you type. Two shortcuts
pay off constantly: `!!` repeats the whole last command, useful after a
permission error as `sudo !!`, and `!$` reuses the last argument of the previous
line.

## Try it

1. Run a command you know will fail, then `echo $?` and name the code.
2. Run a command that succeeds and confirm `$?` is 0.
3. Press Ctrl-R and type part of an earlier command to search history.
4. Run `ls /etc`, then `cd !$` to reuse the path as the next argument.
