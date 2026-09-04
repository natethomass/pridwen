# The journal

systemd collects logs into a single indexed store, the journal, and
`journalctl` reads it. It replaces the scatter of text files under `/var/log`;
on Pridwen those classic files mostly do not exist because no syslog daemon is
installed to write them.

Run bare, `journalctl` shows everything oldest first. The useful views narrow it.
`journalctl -r -n 50` is the most recent fifty. `-f` follows new lines as they
arrive, like `tail -f` for the whole system. `-b` limits to this boot, and
`-b -1` to the previous one.

```
$ journalctl -b -p err
$ journalctl -f -u NetworkManager
$ journalctl --since "10 min ago"
```

Members of the `wheel` or `systemd-journal` groups can read the full journal;
otherwise you see only your own user's messages. The journal is binary and
indexed, which is what makes filtering by field fast, and it rotates on size
automatically so it does not fill the disk. `journalctl --disk-usage` shows how
much it is keeping. Everything the rest of this node teaches is a way of asking
this one store a sharper question.

## Try it

1. Run `journalctl -b -p err` and read any errors from this boot.
2. Run `journalctl -f`, watch a few lines, and stop with Ctrl-C.
3. Run `journalctl --since "1 hour ago" | tail` and read recent activity.
4. Run `journalctl --disk-usage` and note how much space the journal uses.
