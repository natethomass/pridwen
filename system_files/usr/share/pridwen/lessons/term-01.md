# The prompt and where you are

When you open the Terminal app (on Pridwen it is called Ptyxis, and it sits in the dock), you are looking at a shell. A shell is a program that waits for you to type a line, reads it, runs the command you asked for, shows you what came back, and waits again. The shell on Pridwen is bash. The short piece of text it prints while it waits, `{user}@{host}:~$`, is the prompt. The prompt is the shell's way of saying "ready", and it also tells you three things: who you are (`{user}`), which computer you are on (`{host}`), and where you are standing in the filesystem (`~`).

That last part matters more than it looks. Everything on a Linux system lives in one big tree of directories (a directory is what a desktop calls a folder), and at any moment your shell is standing in exactly one of them. That place is called the working directory. Most commands act on the working directory unless you name another path, so knowing where you are is the first skill of the terminal. On a real job, half the mistakes a new admin makes are commands run in the wrong directory.

## Words you'll meet

- **shell**: the program that reads your typed line and runs it; on Pridwen it is bash.
- **prompt**: the text the shell prints when it is ready, `{user}@{host}:~$` here.
- **directory**: a container for files and other directories; a folder.
- **working directory**: the directory your shell is currently standing in.
- **path**: the written address of a file or directory, like `/etc/os-release`.
- **absolute path**: a path that starts with `/`, the root of the tree, so it means the same thing from anywhere.
- **relative path**: a path that does not start with `/`; it is read from the working directory.
- **home directory**: your own directory, `{home}`; the shell writes it as `~`.
- **argument**: a word you type after a command to tell it what to act on.
- **Tab completion**: pressing the Tab key to have the shell finish a name for you.

## How it works

Two commands answer "where am I" and "what is here". `pwd` stands for print working directory and prints your location as an absolute path.

```
{user}@{host}:~$ pwd
{home}
```

That one line is the whole answer: you are in your home directory, which the prompt was already showing as `~`. The tilde is only shorthand; `{home}` is the real address.

`ls` stands for list and shows what the working directory holds. With no arguments it lists the place you are standing.

```
{user}@{host}:~$ ls
Desktop  Documents  Downloads  Music  Pictures  Public  Templates  Videos
```

Each word is a directory or a file inside your home. Plain `ls` hides names that start with a dot, which are configuration files that programs keep for themselves. The `-a` flag (all) shows them too. A flag is a word starting with `-` that changes how a command behaves.

```
{user}@{host}:~$ ls -a
.  ..  .bash_history  .bashrc  .config  .local  Desktop  Documents  Downloads
```

Two entries are always there: `.` means "this directory" and `..` means "the directory above this one". You will use `..` constantly to move up.

`cd` stands for change directory and moves your shell somewhere else. Give it a path as its argument.

```
{user}@{host}:~$ cd Documents
{user}@{host}:~/Documents$ pwd
{home}/Documents
```

Notice the prompt changed from `~` to `~/Documents`. `Documents` was a relative path: the shell looked for it inside the working directory. `{home}/Documents` in the output of `pwd` is the same place written as an absolute path.

`cd ..` goes up one level, and `cd` with no argument always takes you home, wherever you are.

```
{user}@{host}:~/Documents$ cd ..
{user}@{host}:~$ cd /etc
{user}@{host}:/etc$ cd
{user}@{host}:~$
```

`/etc` is the directory that holds the system's configuration files. It is a good place to look around, because you can read most of it but not change it without extra rights, which a later lesson explains.

Tab completion is the habit that saves the most typing and the most typos. Type `cd Doc` and press Tab; the shell finishes it to `cd Documents/`. If more than one name matches, press Tab twice and the shell lists the choices. Use it for every path you type.

## When it goes wrong

`bash: cd: Dcouments: No such file or directory`. The shell looked for a name in the working directory and found nothing with that spelling. Run `ls` to see what is really here, then retype the name, using Tab to complete it. `pridwen why` explains the last failure in full if the hint under the command was not enough.

`bash: cd: notes.txt: Not a directory`. The name exists but it is a file, and `cd` only enters directories. Read it with `less notes.txt` (press `q` to leave) instead.

`bash: lss: command not found`. The shell could not find a program with that name. Usually the command is misspelled. If you are sure of the name, `pridwen explain <command>` tells you whether it exists on Pridwen and what its flags mean.

## Try it

1. Open Ptyxis from the dock. Read the prompt aloud: the part before `@` is your login name, the part after it is the hostname, and `~` is your home directory.
2. Type `pwd` and press Enter. You should see `{home}`.
3. Type `ls`, then `ls -a`. Count how many extra names the second listing shows; every one of them starts with a dot.
4. Type `cd Documents` and check that the prompt now ends with `~/Documents$`. Run `pwd` to see the absolute path.
5. Type `cd ..` and confirm with `pwd` that you are back in `{home}`.
6. Type `cd /etc`, then `ls`, then `cd` on its own. The prompt should be back to `~`.
7. Type `cd Dow` and press Tab. The shell should complete it to `Downloads/`.

## Remember

- The prompt `{user}@{host}:~$` tells you who you are, which machine you are on, and where you stand.
- `pwd` prints where you are, `ls` shows what is here, `cd` moves you; `cd` alone goes home and `cd ..` goes up.
- A path starting with `/` is absolute and means the same thing from anywhere; any other path is read from the working directory.
