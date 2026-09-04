# Variables and quoting

The shell expands your line before any program sees it. It substitutes
variables, runs command substitutions, splits the result on spaces, and matches
filename patterns. Knowing that order explains most surprises with spaces and
special characters.

A variable is set with no spaces around the equals sign and read with a dollar
sign. Quoting controls expansion. Double quotes expand `$var` and `$(cmd)` but
keep the text as one word. Single quotes are literal, so nothing inside expands.
No quotes at all means the value is also split on whitespace and treated as a
glob.

```
$ name="Ada Lovelace"
$ echo $name
Ada Lovelace
$ echo "$name" | wc -w
2
$ echo '$name'
$name
```

The rule of thumb is to double-quote every variable that holds a path or
anything that might contain a space, which on a real system is most of them.
`"$file"` survives a filename with a space in it; `$file` becomes two arguments
and the command misfires. Single quotes are for text you want passed through
untouched, like a regex or a literal dollar sign.

## Try it

1. Set `greeting="hello world"` and print it with and without double quotes.
2. Compare `echo "$HOME"` and `echo '$HOME'` and explain the difference.
3. Make a file with a space in its name and remove it using double quotes.
4. Run `echo *` in a directory to watch the shell expand the glob before echo runs.
