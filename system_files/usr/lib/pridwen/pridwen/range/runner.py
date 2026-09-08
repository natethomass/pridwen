"""Range runner: start, enter, check, reset, stop (docs/range.md, "CLI").

Reuses `missions.run_check` against a `ContainerExecutor` and `missions.Progress`
for recording, the same way M3 missions do on the host, so there is no separate
Range progress store. This slice drives `kind: container` scenarios only; a
vm or network scenario is refused with a clear message rather than guessing at
drivers not built yet.
"""
import os

from ..missions import Progress, run_check
from . import Catalog, images
from . import podman
from .targets import ContainerExecutor


class RunnerError(Exception):
    pass


def catalog(share=None):
    return Catalog(share) if share else Catalog()


def _scenario_and_chair(cat, mid):
    if mid not in cat.mission_scenario:
        raise RunnerError(f"No range mission {mid!r}. `pridwen range list` shows what exists.")
    sid, chair = cat.mission_scenario[mid]
    sc = cat.scenarios[sid]
    if sc.kind != "container":
        raise RunnerError(f"{sid} is a {sc.kind} scenario; only container scenarios run in this build.")
    return sc, chair


def _enter_target_name(sc, chair):
    if chair:
        return (sc.chairs.get(chair) or {}).get("enter") or sc.enter
    return sc.enter


def start(mid, cat=None):
    """Create, seed and commit the scenario's target; -> the container name."""
    cat = cat or catalog()
    sc, _chair = _scenario_and_chair(cat, mid)
    target = sc.target()
    if target is None:
        raise RunnerError(f"{sc.id} has no targets.")
    if not images.present(target.image):
        img = images.load().get(target.image)
        size = f" (~{img.size_mb} MiB)" if img else ""
        raise RunnerError(
            f"Image {target.image!r}{size} is not present. Run "
            f"`pridwen range images pull {target.image}` first."
        )
    try:
        name = podman.create(sc.id, target)
        podman.start(name)
        files_dir = os.path.join(sc.dir, "files")
        if os.path.isdir(files_dir):
            podman.copy_files(name, files_dir)
        if target.seed:
            podman.seed(name, os.path.join(sc.dir, target.seed))
        podman.commit(name, podman.seeded_tag(sc.id, target.name))
    except podman.PodmanError as e:
        raise RunnerError(str(e)) from e
    return name


def enter_argv(mid, target_name=None, cat=None):
    cat = cat or catalog()
    sc, chair = _scenario_and_chair(cat, mid)
    tname = target_name or _enter_target_name(sc, chair)
    target = sc.target(tname)
    if target is None:
        raise RunnerError(f"{sc.id} has no target {tname!r}.")
    name = podman.container_name(sc.id, target.name)
    return ["podman", "exec", "-it", "-u", "root", name, "bash"]


def enter(mid, target_name=None, cat=None):
    """Replace this process with an interactive root shell in the target
    (docs/range.md, "CLI": `pridwen range enter` shells into a target as root)."""
    argv = enter_argv(mid, target_name, cat)
    os.execvp(argv[0], argv)


def check(mid, allow_sudo=False, store=None, lib=None, cat=None):
    """Run the mission's checks against the target(s) they name, then record
    through `Progress.record` exactly as a host mission does. `Progress.run_checks`
    is not reusable here: it hardcodes the host executor, so this is the one
    piece Range has to redo (see docs/range.md, "Where a check runs")."""
    cat = cat or catalog()
    sc, chair = _scenario_and_chair(cat, mid)
    m = cat.missions[mid]
    default_target = _enter_target_name(sc, chair)
    results = []
    for i, c in enumerate(m.checks):
        cid = c.get("id", f"check{i}")
        on = c.get("on") or default_target
        target = sc.target(on)
        if target is None:
            results.append((cid, False, f"Check names target {on!r}, which {sc.id} does not have."))
            continue
        executor = ContainerExecutor(podman.container_name(sc.id, target.name))
        ok, msg = run_check(c, allow_sudo, executor)
        results.append((cid, ok, msg))
    if store is not None:
        Progress(store, lib, cat).record(mid, results)
    return results


def reset(mid, target_name=None, cat=None):
    cat = cat or catalog()
    sc, chair = _scenario_and_chair(cat, mid)
    tname = target_name or _enter_target_name(sc, chair)
    targets = list(sc.targets.values()) if tname == "all" else [sc.target(tname)]
    try:
        for target in targets:
            if target is not None:
                podman.reset(sc.id, target)
    except podman.PodmanError as e:
        raise RunnerError(str(e)) from e


def stop(mid, cat=None):
    cat = cat or catalog()
    sc, _chair = _scenario_and_chair(cat, mid)
    for target in sc.targets.values():
        podman.stop(podman.container_name(sc.id, target.name))


def status(cat=None):
    """Every container-target scenario with something up (docs/range.md,
    "Progress, journal and Dispatch": Podman is the source of truth)."""
    cat = cat or catalog()
    rows = []
    for sc in cat.scenarios.values():
        if sc.kind != "container":
            continue
        for item in podman.list_running(sc.id):
            names = item.get("Names") or [item.get("Name", "")]
            labels = item.get("Labels") or {}
            rows.append({
                "scenario": sc.id,
                "target": labels.get("pridwen.target") or (names[0] if names else ""),
                "name": names[0] if names else "",
                "state": item.get("State", "unknown"),
            })
    return rows
