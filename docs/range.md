# Range (M4)

Range is where the learner is allowed to break things. Academy missions run on
the host and are limited to what the immutable base can undo; Range gives the
learner a Rocky Linux 9 machine they own completely, root included, that can be
wrecked and put back in a second. A scenario is a directory: a manifest, one or
more targets, a seed script per target that breaks or plants something, a brief,
and checks that inspect the target's real state afterwards.

Three kinds of target. A **container** target is Rocky 9 with systemd under
rootless Podman: users, permissions, services, timers, sshd, logs, web servers.
It starts in about a second and resets in about a second. A **vm** target is the
Rocky 9 cloud image under session-mode libvirt: storage, LVM, filesystems,
default boot targets, kernel arguments, SELinux relabels — everything that needs
a real kernel and real block devices. A **network** target is an attacker and one
or more victims on an isolated Podman network, which is how recon, web attacks,
credential spraying and privilege escalation are taught, and then replayed from
the defender's chair with the audit log open.

Range invents no new progress model. A scenario chair *is* a mission: the
catalog turns it into the same `Mission` object `missions.py` already produces,
so node state, track progress, the journal and Academy's pages work unchanged
(see `academy.md`, "Node state"). What Range adds is where a check runs.

Two deviations from the concept doc, both deliberate. It says "Podman pods for
most labs"; Range uses plain containers on a Podman network instead, because
containers in a pod share one network namespace and therefore one address, which
is exactly wrong for an attacker and a victim that need to see each other as
separate hosts. And its `packages/pridwen-range/` + `content/scenarios/` layout
predates the conventions M2 and M3 actually settled on, so scenarios live under
`/usr/share/pridwen/` with the rest of the content and the code lives in the
single `pridwen` Python package with the rest of the code.

## Layout

| Path | What |
|---|---|
| `/usr/share/pridwen/scenarios/<id>/scenario.yaml` | manifest: targets, network, chairs, checks |
| `/usr/share/pridwen/scenarios/<id>/brief.md` | long-form brief, one `## chair-<id>` section per chair |
| `/usr/share/pridwen/scenarios/<id>/seed/<target>.sh` | runs once as root inside that target at seed time |
| `/usr/share/pridwen/scenarios/<id>/files/` | payload copied to `/opt/range/` in every target before seeding |
| `/usr/share/pridwen/images.yaml` | pinned image digests, cloud-image URLs and checksums |
| `/usr/share/pridwen/keys/RPM-GPG-KEY-Rocky-9` | key the cloud-image `CHECKSUM` file is verified against |
| `/usr/lib/pridwen/pridwen/range/__init__.py` | scenario catalog, chair → mission expansion |
| `/usr/lib/pridwen/pridwen/range/targets.py` | `Executor` and its three implementations |
| `/usr/lib/pridwen/pridwen/range/podman.py` | container and network lifecycle |
| `/usr/lib/pridwen/pridwen/range/libvirt.py` | VM lifecycle, cloud-init seed ISO, snapshots |
| `/usr/lib/pridwen/pridwen/range/images.py` | fetch, verify, pin |
| `/usr/lib/pridwen/pridwen/range/runner.py` | start, seed, check, reset, stop; journal and Dispatch |
| `/usr/lib/pridwen/pridwen/missions.py` | gains the executor split; host behaviour unchanged |
| `~/.local/share/pridwen/range/images/` | downloaded cloud images and their checksum files |
| `~/.local/share/pridwen/range/vms/<scenario>/` | qcow2 overlay, NoCloud seed ISO, domain XML |
| `~/.local/share/pridwen/range/state.json` | seeded image tags, subnet allocations, last-start times |
| `~/.ssh/pridwen-range` | the key cloud-init installs in VM targets (generated on first use) |
| `/usr/lib/systemd/user/pridwen-range-idle.{service,timer}` | stops targets idle for two hours |

The Python package is `pridwen.range`. It is only ever reached as
`from .range import runner`; nothing inside it may `import range` as a bare
name, which would shadow the builtin.

## Where a check runs

`missions.py` today does two different things to answer a check: it calls
`os.stat`/`open` in process for the `path_*` family, and it shells out through
`_run()` for everything else. Range keeps the whole `CHECK_TYPES` vocabulary and
retargets execution instead of inventing a second schema. The refactor is one
object:

```python
class Executor:
    def run(self, argv, sudo=False, timeout=20): ...   # -> (rc, stdout, stderr)
```

- `HostExecutor` is today's `_run()`, plus the in-process `path_*` fast path, so
  every M3 mission behaves exactly as it does now.
- `ContainerExecutor(name)` runs `podman exec -u root <name> -- <argv>`.
- `VMExecutor(name)` runs `ssh -F <scenario>/ssh_config <name> -- <argv>`, using
  the key cloud-init installed. SSH, not `virsh qemu-agent-command`: the learner
  will be using `ssh` into the same host anyway, the transport is inspectable
  with `-v` when a scenario misbehaves, and the agent path needs JSON wrapping
  around every command. `qemu-guest-agent` is still installed in the guest and
  is used for exactly two things — the readiness probe and a graceful shutdown
  before a snapshot.

