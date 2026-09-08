# Variables and quoting

Before the shell runs your line, it rewrites it. This step is called expansion, and it happens every time, silently, before any program sees a single word. The shell replaces variables with their values, runs any commands you asked it to substitute, splits the result into separate words wherever it finds spaces, and turns patterns like `*.txt` into the list of matching filenames. Only then does it hand the words to the command. Once you know that order, almost every strange thing a shell does with spaces and special characters has a plain explanation.

This matters because paths on a real system contain spaces, dollar signs and stars more often than you would like, and a command that misreads one can delete or overwrite the wrong file. It matters on Pridwen because the Coach, scripts, and every configuration you will ever automate depend on getting quoting right. The rule you will learn here, double-quote every variable, is one that working admins repeat to each other for years.

## Words you'll meet

- **expansion**: the rewriting the shell does to your line before running it.
- **variable**: a named slot the shell keeps text in; `name=value` sets it and `$name` reads it.
- **word splitting**: the shell breaking expanded text into separate arguments at every space.
- **glob**: a filename pattern like `*.txt`, where `*` means "any characters".
- **double quotes**: `"..."`; the shell still expands `$name` and `$(cmd)` inside but keeps the result as one word.
- **single quotes**: `'...'`; nothing inside is changed at all.
- **command substitution**: `$(cmd)`, replaced by the output of `cmd`.
- **environment variable**: a variable that is also passed to programs you start, such as `HOME` and `PATH`.

## How it works

Set a variable with no spaces on either side of the equals sign, then read it with a dollar sign. `echo` prints its arguments separated by single spaces.

```
{user}@{host}:~$ greeting="hello   world"
{user}@{host}:~$ echo $greeting
hello world
{user}@{host}:~$ echo "$greeting"
hello   world
```

Look closely at the spaces. The value had three spaces between the words. Unquoted, `$greeting` was expanded and then split into two words, `hello` and `world`, and `echo` printed them with a single space. Inside double quotes the expansion still happened but the text stayed as one word, spaces and all. That difference is the whole lesson.

`printf` makes the splitting visible. `printf '[%s]\n' ...` prints each argument inside square brackets on its own line, so you can count how many arguments a command really received.

```
{user}@{host}:~$ printf '[%s]\n' $greeting
[hello]
[world]
{user}@{host}:~$ printf '[%s]\n' "$greeting"
[hello   world]
```

Unquoted: two arguments. Quoted: one. A command like `rm $file` where `file` holds `my notes.txt` would receive two arguments, `my` and `notes.txt`, and try to remove two files that do not exist. `rm "$file"` removes the one you meant.

Single quotes stop expansion completely. Whatever is inside is passed through as literal characters.

```
{user}@{host}:~$ echo '$greeting'
$greeting
{user}@{host}:~$ echo "$HOME"
{home}
{user}@{host}:~$ echo '$HOME'
$HOME
```

`HOME` is an environment variable the system sets to your home directory when you log in. In double quotes it expanded to `{home}`; in single quotes the shell printed the six characters `$HOME` unchanged. Single quotes are for text you want passed through untouched, such as a search pattern for `grep` or a literal dollar sign.

Command substitution puts a command's output into your line. `$(date +%F)` runs `date` with the format `+%F` (the year-month-day form) and is replaced by what it printed.

```
{user}@{host}:~$ today="$(date +%F)"
{user}@{host}:~$ echo "Backup for $today"
Backup for 2026-09-07
```

Globs are the last expansion. `*` matches any run of characters in a filename, so the shell replaces `*.txt` with every matching name in the working directory before the command runs. `echo *` is a quick way to see what a pattern will become.

```
{user}@{host}:~$ echo ~/Documents/*
{home}/Documents/report.txt {home}/Documents/todo.txt
```

Note that `~` expanded to `{home}` as well. Tilde expansion only happens when the tilde is unquoted and at the start of a word, which is a common trap: `"~/Documents"` in quotes stays a literal tilde and points at a directory that does not exist.

## When it goes wrong

`bash: name: command not found` after typing `name = value`. With spaces around `=`, the shell read `name` as a command and `=` and `value` as its arguments. Assignments must be one word: `name=value`.

`bash: $name=value: command not found`. The dollar sign reads a variable; it does not set one. Write `name=value` to set and `$name` to read. `pridwen why` shows both forms after this mistake.

`rm: cannot remove 'my': No such file or directory` followed by a second line for `notes.txt`. A variable or filename with a space was left unquoted and split in two. Put double quotes around it: `rm "my notes.txt"` or `rm "$file"`.

`ls: cannot access '~/Documents': No such file or directory`. The tilde was inside quotes, so it stayed a tilde. Write `~/Documents` unquoted or `"$HOME/Documents"`.

## Try it

1. Type `greeting="hello   world"` with three spaces between the words. Then `echo $greeting` and `echo "$greeting"`, and compare how many spaces survive.
2. Type `printf '[%s]\n' $greeting` and then the same with `"$greeting"`. Count the bracketed lines: two, then one.
3. Type `echo "$HOME"` and `echo '$HOME'`. Explain to yourself why the second one printed a dollar sign.
4. Type `touch "my notes.txt"` to create a file with a space in its name, then `ls` to see it. Now `rm "my notes.txt"` and `ls` again to confirm it is gone.
5. Type `today="$(date +%F)"` and `echo "$today"`. You should see today's date.
6. Type `echo ~/Documents/*` and watch the shell expand the pattern before `echo` ever ran.
7. Type `name = value` on purpose, read the error, then fix it as `name=value` and print it with `echo "$name"`.

## Remember

- The shell expands variables, substitutions, spaces and globs before the command runs, in that order.
- Double quotes expand `$name` but keep the result as one word; single quotes change nothing at all.
- Double-quote every variable that could hold a space, which on a real system is most of them.
