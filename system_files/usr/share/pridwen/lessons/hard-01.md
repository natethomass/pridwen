# The baseline as data

Hardening on Pridwen is not a pile of scripts you run once; it is a set of
decisions expressed as configuration, each one readable and each one a lesson.
The kernel side of it lives in sysctl settings under `/etc/sysctl.d/`, applied at
boot and visible any time with `sysctl`.

A sysctl is a kernel tunable. `sysctl key` reads one; `sudo sysctl -w key=value`
sets it until reboot; the persistent value belongs in a file under
`/etc/sysctl.d/` and loads with `sudo sysctl --system`. Pridwen ships hardened
values there, such as restricting the kernel log and pointer exposure.

```
$ sysctl kernel.dmesg_restrict
kernel.dmesg_restrict = 1
$ sysctl kernel.kptr_restrict net.ipv4.ip_forward
```

Each of these is a small door. `kernel.dmesg_restrict=1` keeps the kernel ring
buffer from ordinary users, `kernel.kptr_restrict` hides kernel addresses that
help exploits, and `net.ipv4.ip_forward=0` says this machine is not a router.
The point of treating the baseline as data is that you can read exactly what is
set, check it against what should be, and explain why each value is there, which
is what the posture panel does automatically.

## Try it

1. Read three of Pridwen's sysctl values and say what each protects.
2. Set one temporarily with `sudo sysctl -w` and read it back.
3. Find where the persistent values live under `/etc/sysctl.d/`.
4. Explain why a `-w` change does not survive a reboot on its own.