Every check type is then expressed as one probe against an executor. On a
non-host executor the `path_*` family becomes argv:

| type | argv on a container or VM target | passes when |
|---|---|---|
| `path_exists` | `test -e -- <path>` | exit 0 |
| `path_missing` | `test -e -- <path>` | exit non-zero |
| `path_type` | `stat -c %F -- <path>` | the word matches `kind` |
| `path_mode` | `stat -c %a -- <path>` | the octal matches `mode` |
| `path_owner` | `stat -c %U:%G -- <path>` | owner (and group) match |
| `path_contains` | `head -c 1048576 -- <path>` | the Python regex matches the bytes returned |
| `sysctl` | `cat /proc/sys/<key with dots as slashes>` | the value matches |

The rule that makes this safe: **the target only ever produces bytes; the regex
is always matched in Python on the host.** No check ships a regex to `grep`,
because POSIX ERE and Python's `re` disagree in exactly the places scenario
authors reach for (`\d`, `\b`, lazy quantifiers), and `{actual}` in a `fail`
message would otherwise mean something different depending on where the check
ran. `path_contains` reads at most one mebibyte; a scenario that needs more
should be using `journal_has` or `cmd_output` with a filter on the target.

`cmd_exit`, `cmd_output`, `unit_*`, `user_exists`, `group_member`, `selinux`,
`firewalld_zone`, `journal_has` already run through `_run()` and need no change
beyond taking the executor. `bootc_rollback` and `env_shell` are host-only and
are refused with a clear message on a Range target — a Rocky container has no
bootc deployment and no learner shell.

`sudo: true` keeps its host meaning (`pkexec`, only when the learner confirms).
On container and VM targets it is ignored, because the executor is already root
inside the target. That is the point of the range.

### Range-only check types

Six types are added; they exist because they need either a second target or a
network to be meaningful.

| type | fields | passes when |
|---|---|---|
| `port_listening` | `port`, optional `proto` (tcp, udp), `on` | `ss -lnH -{t,u}` on the target shows a listener |
| `port_reachable` | `from`, `to` (target name or address), `port` | `timeout 3 bash -c 'exec 3<>/dev/tcp/<to>/<port>'` on `from` exits 0 |
| `port_refused` | `from`, `to`, `port` | the same connect fails |
| `http_status` | `from`, `url`, `status` | `curl -s -o /dev/null -w '%{http_code}' <url>` equals `status` |
| `pkg_installed` | `pkg`, `on` | `rpm -q <pkg>` exits 0 |
| `audit_has` | `regex`, optional `since` (default `-1h`), `on` | `ausearch -i -ts <since>` output matches the Python regex |

Every check may carry `on: <target name>`. Omitted, it means the chair's `enter`
target. `port_reachable` and friends take `from` instead, because the question is
whether the firewall on one host lets another host in — the single most common
thing a defend chair verifies.

### Phases

Checks may declare a phase. The runner runs all `live` checks first; if any
check is `reboot`, it restarts the target (`podman restart`, or `virsh reboot`
plus the readiness probe), waits, then runs those.

```yaml
checks:
  - id: timer-gone
    type: cmd_exit
    cmd: ["systemctl", "list-timers", "--all", "--no-legend"]
    ...
  - id: still-gone-after-reboot
    phase: reboot
    type: path_missing
    path: /etc/cron.d/telemetry
```

This is what "make sure it cannot come back on reboot" means as data. A phase
`reboot` check on a VM target costs a real boot, roughly twenty seconds; on a
container it costs about one.

## Scenario schema (`scenarios/<id>/scenario.yaml`)

