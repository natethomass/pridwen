# From command to script

A script is just a file of commands the shell runs in order. Turning a working
command line into one lets you repeat it reliably and share it. Three things make
a file runnable: a shebang, the execute bit, and a path.

The shebang is the first line, `#!/usr/bin/bash`, telling the kernel which
interpreter to use. The execute bit is set with `chmod +x`. And because the
current directory is not on PATH in Fedora, you run a local script as `./name`,
naming its path explicitly so the shell does not confuse it with a system
command.

```
$ cat > hello.sh <<'EOF'
#!/usr/bin/bash
echo "Hello from $(hostname)"
EOF
$ chmod +x hello.sh
$ ./hello.sh
Hello from pridwen
```

Two failures explain most "it will not run" moments. Exit 126 means it was found
but not executable, so `chmod +x` it or run `bash name` once. Exit 127 with the
file present usually means you forgot the `./`. A script edited on Windows can
carry carriage returns that break the shebang, fixed with `sed -i 's/\r$//'`. Put
scripts you use everywhere in `~/.local/bin`, which is on your PATH by default.

## Try it

1. Write the hello script above, make it executable, and run it with `./`.
2. Remove the execute bit with `chmod -x` and watch it fail with exit 126.
3. Move the script to `~/.local/bin` and run it by name from another directory.
4. Explain why Fedora leaves the current directory off PATH.
