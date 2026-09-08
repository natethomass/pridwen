#!/bin/bash
# Seeds a broken "auditor" account (docs/range.md, "Layout": runs once as root
# inside the target before the seeded commit). Every fact this scenario's
# checks look at is deliberately wrong here.
set -euo pipefail

# rocky9-init (the 9-ubi-init tag) ships shadow-utils (useradd, chage) but not
# the separate `passwd` package (passwd, chsh, chfn, gpasswd) — confirmed live:
# `rpm -q passwd` said "package passwd is not installed", so `passwd -l` below
# failed with "command not found" until this line was added.
dnf install -y passwd >/dev/null

groupadd -g 2001 auditors
# No -u: auditor gets whatever UID useradd picks next, not the 2001 compliance wants.
useradd -m -d /home/auditor -g auditors -s /sbin/nologin auditor
echo 'auditor:Sup3rSecret!' | chpasswd
passwd -l auditor
chage -E 1 auditor
chown -R root:root /home/auditor

mkdir -p /opt/range
: > /opt/range/seeded