```yaml
id: rhcsa-07-webserver          # unique; also the directory name and the mission id
title: Serve a page and let exactly one host in
kind: container                 # container | vm | network
track: rhcsa
node: services                  # the tree node this verifies
required: true
minutes: 30
requires_images: [rocky9-init]  # keys in images.yaml; nothing starts until they are present

targets:
  - name: web-01                # also the container name suffix and the hostname
    image: rocky9-init
    memory: 1g
    pids: 512
    seed: seed/web-01.sh        # runs as root inside the target, once, before the seeded commit
    expose:                     # optional; always bound to 127.0.0.1, never 0.0.0.0
      - {host: 8080, target: 80}

enter: web-01                   # which target `pridwen range enter` drops into
brief: brief.md                 # long form; see "Over-explain, always" in coach.md
steps:
  - Find out which package provides a web server and install it inside web-01.
  - Start it, and make it come back after a reboot.
  - Put a page at the document root that says the host's own name.
  - Open port 80 in firewalld so it survives a restart of the service.
hints:
  - >-
    A service that runs now and a service that runs after a reboot are two
    different states in systemd. `systemctl status` tells you the first,
    `systemctl is-enabled` the second.
  - >-
    `dnf install -y httpd` puts the server in place. `systemctl enable --now
    httpd` does both states at once: `--now` starts it, `enable` writes the
    symlink that starts it at boot. The document root is `/var/www/html`.
  - >-
    In order, inside `pridwen range enter rhcsa-07-webserver`:
    `dnf install -y httpd`, `systemctl enable --now httpd`,
    `hostname > /var/www/html/index.html`,
    `firewall-cmd --permanent --add-service=http`, `firewall-cmd --reload`.
checks:
  - id: installed
    type: pkg_installed
    pkg: httpd
    fail: >-
      `rpm -q httpd` says the package is not installed on web-01. Enter the
      host with `pridwen range enter rhcsa-07-webserver` and run
      `dnf install -y httpd`.
  - id: running
    type: unit_active
    unit: httpd
    fail: >-
      `systemctl is-active httpd` says {actual}, not `active`. `systemctl start
      httpd` starts it now; if it refuses, `systemctl status httpd` prints the
      reason on the last few lines.
  - id: enabled
    type: unit_enabled
    unit: httpd
    fail: >-
      `systemctl is-enabled httpd` says {actual}. That means it is running today
      but will not come back after a reboot. `systemctl enable httpd` writes the
      symlink that fixes it.
  - id: page
    type: http_status
    from: web-01
    url: http://localhost/
    status: 200
    fail: >-
      A request to `http://localhost/` from inside web-01 returned {actual}
      instead of 200. 403 usually means `/var/www/html/index.html` is missing or
      unreadable; 000 means nothing answered on port 80.
  - id: firewall
    type: cmd_output
    cmd: ["firewall-cmd", "--permanent", "--list-services"]
    regex: '\bhttp\b'
    fail: >-
      firewalld's permanent rules are {actual} and do not include `http`, so the
      port closes again on the next reload. `firewall-cmd --permanent
      --add-service=http` then `firewall-cmd --reload`.
  - id: survives
    phase: reboot
    type: unit_active
    unit: httpd
    fail: >-
      After a reboot of web-01, `httpd` is {actual}. The unit starts by hand but
      is not enabled: `systemctl enable httpd`.
```

Field notes:

- `kind` decides the driver, not the number of targets. A `network` scenario is
  the only kind that creates a Podman network and the only one allowed more than
  one container.
- `brief` names a file rather than holding the text, because the over-explain
  rule makes briefs three or four paragraphs and YAML block scalars in a
  manifest that also holds shell payload paths get unreadable fast. `brief.md`
  uses the same restricted markdown subset the lessons use (`coach.md`, "Over-
  explain, always"), with `{user}`, `{home}` and `{host}` filled at render time.
- `steps`, `hints`, `checks` and `fail` follow the mission rules in
  `academy.md` exactly: three hints in escalating order, and a `fail` that
  quotes what the checker saw, translates it, and gives the one command that
  fixes it.
- `required`, `minutes`, `node`, `track` are the `Mission` fields verbatim.

### Chairs

A scenario with `chairs:` produces one mission per chair instead of one for the
scenario. Everything above the `chairs:` key is shared: the targets, the
network, the seed. Everything inside a chair is mission-shaped.

```yaml
chairs:
  attack:
    id: quiet-cron-attack       # optional; defaults to <scenario>-<chair>
    node: persistence
    title: "Persistence: leave something behind"
    enter: attacker
    brief_section: chair-attack # heading in brief.md
    checks: [...]
  defend:
    node: incident-response
    also_verifies: [timers, log-analysis]
    title: "Incident: the quiet cron"
    enter: web-01
    after: quiet-cron-attack    # this chair stays locked until that mission verifies
    from: breached              # start this chair from the post-attack image, not the seed
    checks: [...]
```

`after` is a mission-level prerequisite, distinct from the tree's node-level
`requires`. It is the only new gate: `Progress.mission_state` returns `locked`
when a mission's `after` is not verified, and `node_state` treats a locked
mission the way it treats an unverified one.

`also_verifies` is the second small engine change. A good scenario proves
several things at once — the quiet cron is a lesson in timers, in reading the
journal, and in incident response, and pretending otherwise would mean writing
three thin scenarios instead of one real one. `Mission` gains a `nodes` list
whose first entry is `node`, and `Catalog.for_node` matches on membership rather
than equality. A mission listed under a node still has to be `required: true`
there to be able to verify it, so a scenario cannot accidentally complete a node
it only brushed against.

`from: breached` is how the two-chair replay works and it needs no new
mechanism: see "Reset and snapshots".

## Worked example: a VM target

```yaml
id: rhcsa-11-lvm
title: Grow a filesystem that ran out of room
kind: vm
track: rhcsa
node: storage
minutes: 40
requires_images: [rocky9-cloud]

targets:
  - name: store-01
    image: rocky9-cloud
    vcpus: 2
    memory: 2048              # MiB
    disks:
      - {size: 20G, label: root}      # the backing overlay
      - {size: 4G, label: spare}      # extra blank disk, appears as /dev/vdb
    ssh_port: 2222            # forwarded on 127.0.0.1 only
    seed: seed/store-01.sh

enter: store-01
brief: brief.md
steps:
  - Log in to store-01 and find which filesystem is full and what is under it.
  - Add the blank disk to the volume group that backs it.
  - Grow the logical volume and then the filesystem on top of it.
  - Make sure the mount comes back at boot.
