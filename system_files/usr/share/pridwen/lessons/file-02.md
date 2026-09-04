# Copy, move, and remove

Three commands do most of the work of shaping a directory: `cp` copies, `mv`
moves or renames, and `rm` removes. They are fast and quiet, which is exactly
why a moment of care pays off, because there is no recycle bin on the command
line.

`cp source dest` copies a file; a directory needs `cp -r`, and `cp -a` also
keeps permissions and timestamps. `mv` both moves and renames, since renaming is
just moving within the same directory. `rm` deletes; a directory needs `rm -r`,
and while you are learning, `rm -i` asks before each file.

```
$ cp notes.txt notes.bak
$ mv notes.bak archive/
$ rm -i archive/notes.bak
rm: remove regular file 'archive/notes.bak'? y
```

The classic mistake is a stray space, as in `rm -rf / home` instead of
`rm -rf /home`, which targets two things. Preview a pattern with `ls` before you
hand it to `rm`: if `ls *.log` shows what you expect, then `rm *.log` will too.
On Pridwen the image under `/usr` is read-only, so it survives a slip, but
`/home` and `/etc` do not.

## Try it

1. Copy a file to a new name, then `ls -l` both and compare their times.
2. Rename the copy with `mv`, then move it into a new subdirectory.
3. Preview `ls *.bak`, then remove those files with `rm -i`.
4. Copy a directory with `cp -r` and confirm the contents came along.
