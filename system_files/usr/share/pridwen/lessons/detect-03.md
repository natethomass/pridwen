# Alerts that reach you

A detection that no one reads is not much of a detection. The last step is
turning a noticed event into a message that reaches a person, on Pridwen through
the same Dispatch notifications the Coach uses, and on a server through a log a
monitor watches.

The simplest reliable pattern is a systemd timer that runs a check and, when the
check finds something, writes a high-priority journal line and sends a desktop
notification. Because the check is a unit, its own runs are logged, so you can
tell the difference between "nothing happened" and "the check never ran".

```
#!/usr/bin/bash
if ss -tuln | grep -q ':4444'; then
    logger -p security.warning -t detect "unexpected listener on 4444"
    notify-send "Detection" "Unexpected listener on port 4444"
fi
```

On a Range host you wire this to a timer, trigger the condition, and confirm the
alert arrives. The design questions are the ones that separate a useful alert
from noise: it must fire on the real thing often enough to trust and rarely
enough to keep reading. An alert that cries wolf gets muted, and a muted alert is
the same as none, so tuning the threshold is part of the work, not an afterthought.

## Try it

1. Write a check script that tests for a specific unexpected condition.
2. Have it log a priority line and call `notify-send` when the condition is true.
3. Run it from a user timer and trigger the condition to see the alert.
4. Explain why an alert that fires too often ends up ignored.