hints:
  - >-
    Three layers sit under a mounted directory here: a physical volume (a whole
    disk or partition handed to LVM), a volume group (a pool made of physical
    volumes), and a logical volume (a slice of the pool that gets a filesystem).
    You grow them from the bottom up, and the filesystem last.
  - >-
    `lsblk` shows the blank disk. `pvcreate /dev/vdb` hands it to LVM,
    `vgextend <vg> /dev/vdb` adds it to the pool, `lvextend -l +100%FREE <lv>`
    takes all of the new room, and `xfs_growfs <mountpoint>` grows the XFS
    filesystem into it while it stays mounted.
  - >-
    In order: `pvcreate /dev/vdb`, `vgextend rangevg /dev/vdb`,
    `lvextend -l +100%FREE /dev/rangevg/data`, `xfs_growfs /srv/data`, then
    `df -h /srv/data` to see the new size and `grep srv /etc/fstab` to confirm
    the mount is written down.
checks:
  - id: pv
    type: cmd_output
    cmd: ["pvs", "--noheadings", "-o", "pv_name"]
    regex: '/dev/vdb'
    fail: >-
      `pvs` lists {actual} and does not include `/dev/vdb`, so the blank disk is
      still outside LVM. `pvcreate /dev/vdb` is the first step.
  - id: size
    type: cmd_output
    cmd: ["findmnt", "-nbo", "SIZE", "/srv/data"]
    regex: '^(?:[6-9]|\d{2,})\d{9}'
    fail: >-
      `/srv/data` is {actual} bytes, still under six gigabytes, so the
      filesystem has not been grown yet. `lvextend -l +100%FREE
      /dev/rangevg/data` takes the space and `xfs_growfs /srv/data` uses it.
  - id: fstab
    type: path_contains
    path: /etc/fstab
    regex: '^\S+\s+/srv/data\s'
    fail: >-
      `/etc/fstab` has no line for `/srv/data`, so the mount disappears at the
      next boot. Add one naming the logical volume by its `/dev/rangevg/data`
      path, then test it with `mount -a` before you trust it.
  - id: mounted-after-reboot
    phase: reboot
    type: cmd_exit
    cmd: ["findmnt", "-n", "/srv/data"]
    fail: >-
      After a reboot, `/srv/data` is not mounted (findmnt exited {actual}). The
      `/etc/fstab` line is wrong or names a device that no longer exists; boot
      messages for it are in `journalctl -b -u local-fs.target`.
```

`disks` beyond the first are blank qcow2 files created at prepare time and
attached as `vdb`, `vdc`. They are part of the snapshot, so a reset returns them
to blank.

## Worked example: a network target with two chairs

```yaml
id: quiet-cron
title: The quiet cron
kind: network
track: defend
minutes: 60
requires_images: [rocky9-init, attacker]

network:
  subnet: 10.66.12.0/24
  internal: true

targets:
  - name: web-01
    image: rocky9-init
    ip: 10.66.12.20
    seed: seed/web-01.sh
  - name: listener
    image: rocky9-init
    ip: 10.66.12.30
    seed: seed/listener.sh
  - name: attacker
    image: attacker
    ip: 10.66.12.10

brief: brief.md
dispatch:
  - id: quiet-cron-noticed
    after: 120                  # seconds after the environment comes up
    chair: defend
    title: Unusual login on web-01
    body: >-
      A range host logged a session you did not start. Open the scenario and
      find out what it is doing.

chairs:
  attack:
    node: persistence
    title: "Persistence: leave something behind"
    enter: attacker
    brief_section: chair-attack
    steps:
      - From the attacker host, find the service web-01 is running and get a shell on it.
      - Leave something behind that runs every five minutes and calls home to the listener.
      - Make it survive a reboot without being an obvious cron job.
    hints: [...]
    checks:
      - id: beacon
        type: journal_has
        on: listener
        regex: 'GET /pixel'
        since: '-10m'
        fail: >-
          The listener has seen no request in ten minutes ({actual}). Whatever
          you left on web-01 either is not running or cannot reach
          10.66.12.30. Check it by hand on web-01 first, then check the route.
      - id: survives
        phase: reboot
        type: journal_has
        on: listener
        regex: 'GET /pixel'
        since: '-6m'
        fail: >-
          After web-01 rebooted, the listener stopped hearing from it, so the
          persistence lives only in memory or in a session that ends at logout.
          Something that runs at boot is a unit, a timer, or a line in a file
          systemd or the shell reads at startup.
  defend:
    node: incident-response
    title: "Incident: the quiet cron"
    enter: web-01
    after: quiet-cron-attack
    from: breached
    brief_section: chair-defend
    steps:
      - Find what on web-01 is making an outbound request every five minutes.
      - Work out how it starts and who put it there, using the journal and the audit log.
      - Stop it and remove every copy of it, including the way it comes back at boot.
      - Close the way in, and prove the block survives a firewalld reload.
    hints: [...]
    checks:
      - id: quiet
        type: journal_has
        on: listener
        regex: 'GET /pixel'
        since: '-8m'
        expect: absent
        fail: >-
          The listener is still hearing from web-01 ({actual} in the last eight
          minutes), so something is still running. `systemctl list-timers --all`
          and `ls -l /etc/cron.d/` on web-01 name the usual two places.
      - id: dropper-gone
        type: path_missing
        on: web-01
        path: /usr/local/sbin/telemetry
        fail: >-
          `/usr/local/sbin/telemetry` is still on disk. Removing the timer
          without removing the script leaves it one line away from coming back.
      - id: profile-clean
        type: path_contains
        on: web-01
        path: /etc/profile.d/00-locale.sh
        regex: 'telemetry'
        expect: absent
        fail: >-
          `/etc/profile.d/00-locale.sh` still mentions `telemetry`. Files in
          `/etc/profile.d/` are read by every interactive login shell, which is
          why they are a favourite hiding place.
      - id: blocked
        phase: reboot
        type: port_refused
        from: attacker
        to: web-01
        port: 80
        fail: >-
          The attacker can still reach port 80 on web-01 after a reboot. A
          `firewall-cmd` change without `--permanent` disappears on reload;
          `firewall-cmd --permanent --remove-service=http --reload` makes it stick.
