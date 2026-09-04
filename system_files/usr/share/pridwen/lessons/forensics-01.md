# Timestamps and hashes

Forensics is saying what happened after the fact, with evidence that holds up.
Two primitives underlie it: the timestamps a filesystem keeps, and the hashes
that prove a file has not changed. Both are things you read, not things you alter.

Every file carries three times: modification (mtime, when the contents changed),
change (ctime, when the metadata changed), and access (atime). `stat` shows all
three. A file whose mtime sits inside your incident window is worth a closer
look, and one whose ctime and mtime disagree may have had its metadata touched.

```
$ stat -c 'mtime=%y ctime=%z name=%n' /etc/passwd
$ sha256sum /etc/passwd > evidence.sha256
$ sha256sum -c evidence.sha256
/etc/passwd: OK
```

A hash is a fingerprint: `sha256sum` reduces a file to a short value that changes
if a single byte does. Recording hashes of evidence lets you prove later that the
copy you analysed is the copy you took. On a Range host you practise building a
list of files changed in a window and hashing them, which is the raw material of
a forensic account and the reason these two humble commands matter so much.

## Try it

1. Run `stat` on a file and read its three timestamps.
2. Hash a file with `sha256sum`, then verify it with `-c`.
3. On a Range host, find files under `/etc` modified today with `find -mtime`.
4. Explain what a mismatch between ctime and mtime might indicate.
