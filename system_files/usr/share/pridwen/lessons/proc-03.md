# Jobs and staying alive

The shell can run more than one thing at once. A command followed by `&` starts
in the background and hands you the prompt back. Ctrl-Z stops the foreground
command and parks it as a job. `jobs` lists them, `fg` brings one forward, and
`bg` resumes a stopped one in the background.

```
$ sleep 300 &
[1] 5100
$ jobs
[1]+  Running   sleep 300 &
$ fg %1
sleep 300
^Z
[1]+  Stopped   sleep 300
$ bg %1
```

Background jobs belong to the shell that started them and normally end when you
log out. `nohup command &` detaches one so it survives, writing its output to
`nohup.out`. For anything that should really keep running, though, a systemd
unit is the better tool: `systemd-run --user command` gives it a name, a place
in the journal, and a clean way to stop it, which a bare background job does not
have.

## Try it

1. Start `sleep 300 &`, run `jobs`, and read the job number.
2. Bring it forward with `fg`, stop it with Ctrl-Z, and resume it with `bg`.
3. Start a job with `nohup sleep 60 &` and find its output file.
4. Run `systemd-run --user --on-active=10s true` and find it in `list-timers`.