```

`expect: absent` inverts any check. It exists because half of every defend chair
is proving that something is *not* there any more, and writing that as a
separate `journal_lacks` type for every existing type would double the table.

The two chairs are one environment and two missions. `pridwen range start
quiet-cron` brings up the network, the two victims and the attacker once. The
attack chair drops the learner into `attacker`; the defend chair drops them into
`web-01` with the journal and audit log of what they themselves just did. The
tree wires them together without any Range-specific mechanism: `persistence`
verifies from one, `incident-response` from the other, and every Attack node
ends up twinned with a Defend node because they share the manifest.

## Reset and snapshots

### Containers

The lifecycle is create → seed → commit → run, and reset throws away the
container, never the seeded image.

`--systemd=always` only prepares systemd-friendly mounts and the stop signal;
it does not replace the image's own `CMD`. Rocky's base image `CMD` is
`/bin/bash`, which under `podman create` reads no stdin and exits at once
(confirmed live in the M1 test VM: the container showed `Exited (0)` seconds
after `podman start`), so the command is named explicitly, `/sbin/init`.

```
podman network create --internal --subnet 10.66.12.0/24 pridwen-quiet-cron
podman create --name pridwen-quiet-cron-web-01 --hostname web-01 \
    --network pridwen-quiet-cron:ip=10.66.12.20 \
    --systemd=always --stop-signal SIGRTMIN+3 \
    --memory 1g --pids-limit 512 \
    --label pridwen.scenario=quiet-cron --label pridwen.target=web-01 \
    quay.io/rockylinux/rockylinux@sha256:<pinned> /sbin/init
podman start pridwen-quiet-cron-web-01
podman cp <scenario dir>/files/. pridwen-quiet-cron-web-01:/opt/range/
podman exec pridwen-quiet-cron-web-01 bash /opt/range/../seed/web-01.sh
podman commit pridwen-quiet-cron-web-01 pridwen/scenario/quiet-cron/web-01:seeded
```

Reset is `podman rm -f` on the container and `podman create` from the `:seeded`
image. That is why it takes about a second: the expensive part — the package
installs and the file layout the seed script performs — is already baked into a
local image layer and never runs twice.

Podman's own `container checkpoint` is deliberately not used. It needs CRIU, it
is fragile rootless, and it fails often on containers running systemd, which is
every Range container. A commit is boring and always works.

`from: breached` in a chair means the runner commits again after the previous
chair verifies — `pridwen/scenario/quiet-cron/web-01:breached` — and creates
from that tag instead. The defender inherits the attacker's mess, including the
journal and the audit log, because those live in the container's writable layer
and a commit captures them.

Teardown (`pridwen range stop`) removes containers and the network and leaves
both image tags. `pridwen range clean <id>` removes the tags too; `pridwen range
clean --images` also removes the pulled bases.

### VMs

```
qemu-img create -f qcow2 -F qcow2 \
    -b ~/.local/share/pridwen/range/images/Rocky-9-GenericCloud.qcow2 \
    ~/.local/share/pridwen/range/vms/rhcsa-11-lvm/root.qcow2 20G
xorrisofs -V CIDATA -J -r -o .../seed.iso user-data meta-data
virsh -c qemu:///session define .../domain.xml
virsh -c qemu:///session start pridwen-rhcsa-11-lvm-store-01
```

The base cloud image is a *backing file* and is never written to, so a scenario
costs only the bytes it dirties and a corrupted lab can never poison the
download. `user-data` creates `{user}` inside the guest with the learner's
Range SSH key, `NOPASSWD` sudo and a known password, and installs
`qemu-guest-agent`. That guest account is deliberately more permissive than the
desktop's: the range is where the learner gets root, the daily driver is not.

Once cloud-init reports done and `seed/<target>.sh` has run over SSH, the runner
takes a **running** snapshot, memory included:

```
virsh -c qemu:///session snapshot-create-as pridwen-rhcsa-11-lvm-store-01 \
    seeded --atomic
