A compliance auditor is supposed to start work on this machine today, and
whoever provisioned the account got almost everything about it wrong. This
scenario runs inside `rhcsa-01-users`, a disposable Rocky Linux 9 container
that belongs entirely to you: nothing you do here can touch `{host}`, your
real machine, and nothing you type goes through `sudo`, because
`pridwen range enter rhcsa-01-users` already drops you in as root. That is
the whole point of the range: the failure mode here is "reset the container,"
never "reinstall the OS."

A user account is not one fact, it is several, and the system tracks each of
them separately. Its **UID** (user ID) is the number the kernel actually
checks for file ownership; the login name is a label a human reads, the UID
is what everything else compares against. Its **primary group** is the group
new files get by default, and its **supplementary groups** are every other
group it also belongs to — `wheel`, the group that grants sudo on Rocky, is
almost always a supplementary one, added on top of whatever primary group an
account already has, not swapped in for it. Its **login shell** is the
program that runs the moment it logs in; `/sbin/nologin` exists specifically
to make an account unable to get an interactive session at all, which is
correct for a service account and wrong for a person who needs to work. And
its **home directory's ownership** is a plain filesystem fact, independent of
all of the above — a directory can belong to the wrong user even when the
account itself is otherwise fine.

Two more facts sit on top of those four, and they are easy to confuse with
each other. A **locked** account (`passwd -l`) has its password hash
prefixed with a marker that makes every login attempt fail, correct
password or not; `passwd -u` removes the marker without touching the hash
underneath, which is why it is the fix and not "set a new password." An
**expiration date** (`chage -E`), by contrast, is not about the password at
all — it is a date after which the account itself stops being usable no
matter what the password is, the tool a company uses for a contractor whose
engagement has an end date already known. `chage -l` prints it as an
absolute date, or the word `never`.

`id`, `getent passwd`, `passwd -S` and `chage -l` are how you read all six
facts back, and in that order they are close to the first four commands
anyone runs when a login stops working on a real system: what does the
system think this account is, does it have the login it needs, is the
password itself usable, and has it quietly expired. Done looks like all six
matching what compliance asked for, checkable the same way: `pridwen range
check rhcsa-01-users` reads them back exactly as you would by hand.
