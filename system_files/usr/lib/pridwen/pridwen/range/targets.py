"""Range executors: retarget missions.run_check's CHECK_TYPES at a Range target
instead of the host (docs/range.md, "Where a check runs"). This slice ships
only the container executor; VMExecutor is later work.
"""
import subprocess


class ContainerExecutor:
    """Duck-types missions.HostExecutor: `.run(argv, sudo=False, timeout=20) ->
    (rc, stdout, stderr)`. `sudo` is a no-op here: `podman exec` is already
    root inside the target, which is the point of the range."""

    def __init__(self, name):
        self.name = name

    def run(self, argv, sudo=False, timeout=20):
        # No "--" separator: confirmed live that this podman passes it straight to
        # crun as the command to run ("executable file `--` not found in $PATH"),
        # rather than treating it as an end-of-options marker. `-u root` before the
        # container name is unambiguous without one.
        cmd = ["podman", "exec", "-u", "root", self.name, *argv]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return r.returncode, r.stdout, r.stderr
        except FileNotFoundError:
            return 127, "", "podman: not found"
        except subprocess.TimeoutExpired:
            return 124, "", "timed out"