```

Reset is `virsh snapshot-revert ... seeded`, which restores disk and RAM
together, so the VM comes back in about two seconds already booted with services
up rather than twenty seconds of POST and systemd. The cost is one copy of the
guest's RAM inside the qcow2, which is why VM targets default to 2048 MiB and
the manifest has to say so explicitly to ask for more.

Teardown is `virsh destroy` then `virsh undefine --nvram`, followed by removing
the scenario's own directory under `range/vms/`. The base image in
`range/images/` survives; it is shared by every VM scenario.

## Podman, libvirt, and the hardened host

Range asks the host for nothing that a normal desktop user does not already
have. Stated plainly, control by control:

- **Containers are rootless**, run as the learner, and Podman is already in the
  base image. No `docker` group, no rootful socket, no new polkit rule. Storage
  lands in `~/.local/share/containers`, which is on the LUKS volume.
- **The one thing rootless Podman needs is a subuid/subgid range** for the
  learner. `useradd` writes one; users created by the first-boot wizard through
  AccountsService do not always get one. M4 extends
  `/usr/libexec/pridwen-firstboot` to write the range at account creation, and
  `pridwen range doctor` checks `/etc/subuid` on every existing install and
  prints the one-time fix (`sudo usermod --add-subuids 100000-165535
  --add-subgids 100000-165535 {user}`) rather than running it.
- **libvirt runs in session mode** (`qemu:///session`), as the learner. This is
  the decision that keeps the security story simple: no `libvirt` group, no
  `org.libvirt.unix.manage` polkit rule, no system daemon holding the learner's
  disk images. The build enables the user socket with
  `systemctl --global enable virtqemud.socket`.
- Session mode costs two things and both are accepted. Guests get user-mode
  networking (passt) rather than a libvirt NAT bridge, so a VM reaches the
  outside through the learner's own network stack and is reachable from the host
  only on forwarded ports; and VM-to-VM traffic is not possible. Multi-host
  networks are therefore always container scenarios, which is where they belong
  anyway — twelve RHCSA VM scenarios need one machine each.
- **`/dev/kvm`** is `0666` under Fedora's default udev rules, so no group is
  needed. Where it is not, `pridwen range doctor` names `kvm` as the group to
  add. That is the only group membership Range ever asks for and it grants
  nothing but access to the virtualisation device.
- **SELinux stays enforcing on the host.** Rootless container bind mounts use
  `:Z`; the scenario payload is copied with `podman cp` rather than mounted,
  which sidesteps labelling entirely. Session-mode qemu runs as the learner
  under an unconfined domain, so VM disk images in `$HOME` need no relabel —
  a documented consequence of session mode, not a weakening of the host policy.
  SELinux *inside* a Rocky target is enforcing and is the subject of several
  scenarios.
- **firewalld's drop zone is untouched.** No Range target ever listens on a host
  interface. `expose` entries bind to `127.0.0.1` and go through Podman's
  rootless port handler; VM SSH forwards bind to `127.0.0.1` too. If a learner's
  browser needs to see a scenario's web server, it reaches it on
  `http://127.0.0.1:8080`, which no firewalld zone governs.
- **USBGuard, auditd and DNS over TLS are unaffected.** Range touches no USB
  device and adds no resolver.
- **Range never uses sudo on the host and refuses to run as root.** `pridwen
  range` exits with an explanation if `os.geteuid() == 0`, because a scenario
  started as root would put root-owned containers in the learner's storage and
  break every later rootless command.
- **Attack tooling is never installed on the host.** `nmap`, `hydra`, `nikto`
  and the rest live in the attacker container image only. The desktop stays a
  desktop.

Resource limits are part of the manifest, not the driver: containers default to
1 GiB and 512 PIDs, VMs to 2 vCPU and 2048 MiB. `pridwen-range-idle.timer` runs
every fifteen minutes as a user timer and stops any target whose scenario has
had no `enter` or `check` for two hours, so a forgotten lab does not sit on
memory. Stopping is not resetting: the seeded image and the snapshot stay, and
`pridwen range start` brings it back where it was.

## Host targets

The concept doc calls the fourth kind "live missions": scenarios that run
against the learner's own machine, limited to what the immutable base can undo.
These need no Range driver at all — they are M3 missions with `target: host`,
which already work — but M4 makes the category explicit, because the reason they
are safe is worth teaching. "Harden your own sshd config" is undone by a
`bootc rollback`; so is "roll back last week's update and diff what changed",
which is why `bootc_rollback` is already in the check table. A host scenario may
carry `undo: rollback` in its manifest, which does nothing but make Academy show
the sentence "this changes your real machine; `sudo bootc rollback` puts it
back" above the brief, and refuse to offer the mission on a machine whose
`bootc status` shows no rollback deployment to fall back to.

The line is drawn at the Posture table. A host scenario may change a control
that Posture already tracks, because Posture will show the drift and the learner
can put it back. A host scenario may not disable SELinux, open the firewall to a
network, or enable sshd without the learner performing that step themselves and
seeing it in the posture panel afterwards. Anything more destructive than that
belongs on a VM target, which is also where the two controls Pridwen
deliberately does not ship — fapolicyd and full STIG enforcement — will be
taught when M6 gets to them: on a throwaway Rocky 9 VM where a learner can feel
exactly what they cost without losing a desktop for the afternoon.

## Images (`images.yaml`)

Nothing is baked into the Pridwen image. A 700 MiB cloud image has no business
in an OS every user pulls on every update, and mirroring another distribution's
media is not this project's job. Images are fetched on the learner's machine, on
purpose, into `~/.local/share/pridwen/range/images/`.

