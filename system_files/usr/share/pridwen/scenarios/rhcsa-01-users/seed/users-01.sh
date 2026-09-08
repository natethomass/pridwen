#!/bin/bash
# Seeds a broken "auditor" account (docs/range.md, "Layout": runs once as root
# inside the target before the seeded commit). Every fact this scenario's
# checks look at is deliberately wrong here.
set -euo pipefail

groupadd -g 2001 auditors
# No -u: auditor gets whatever UID useradd picks next, not the 2001 compliance wants.
useradd -m -d /home/auditor -g auditors -s /sbin/nologin auditor
echo 'auditor:Sup3rSecret!' | chpasswd
passwd -l auditor
chage -E 1 auditor
chown -R root:root /home/auditor

mkdir -p /opt/range
: > /opt/range/seeded
