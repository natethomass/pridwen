# Counting and ranking

The fastest way to find the odd thing in a large log is to count. A log with
ten thousand lines cannot be read, but a tally of which address, which user, or
which program appears how many times can be read in seconds. Turning a stream of
lines into a ranked list surfaces both the loud thing and the rare thing, and the
story is often in what appears once, not in what appears most.

This is the single most reused habit in log work, on Pridwen and on a job. The
same three-command pipeline answers "who is hammering the SSH port", "which
program ran most today", and "which error is new". You practise it here on your
own host's journal and, when the Range arrives in milestone M4, on Rocky 9 lab
hosts you own that carry the kind of failed-login traffic a desktop never sees.

## Words you'll meet

- **pipeline**: commands joined with `|` so the output of one becomes the input of the next.
- **tally**: a count of how many times each distinct line appears.
- **field**: the part of a line you choose to count, such as an address or a username.
- **stdin and stdout**: a command's input stream and output stream; a pipe connects one to the other.
- **audit log**: the kernel's own record of security-relevant actions, kept by `auditd` under `/var/log/audit/`.
- **aureport**: the tool that summarises the audit log by executable, user, event and more.

## How it works

The workhorse is `sort | uniq -c | sort -rn`. `sort` puts identical lines next to
each other, which `uniq` needs because it only compares neighbouring lines.
`uniq -c` (count) collapses each run of identical lines into one and prefixes it
with how many there were. The second `sort -rn` (reverse, numeric) orders those
counts largest first. Try it on something you can see all of before trusting it
on something you cannot.

```
{user}@{host}:~$ journalctl --since today -o cat _TRANSPORT=syslog | awk '{print $1}' | sort | uniq -c | sort -rn | head -n 5
    412 sudo[4121]:
     88 gnome-shell[2310]:
     14 systemd[1]:
      3 pridwend[2601]:
      1 usbguard-daemon[812]:
```

`-o cat` prints only the message text without timestamp or hostname, and `awk
'{print $1}'` keeps the first word of each line, which here is the program name
and pid. `head -n 5` shows the top five. The first column is the count, the
second is the thing counted. Reading it back: `sudo` wrote 412 lines today,
which is normal for someone working through missions, and `usbguard-daemon`
wrote exactly one, which is the line to open, because a program that speaks once
usually had a reason.

Applied to failed logins on a Range host, the same shape ranks source addresses.
`grep -oE 'from [0-9.]+'` keeps only the matching part of each line (`-o`) using
an extended regex (`-E`), so the address alone is counted rather than the whole
message with its changing port numbers.

```
{user}@{host}:~$ journalctl _COMM=sshd -g Failed --since today | grep -oE 'from [0-9.]+' | sort | uniq -c | sort -rn | head
     58 from 203.0.113.9
      2 from 198.51.100.7
```

The top line is the noisy scanner. The bottom line, two failures from a
different address, is the one to chase, because a careful intruder fails twice
and then succeeds, while a scanner fails fifty-eight times and moves on. On your
own Pridwen host this pipeline prints nothing, because `sshd` is off; that empty
result is correct.

On the audit side, `aureport -x --summary` ranks executables (`-x`) by how often
the audit log saw them run, as a summary rather than one line per event. The
audit log is root-only, so `sudo` is required.

```
{user}@{host}:~$ sudo aureport -x --summary
Executable Summary Report
=================================
total  file
=================================
1330  /usr/bin/sudo
201  /usr/lib/systemd/systemd
6  /usr/bin/passwd
1  /usr/bin/nc
```

Same shape: count, then the thing. `/usr/bin/nc`, a network tool, ran once and
`passwd` ran six times. On a desktop where you did neither, both deserve a look.
The skill is choosing what to count: addresses, users, commands, or return
codes. Counting the wrong field hides the story; counting the right one makes it
obvious.

## When it goes wrong

`sort: write failed: standard output: Broken pipe`. You piped into `head`, and
`head` closed its input after enough lines while `sort` was still writing. The
counts you saw are correct; the message is noise, and it is safe to ignore.

`Error opening /var/log/audit/audit.log (Permission denied)`. `aureport` was run
without `sudo`. The audit log is readable only by root, by design, so that a
compromised user account cannot read what the kernel recorded about it. Run
`sudo aureport -x --summary`.

`grep: invalid option -- 'o'` or an empty result after `grep -oE`. Usually the
regex is wrong for the lines you have. Run the `journalctl` half alone, look at
one real line, and adjust the pattern to match what is actually printed.
`pridwen explain grep` names each flag.

## Try it

1. On your own host, run `journalctl --since today -o cat _TRANSPORT=syslog | awk '{print $1}' | sort | uniq -c | sort -rn | head -n 5`. Say which program wrote most and which wrote least.
2. Remove `| sort -rn | head -n 5` and run it again. Notice the counts are there but unordered; that is what the second sort adds.
3. Run `sudo aureport -x --summary` and read the top three executables. Decide whether each is expected on a desktop.
4. On a Range host, rank source addresses in failed SSH logins with the `grep -oE 'from [0-9.]+'` pipeline.
5. Take the least frequent address and run `journalctl _COMM=sshd -g '<that address>' --since today` to see everything it did, including any `Accepted`.
6. Write one sentence on why the rarest line was the important one.

## Remember

- `sort | uniq -c | sort -rn` turns any stream of lines into a ranked tally.
- Count one field at a time, and pick the field that would change if something were wrong.
- The rarest line is often the story; the most common one is often the noise.