```yaml
rocky9-init:
  kind: container
  ref: quay.io/rockylinux/rockylinux
  digest: sha256:<64 hex>        # pulled by digest; the pull is self-verifying
  about: Rocky Linux 9 with systemd as PID 1. The target for most scenarios.
  size_mb: 250

attacker:
  kind: container
  ref: <pinned attacker base>
  digest: sha256:<64 hex>
  about: Recon and web tooling. Only ever runs on an internal network.
  size_mb: 900

rocky9-cloud:
  kind: cloud
  url: https://dl.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud-Base-<v>.x86_64.qcow2
  checksum_url: https://dl.rockylinux.org/pub/rocky/9/images/x86_64/CHECKSUM
  sha256: <64 hex>
  gpg_key: /usr/share/pridwen/keys/RPM-GPG-KEY-Rocky-9
  about: Rocky Linux 9 cloud image, booted under libvirt for storage and boot work.
  size_mb: 600
```

Container images are pinned by digest, so `podman pull ref@sha256:…` verifies
itself and a tag moving underneath us cannot change what a scenario runs. The
cloud image is verified twice: `gpg --verify` on Rocky's signed `CHECKSUM`
against the key shipped in the OS image, then the sha256 from that file compared
with both the downloaded file and the value pinned in `images.yaml`. A mismatch
between the two pins is treated as an error, not as a reason to trust the
network. A VM whose backing file did not verify is never defined.

`pridwen range start` on a scenario whose `requires_images` are missing prints
what it would download and how large it is, and waits for the learner to run
`pridwen range images pull <key>`. Range never downloads several hundred
megabytes on its own.

## Progress, journal and Dispatch

**Progress.** `Catalog` gains a second loader that reads
`scenarios/*/scenario.yaml` and yields `Mission` objects — one per chair, or one
per scenario when there are no chairs. Those missions carry `target` set to
`container`, `vm` or `network`, plus `scenario`, `chair` and `after`. Everything
downstream is unchanged: `mission_state`, `node_state`, `track_progress`, the
`missions` and `journal` tables. There is no Range progress store.

Runtime state is not learning data and does not go in SQLite. Podman and libvirt
are the source of truth, queried by label
(`podman ps --filter label=pridwen.scenario=<id>`,
`virsh list --all --name`); `state.json` caches only the seeded image tags,
subnet allocations and last-touch times, and is rebuildable by deleting it.

**Guide (M5).** Nothing in this design waits on Guide, but two hooks are placed
now so M5 does not have to reopen the schema. A chair may set `socratic: true`,
which Academy passes to Guide when it is present: during that mission Guide says
where to look and never what to type, which is the mode the concept doc names
for graded missions. And every check carries its `id` into the journal, so Guide
can be asked "why did `dropper-gone` fail" and have something concrete to read.
Until M5 both are inert data.

**Journal.** The runner writes `store.journal("range", <scenario>, …)` for
start, seed, reset, breach commit and teardown. Mission results already go
through `Progress.record` as kind `mission`, so a defend chair that fails shows
its failing check in the same list as a Coach firing from ten minutes earlier.
`pridwen journal` needs one new label.

**Dispatch.** Scenarios can make things happen to the learner rather than only
waiting for them. A `dispatch:` block in the manifest declares notifications the
runner raises: `after: <seconds>` from environment start, or `on: check-fail`,
or `on: idle`. The runner sends them through the existing socket as an event
line the daemon already knows how to route:

```json
{"v":1,"event":"range_incident","scenario":"quiet-cron","title":"Unusual login on web-01","body":"..."}
```

`daemon.py` gains an event line alongside the command line; `Dispatch.on_event`
does the rest. Scenario notifications obey the same quiet hours and the same cap
of three a day as every other nudge, which is the point of routing them through
Dispatch rather than calling libnotify directly. Their actions are **Open**
(Academy on that chair) and **Not this again**.

## Academy

A fifth sidebar row, **Range**, next to Skill tree, Tracks, Journal and Posture.

- **Range** lists scenarios with a state chip (down, starting, up, breached), a
  target chip (container, vm, network), the images they need and whether those
  are present. Buttons: Start, Enter, Check, Reset, Stop.
- **Scenario** shows the brief for the current chair, the steps, the hints one at
  a time, a target list with each host's name and address, and Check — the same
  page shape the Mission page already has, plus the target list and a Range
  toolbar.
- Range missions also appear inline on the existing **Node** and **Track** pages
  with their target chip, because a track is an ordered list of missions and
  RHCSA's list is mostly scenarios.
- **Enter** launches Ptyxis running `pridwen range enter <id> [target]`. Academy
  never embeds a terminal.

The M3 threading rule holds and matters more here, because Range operations are
slow: image pulls take minutes, a VM define and boot takes twenty seconds.
**Never touch `Store` from a worker thread.** Long operations run off-thread and
report back with `GLib.idle_add`; the store write and the progress recording
happen on the main thread. Every Range button shows a determinate or spinning
state and a status line that surfaces the driver's stderr verbatim when
something fails, because "Starting…" forever is the failure mode M3 already hit.

## CLI

