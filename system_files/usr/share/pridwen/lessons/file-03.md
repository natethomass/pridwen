# Reading and finding

Once files exist you need to read what is in them and locate the ones you cannot remember the path to. Reading is the everyday work of an admin: a configuration file to check, a log to watch while something starts, a script someone else left behind. Finding is the other half, because a real system holds hundreds of thousands of files and you will not know where most of them are. Linux answers each with small tools that do one thing: `cat`, `less`, `head` and `tail` read, `find` locates by name or property, and `grep` searches for text inside files.

These tools matter on Pridwen straight away. `/etc/os-release` tells you which build of Pridwen you are running, the journal and `/var/log` hold what the system did, and `grep` across `/etc` is how you learn where a setting lives. On a job, `tail -f` on a log while you restart a service, and `grep -rn` across a configuration tree, are two of the moves you will make most often.

## Words you'll meet

- **page**: one screenful of text; a pager like `less` shows a file one page at a time.
- **stdout** and **stderr**: a program's two output streams; normal results go to stdout, complaints to stderr.
- **redirect**: sending a stream somewhere else with `>`; `2>/dev/null` throws stderr away.
- **`/dev/null`**: a special file that discards everything written to it.
- **pattern**: the text or wildcard you are searching for.
- **regular expression**: a pattern language `grep` understands, where `.` means any character and `^` means start of line.
- **recursive**: going into every subdirectory; `-r` on `grep`, automatic for `find`.
- **quoting**: wrapping a pattern in single quotes so the shell hands it to the command unchanged.

## How it works

`cat` prints a whole file to the terminal. It is right for short files like `/etc/os-release`, which describes the system in `KEY=value` lines.

```
{user}@{host}:~$ cat /etc/os-release
NAME="Pridwen OS"
ID=fedora
VERSION_ID=43
PRETTY_NAME="Pridwen OS 0.3.1-m3"
```

The real file has more lines; these are the ones worth reading. `NAME` and `PRETTY_NAME` are branded Pridwen, while `ID=fedora` stays, because tools decide how to behave by reading `ID` and Pridwen is a Fedora underneath. `PRETTY_NAME` is the build you are running and changes with every `bootc upgrade`.

For a long file, `less` shows one page at a time. The space bar moves down a page, the arrow keys move a line, `/word` searches forward, and `q` quits. `head` and `tail` show the two ends of a file. Write a small file first so every result below is predictable. `printf` prints the text you give it, `\n` inside it means "new line", and the `>` sends the output into the file instead of the screen, replacing whatever was there.

```
{user}@{host}:~$ printf 'shield\nchevron\nSHIELD wall\n' > pridwen/notes.txt
{user}@{host}:~$ head -n 2 pridwen/notes.txt
shield
chevron
{user}@{host}:~$ tail -n 1 pridwen/notes.txt
SHIELD wall
```

`head -n 2` (`-n` for number of lines) printed only the first two lines and `tail -n 1` only the last. `tail -f` (follow) keeps a file open and prints new lines as they arrive, which is how you watch a log grow; press Ctrl-C to stop.

`grep pattern file` prints every line of the file that contains the pattern. `-n` adds the line number, `-i` ignores upper and lower case, and `-r` recurses through a directory, searching every file below it and printing the file name in front of each match.

```
{user}@{host}:~$ grep -n shield pridwen/notes.txt
1:shield
{user}@{host}:~$ grep -in shield pridwen/notes.txt
1:shield
3:SHIELD wall
{user}@{host}:~$ grep -rn chevron pridwen
pridwen/notes.txt:2:chevron
```

In the `grep` output, the number before the colon is the line number; with `-r` the file path comes first. A `grep` that prints nothing found nothing, and its exit code is 1, which is not an error, just "no match".

`find` walks a directory tree and prints every path that matches your tests. `-name` tests the file name, `-type d` keeps only directories and `-type f` only regular files, and `-mtime -1` keeps files changed in the last day.

```
{user}@{host}:~$ find pridwen -name '*.txt'
pridwen/notes.txt
{user}@{host}:~$ find /etc -name '*.conf' 2>/dev/null | head -n 3
/etc/host.conf
/etc/ld.so.conf
/etc/sysctl.conf
```

Two habits keep these tools calm. Quote any pattern that contains `*`, as in `'*.conf'`, so the shell does not expand it against the current directory before `find` sees it. And when searching directories you do not own, add `2>/dev/null`: the `2` is stderr, and sending it to `/dev/null` hides each "Permission denied" line while the results you can read still arrive on stdout, complete.

## When it goes wrong

`cat: pridwen: Is a directory`. `cat` reads files, and you gave it a directory. `ls -l pridwen` lists it instead; `cat pridwen/notes.txt` reads a file inside it.

`grep: pridwen: Is a directory` with exit code 2. `grep` needs `-r` to walk a directory. `grep -rn chevron pridwen` searches every file below it. `pridwen explain grep` names the rest of the flags.

`find: '/root': Permission denied` mixed into otherwise good results. `find` reports each directory it may not enter and carries on; the results are fine, but the exit code is 1 to admit it missed some. Add `2>/dev/null` to hide the complaints, or start from a narrower directory.

`find: paths must precede expression: 'notes.txt'`. An unquoted `*` was expanded by the shell into several file names before `find` ran. Quote the pattern: `find . -name '*.txt'`.

## Try it

1. Type `cat /etc/os-release` and find the `PRETTY_NAME` line; that is the Pridwen build you are on.
2. Type `less /etc/os-release`, press the space bar, then type `/ID` and Enter to search, then `q` to quit.
3. Type `printf 'shield\nchevron\nSHIELD wall\n' > ~/pridwen/notes.txt`, then `head -n 2 ~/pridwen/notes.txt` and `tail -n 1 ~/pridwen/notes.txt`. Expect two lines, then one.
4. Type `grep -n shield ~/pridwen/notes.txt` and `grep -in shield ~/pridwen/notes.txt`. Compare the line counts: one match, then two.
5. Type `grep -rn chevron ~/pridwen` and read the three parts of the result: path, line number, matching line.
6. Type `find ~/pridwen -name '*.txt'` and confirm it finds your notes file.
7. Type `find /etc -name '*.conf' | head -n 5`, note any `Permission denied` lines, then run it again with `2>/dev/null` before the `|`.

## Remember

- `cat` for short files, `less` for long ones (`q` to quit), `head` and `tail` for the ends, `tail -f` to watch a log.
- `grep -rn pattern dir` searches inside files; `find dir -name 'pattern'` searches by name, with the pattern in single quotes.
- `2>/dev/null` hides "Permission denied" from stderr without losing any result you were allowed to see.
