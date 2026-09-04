# The prompt and where you are

The shell is a program that reads what you type and runs it. The prompt is its
way of saying it is ready, and it usually tells you who you are and where you
are standing in the filesystem. Everything you do starts from a current
directory, and most commands act on that directory unless you name another path.

Two commands answer "where am I" and "what is here". `pwd` prints the working
directory as an absolute path from the root of the tree. `ls` lists what that
directory holds. Paths that start with `/` are absolute; anything else is read
relative to where you are now, and `~` is shorthand for your home directory.

```
$ pwd
/home/nate
$ ls
Desktop  Documents  Downloads  Pictures
$ cd Documents
$ pwd
/home/nate/Documents
```

Tab completion is the habit that saves the most typing and the most typos: start
a name, press Tab, and the shell finishes it or shows the choices. On Pridwen the
prompt and colours come from the Cream Glass shell theme, but the mechanics are
the same as any Fedora terminal.

## Try it

1. Run `pwd` and read the absolute path back to yourself.
2. Run `ls` and then `ls -a` to see the dot files the first one hid.
3. `cd` into a subdirectory, run `pwd` again, then `cd` with no argument to jump home.
4. Type the first few letters of a directory name and press Tab to complete it.
