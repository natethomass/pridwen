# Listing and moving around

The filesystem is a single tree that starts at `/`. You move through it with
`cd` and look at it with `ls`. A long listing, `ls -l`, is the view worth
learning first because it packs a lot into one line per file.

Read a long listing left to right: the type and permission bits, the link
count, the owner, the group, the size in bytes, the modification time, and the
name. The very first character is the type, where `-` is a regular file and `d`
is a directory.

```
$ ls -l
drwxr-xr-x. 2 nate nate 4096 Sep  4 09:12 Documents
-rw-r--r--. 1 nate nate  220 Sep  1 08:00 notes.txt
```

Useful flags stack: `-a` shows dot files, `-h` prints sizes as K and M, `-t`
sorts by time, and `-R` recurses. `ls -lah` is a common combination. Making
directories is `mkdir`, and `mkdir -p a/b/c` creates a whole chain at once,
treating "already exists" as success rather than an error.

## Try it

1. Run `ls -l` in your home directory and name each column out loud.
2. Add `-a` and find at least one dot file the plain listing hid.
3. Run `mkdir -p practice/one/two` and confirm the chain with `ls -R practice`.
4. Run `ls -lt` and notice the newest file is now at the top.
