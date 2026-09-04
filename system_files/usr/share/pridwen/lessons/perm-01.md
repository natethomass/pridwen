# Reading the mode

Every file carries a mode that answers a simple question three times: may this
user read, write, and execute it. The three groups are the owner, the group,
and everyone else. `ls -l` shows the mode as ten characters, and `stat` shows it
as a number.

The first character is the type. The next nine are three sets of `rwx`: owner,
group, other. A letter means the bit is on, a dash means off. So `-rwxr-x---`
is a file the owner may read, write and run, the group may read and run, and
others may do nothing.

```
$ ls -l script.sh
-rwxr-x---. 1 nate devs 812 Sep  4 09:20 script.sh
$ stat -c '%A %a %U:%G' script.sh
-rwxr-x--- 750 nate:devs
```

The numeric form adds the bits: read is 4, write is 2, execute is 1. So `rwx` is
7, `r-x` is 5, and `r--` is 4, which makes `750` the same mode as above. On a
directory the execute bit means "may enter", and read means "may list", which is
why a directory you cannot execute refuses `cd` even when you can see its name.

## Try it

1. Run `ls -l` on a file and read its owner, group and other bits aloud.
2. Run `stat -c '%A %a' file` and match the letters to the number.
3. Create a file and work out its mode before checking with `ls -l`.
4. Look at a directory with `ls -ld` and explain what its execute bit allows.
