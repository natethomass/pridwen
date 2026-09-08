"""Container lifecycle (docs/range.md, "Reset and snapshots > Containers").

Create -> seed -> commit -> run; reset throws away the container, never the
seeded image. Single-target scenarios only in this slice, so no Podman
network is created here.
"""
import json
import subprocess

from . import images as images_mod


class PodmanError(Exception):
    pass


def _run(argv, timeout=120):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return 127, "", "podman: not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"


def _run_stdin(argv, input_text, timeout=120):
    try:
        r = subprocess.run(argv, input=input_text, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return 127, "", "podman: not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"


def _require(rc, out, err, action):
    if rc != 0:
        raise PodmanError(f"{action} failed: {(err or out).strip() or f'exit {rc}'}")


def container_name(scenario_id, target_name):
    return f"pridwen-{scenario_id}-{target_name}"


def seeded_tag(scenario_id, target_name):
    return f"pridwen/scenario/{scenario_id}/{target_name}:seeded"


def _create_argv(name, scenario_id, target, image_ref):
    # --systemd=always only prepares systemd-friendly mounts and the stop signal; it does
    # not replace the image's own CMD. Rocky's base image CMD is /bin/bash, which reads no
    # stdin under `podman create` and exits immediately (confirmed live: the container
    # showed "Exited (0)" right after start), so the container's actual init must be named
    # explicitly.
    return [
        "podman", "create", "--name", name, "--hostname", target.name,
        "--systemd=always", "--stop-signal", "SIGRTMIN+3",
        "--memory", str(target.memory), "--pids-limit", str(target.pids),
        "--label", f"pridwen.scenario={scenario_id}", "--label", f"pridwen.target={target.name}",
        image_ref, "/sbin/init",
    ]


def create(scenario_id, target):
    """podman create from the pinned digest named in images.yaml."""
    name = container_name(scenario_id, target.name)
    img = images_mod.load().get(target.image)
    if img is None:
        raise PodmanError(f"Unknown image {target.image!r} for target {target.name!r}.")
    rc, out, err = _run(_create_argv(name, scenario_id, target, img.pinned))
    _require(rc, out, err, f"podman create {name}")
    return name


def start(name):
    rc, out, err = _run(["podman", "start", name])
    _require(rc, out, err, f"podman start {name}")


def copy_files(name, files_dir):
    rc, out, err = _run(["podman", "cp", f"{files_dir}/.", f"{name}:/opt/range/"])
    _require(rc, out, err, f"podman cp {files_dir} -> {name}:/opt/range/")


def seed(name, seed_path):
    """Feeds the seed script to `bash` over stdin rather than copying it into
    the target first: the script is read-only OS content under
    /usr/share/pridwen, not part of the target's writable layer, so nothing
    from it needs cleaning up afterwards."""
    try:
        with open(seed_path, encoding="utf-8") as f:
            script = f.read()
    except OSError as e:
        raise PodmanError(f"could not read seed script {seed_path}: {e}") from e
    rc, out, err = _run_stdin(["podman", "exec", "-i", "-u", "root", name, "bash"], script, timeout=600)
    _require(rc, out, err, f"seed script on {name}")


def commit(name, tag):
    rc, out, err = _run(["podman", "commit", name, tag])
    _require(rc, out, err, f"podman commit {name} -> {tag}")


def rm(name):
    _run(["podman", "rm", "-f", name])


def reset(scenario_id, target, from_tag=None):
    """Drop the container, recreate it from the seeded (or a chair's `from:`)
    image tag. Cheap: the package installs and file layout the seed script
    performed are already baked into that layer."""
    name = container_name(scenario_id, target.name)
    rm(name)
    tag = from_tag or seeded_tag(scenario_id, target.name)
    rc, out, err = _run(_create_argv(name, scenario_id, target, tag))
    _require(rc, out, err, f"podman create {name} from {tag}")
    start(name)
    return name


def stop(name):
    """podman rm -f: keeps the seeded/breached image tags (docs/range.md, "Teardown")."""
    rm(name)


def list_running(scenario_id):
    """Podman is the source of truth for what is up, queried by label
    (docs/range.md, "Progress, journal and Dispatch")."""
    rc, out, _err = _run(["podman", "ps", "-a", "--filter", f"label=pridwen.scenario={scenario_id}", "--format", "json"])
    if rc != 0 or not out.strip():
        return []
    try:
        data = json.loads(out)
    except ValueError:
        return []
    return data if isinstance(data, list) else []
