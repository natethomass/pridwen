# Reading and finding

Once files exist you need to read them and locate them. For reading, `cat`
dumps a whole file, `less` pages through a big one, and `head` and `tail` show
the first or last lines. `tail -f` follows a file as it grows, which is handy
for logs.

Finding splits into two questions. `find` walks the tree by name, size, time, or
type, evaluating each file as it goes. `grep` searches inside files for text,
and `grep -rn pattern dir` recurses through a directory printing line numbers.

```
$ head -n 3 /etc/os-release
NAME="Pridwen OS"
VERSION="0.2.0-m1"
ID=fedora
$ grep -rn "PRETTY" /etc/os-release
2:PRETTY_NAME="Pridwen OS 0.2.0-m1"
```

Two habits keep these tools calm. Quote any pattern that contains a `*` so the
shell does not expand it before `find` sees it, as in `find . -name '*.conf'`.
And when `find` or `grep` prints "Permission denied" for directories you do not
own, add `2>/dev/null` to hide those lines; the results you can read are still
complete.

## Try it

1. Read `/etc/os-release` with `cat`, then again with `less` and quit with `q`.
2. Show just the last two lines with `tail -n 2 /etc/os-release`.
3. Run `grep -rn fedora /etc/os-release` and read the line numbers.
4. Run `find /etc -name '*.conf' 2>/dev/null | head` and note the quoting.
