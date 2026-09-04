# Quoting and safety

Most script bugs are not logic errors; they are the shell splitting a value you
did not expect, or a comparison written with the wrong spacing. A few habits make
scripts survive spaces, empty values, and other people.

Quote every variable that could hold a path or spaces, which is most of them:
`"$file"` stays one argument, `$file` becomes several. Test with the right
spacing, because `[` is a command: `[ "$a" = "$b" ]` needs spaces around the
brackets and the operator. In bash, `[[ ... ]]` is safer and supports `==` and
`&&`. Prefer `$(command)` over backticks for substitution because it nests and
quotes cleanly.

```
#!/usr/bin/bash
set -euo pipefail
name="${1:-world}"
if [[ "$name" == "root" ]]; then
    echo "no root here"
    exit 1
fi
echo "hello, $name"
```

The header `set -euo pipefail` is the seatbelt: `-e` stops on the first error,
`-u` treats an unset variable as an error rather than an empty string, and
`pipefail` makes a failure anywhere in a pipe fail the line. With those on, a typo
in a variable name becomes a loud "unbound variable" instead of a silent empty
value that corrupts the rest of the run.

## Try it

1. Write a script that echoes `"$1"` and run it with an argument containing a space.
2. Remove the quotes and watch the argument split into words.
3. Add `set -u` and reference an unset variable to see it fail loudly.
4. Rewrite a `[ ... ]` test as `[[ ... ]]` and note what changes.
