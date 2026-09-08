# Quoting and safety

Most script bugs are not mistakes in logic. They come from the shell doing exactly what it was told with a value the writer did not picture: a file name with a space in it, a variable that turned out to be empty, a comparison written without the spaces the shell needs. A script that works on your test file and deletes the wrong thing on a real one is the classic result.

A few habits stop nearly all of this. Quote your variables, write tests with the right spacing, and turn on the shell's own safety switches with one line at the top. You already know from the previous lesson that a script is a file of commands with a shebang; this lesson is about making those commands survive real data and other people.

## Words you'll meet

- **variable**: a named value; `name="world"` sets one and `$name` reads it.
- **word splitting**: the shell breaking an unquoted value into separate arguments wherever it sees a space.
- **argument**: one item handed to a command; `ls -l notes.txt` has two.
- **positional parameter**: the arguments a script itself received, `$1` for the first, `$2` for the second.
- **test**: a check that is true or false, written `[ ... ]` or `[[ ... ]]`; an `if` decides on its result.
- **command substitution**: running a command and using its output as text, written `$(command)`.
- **unset**: a variable that has never been given a value at all, different from one set to empty.
- **pipeline**: commands joined with `|`, where the output of each becomes the input of the next.

## How it works

Start with quoting. When you write `$file` without quotes, the shell first replaces it with the value, then splits that value into words at spaces. With double quotes, the value stays one argument.

```
{user}@{host}:~$ file="my notes.txt"
{user}@{host}:~$ touch "$file"
{user}@{host}:~$ ls -l $file
ls: cannot access 'my': No such file or directory
ls: cannot access 'notes.txt': No such file or directory
{user}@{host}:~$ ls -l "$file"
-rw-r--r--. 1 {user} {user} 0 Sep  7 09:31 'my notes.txt'
```

The unquoted `ls -l $file` became `ls -l my notes.txt`, three arguments, and `ls` looked for two files that do not exist. The quoted form passed one argument and found the file. The rule is simple: quote every variable that could hold a path, a name, or anything a person typed, which is most of them.

Next, tests. `[` is not punctuation; it is a command, and like every command it needs spaces between itself and its arguments, including the closing `]`.

```
{user}@{host}:~$ a=root; b=root
{user}@{host}:~$ [ "$a"="$b" ] && echo same
same
{user}@{host}:~$ a=root; b=other
{user}@{host}:~$ [ "$a"="$b" ] && echo same
same
```

Both say `same`, and the second one is wrong. Without spaces around `=`, the test received one argument, `root=other`, and a single non-empty string counts as true. Written `[ "$a" = "$b" ]`, with spaces, the second test is false. In bash, `[[ ... ]]` is the safer form: it is part of the shell rather than a separate command, it accepts `==` and `&&` inside, and it does not split unquoted variables.

Command substitution should use `$(command)` rather than backticks. The two do the same job, but `$( )` nests, so `$(dirname $(readlink -f "$0"))` is readable, and it behaves cleanly inside double quotes.

Now the safety line. Put it right under the shebang in every script you write.

```
{user}@{host}:~$ cat > greet.sh <<'EOF'
#!/usr/bin/bash
set -euo pipefail
name="${1:-world}"
if [[ "$name" == "root" ]]; then
    echo "no root here"
    exit 1
fi
echo "hello, $name"
EOF
{user}@{host}:~$ chmod +x greet.sh
{user}@{host}:~$ ./greet.sh
hello, world
{user}@{host}:~$ ./greet.sh "Ada Lovelace"
hello, Ada Lovelace
{user}@{host}:~$ ./greet.sh root; echo "exit $?"
no root here
exit 1
```

`set -euo pipefail` is three switches in one line. `-e` means exit on error: if any command fails, the script stops there instead of carrying on with half-done work. `-u` means unset is an error: reading a variable that was never assigned stops the script, so a typo in a name cannot silently become an empty string. `-o pipefail` means a pipeline fails if any command in it fails, not just the last one, so `grep pattern file | sort` reports the missing file rather than pretending an empty sort succeeded. Together they turn quiet corruption into a loud stop.

`${1:-world}` is the one exception you will use with `-u`: it reads `$1` if it is set and uses `world` if it is not, so an optional argument does not trip the unset check. The `exit 1` returns a non-zero status, which is how the script tells whoever ran it that something was refused.

## When it goes wrong

`./greet.sh: line 3: nmae: unbound variable` is `set -u` catching a typo: the script read `$nmae` and no such variable exists. Fix the spelling, or, if the variable is meant to be optional, give it a default with `${nmae:-}`.

`bash: [root=other: command not found` or `bash: [: missing ']'` means the spaces around `[`, `]` or the operator are missing. Write `[ "$a" = "$b" ]` with a space on both sides of every part, or switch to `[[ ]]`.

A script that stops with no message part way through, when it used to run to the end, is usually `-e` doing its job: some command returned non-zero. Run `bash -x ./greet.sh` (`-x` prints each line before running it) to see which one. `pridwen why` will translate the last failure, and `pridwen explain set` lists what each letter means.

## Try it

1. Create `greet.sh` as above, make it executable, and run it with no argument, expecting `hello, world`.
2. Run `./greet.sh "two words"` and expect both words in the greeting. Remove the quotes around `$name` in the echo line, run again, and see it still works, then think about why `ls -l $file` did not.
3. Change `$name` to `$nmae` on the last line, run the script, and expect `unbound variable`. Put it back.
4. At the prompt, run `[ "$a"="$b" ] && echo same` with different values in `a` and `b`, then add the spaces and see the answer change.
5. Run `false | true; echo $?` and expect `0`, then `set -o pipefail; false | true; echo $?` and expect `1`. Run `set +o pipefail` to turn it off again at the prompt.
6. Rewrite one `[ ... ]` test in the script as `[[ ... ]]` and confirm it still runs.

## Remember

- Quote every variable: `"$file"` is one argument, `$file` may be several.
- `[` is a command; it needs spaces around every part, and `[[ ]]` is the safer bash form.
- `set -euo pipefail`: `-e` stop on error, `-u` unset is an error, `pipefail` any failure in a pipe fails the line.