| Command | Does |
|---|---|
| `pridwen range list [track]` | scenarios with state, target kind, and whether their images are present |
| `pridwen range show <id>` | brief, steps, targets, checks, and what it unlocks |
| `pridwen range start <id>` | create the network and targets, seed them, commit `:seeded`, print how to enter |
| `pridwen range enter [<id>] [target]` | shell into a target as root; with no id, the only running scenario |
| `pridwen range check <id>` | run the chair's checks against its targets, record the result, print each line |
| `pridwen range reset <id> [target]` | back to `:seeded` (or the chair's `from:`), one target or all |
| `pridwen range stop <id>` | stop and remove containers and the network, or shut the VM down; keep the seed |
| `pridwen range status` | every scenario with a live target: uptime, addresses, memory, idle time |
| `pridwen range images [pull\|verify] [key]` | list, download or re-verify the pinned images |
| `pridwen range clean [<id>] [--images]` | remove seeded and breached tags, VM overlays, and optionally the bases |
| `pridwen range doctor` | preflight: cgroup v2, subuid range, `/dev/kvm`, `virtqemud.socket`, free disk, images |
| `pridwen enter rocky` | a scratch Rocky 9 container that belongs to no scenario; `--fresh` recreates it |

`pridwen mission check <id>` keeps working for scenario missions: it looks at
`Mission.target` and hands off to the Range runner, so nothing that reads
missions needs to know Range exists. `pridwen range check` is the alias that
also prints target state first, which is what a learner staring at a failing
check actually wants.

`pridwen enter rocky` is the odd one out on purpose. It is not a scenario: it is
a long-lived container named `pridwen-rocky` from the same pinned Rocky 9 image,
kept across reboots, for the moment a learner wants to try something as root
without a mission attached. It is the answer to "where do I practise `dnf` on a
machine I can't hurt", and it is the first Range thing most people will run.

`pridwen range doctor` output is the shape of a posture panel: one line per
condition, `pass` or the exact command that fixes it, never a fix run on the
learner's behalf.

## Scenario inventory (24)

M4's deliverable, by track and target kind. Node ids are the tree's.

| id | kind | node |
|---|---|---|
| `rhcsa-01-users` | container | users |
| `rhcsa-02-permissions` | container | permissions |
| `rhcsa-03-processes` | container | processes |
| `rhcsa-04-services` | container | services |
| `rhcsa-05-timers` | container | timers |
| `rhcsa-06-packages` | container | packages |
| `rhcsa-07-webserver` | container | services |
| `rhcsa-08-ssh` | container | ssh |
| `rhcsa-09-selinux` | container | selinux |
| `rhcsa-10-firewall` | container | firewall |
| `rhcsa-11-lvm` | vm | storage |
| `rhcsa-12-boot` | vm | boot |
| `def-01-first-hour` | container | incident-response |
| `def-02-log-story` | container | log-analysis |
| `def-03-file-integrity` | container | detection |
| `def-04-timeline` | vm | forensics |
| `quiet-cron` (defend chair) | network | incident-response |
| `spray` (defend chair) | network | detection |
| `atk-01-map-it` | network | recon |
| `atk-02-web-input` | network | web |
| `quiet-cron` (attack chair) | network | persistence |
| `spray` (attack chair) | network | credentials |
| `atk-03-sudo-hole` | container | privesc |
| `atk-04-key-reuse` | network | credentials |

Twelve RHCSA, six defend, six attack. Two of the defend and two of the attack
entries are chairs of shared scenarios, which is the "attack and defend twins on
one network" half of the milestone.

The runner is bounded work; twenty-four scenarios are not. Each one is a
manifest, a seed script that has to break something in a way that is findable,
a three-paragraph brief, three escalating hints and five or six checks with
`fail` messages that quote and translate. Build the runner against two or three
scenarios — one per target kind — and treat the remaining twenty-one as content,
paced like the M2 rules library was.

## Testing

Range runs on an installed Pridwen machine and nowhere else. There is no podman
on the Windows checkout and CI builds only the OS image, so nothing about Range
can be exercised from this repo. What CI can do is check shape: a `just
lint-scenarios` step that loads every `scenario.yaml`, asserts the manifest
schema, asserts every check `type` is known, every `on`/`from` names a declared
target, every `node` exists in `tree.yaml`, every `requires_images` key exists in
`images.yaml`, every referenced `seed/` and `files/` path is present, and no
content hard-codes a username instead of `{user}`.

Everything else is verified by hand in a VM, in the M0/M1 order: push, CI green,
`bootc upgrade` in the test VM, reboot, `pridwen range doctor`, run the scenario.
Container and network targets work fine inside the existing VirtualBox VMs —
rootless Podman is namespaces, not virtualisation. **VM targets cannot be tested
there**: the host runs Hyper-V, VirtualBox falls back to its slower backend, and
nested KVM is not available. `rhcsa-11-lvm`, `rhcsa-12-boot` and `def-04-timeline`
have to be verified on bare metal or on Proxmox with nested virtualisation
enabled. That is a known M4 gap to plan around, not one to discover late: the
ten container RHCSA scenarios and all six network scenarios are the ones that
can be iterated on quickly.
