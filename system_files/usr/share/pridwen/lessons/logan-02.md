# Counting and ranking

The fastest way to find the odd thing in a large log is to count. Turning a
stream of lines into a ranked tally surfaces both the loud and the rare, and the
story is often in what appears just once, not what appears most.

The workhorse pipeline is `sort | uniq -c | sort -rn`: sort so identical lines
sit together, `uniq -c` counts each group, and sort again numerically to rank
them. Applied to source addresses in failed logins, the top of the list is the
noisy scanner and the bottom may be the one login that succeeded.

```
$ journalctl _COMM=sshd -g Failed --since today \
    | grep -oE 'from [0-9.]+' | sort | uniq -c | sort -rn | head
     58 from 203.0.113.9
      2 from 198.51.100.7
```

On the audit side, `sudo aureport -x --summary` ranks executables by how often
they ran, and an unfamiliar program near the top is worth a second look. The
skill is choosing what to count: addresses, users, commands, or return codes.
Counting the wrong field hides the story; counting the right one makes it
obvious. Practise on Range logs where you already know the answer, then trust the
method on ones you do not.

## Try it

1. Build a `sort | uniq -c | sort -rn` pipeline over a log field of your choice.
2. Rank source addresses in failed SSH logins on a Range host.
3. Run `sudo aureport -x --summary` and read the top executables.
4. Explain why the least frequent line is sometimes the important one.
