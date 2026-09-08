"""Range: scenarios as missions (docs/range.md).

A scenario becomes one Mission per chair, or one Mission when it has no chairs,
reusing missions.Mission verbatim so node state, track progress, the journal
and Academy's pages need not know Range exists (docs/range.md, "Where a check
runs" and "Progress, journal and Dispatch"). This slice fully drives
`kind: container` scenarios only; `vm`, `network` and `chairs` scenarios load
without raising so `pridwen range list` can show them, but running them is
later work (see `runner.py`).

Reached from outside this package only as `from .range import runner`; nothing
in here imports `range` as a bare name, which would shadow the builtin.
"""
import glob
import os

import yaml

from .. import SHARE
from ..missions import Mission


def _yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _brief_text(scenario_dir, brief_name, section=None):
    """Read scenario.yaml's `brief` file; a chair's `brief_section` pulls the
    `## <section>` heading out of it (docs/range.md, "Layout"). A missing file
    or heading falls back rather than raising, so a content typo never blocks
    the mission from loading."""
    if not brief_name:
        return ""
    path = os.path.join(scenario_dir, brief_name)
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return ""
    if not section:
        return text
    marker = f"## {section}"
    start = text.find(marker)
    if start < 0:
        return text
    start += len(marker)
    end = text.find("\n## ", start)
    return text[start:end if end >= 0 else None].strip()


class Target:
    def __init__(self, d):
        self.name = d.get("name", "")
        self.image = d.get("image", "")
        self.memory = d.get("memory", "1g")
        self.pids = int(d.get("pids", 512))
        self.seed = d.get("seed")
        self.ip = d.get("ip")
        self.expose = list(d.get("expose") or [])


class Scenario:
    """The manifest fields Mission does not carry: targets, images, network, chairs."""

    def __init__(self, d, source):
        self.d = d
        self.source = source
        self.dir = os.path.dirname(source)
        self.id = d["id"]
        self.kind = d.get("kind", "container")
        self.requires_images = list(d.get("requires_images") or [])
        self.targets = {t["name"]: Target(t) for t in (d.get("targets") or []) if t.get("name")}
        self.network = d.get("network")
        self.enter = d.get("enter") or (next(iter(self.targets), None))
        self.chairs = d.get("chairs") or {}

    def target(self, name=None):
        return self.targets.get(name or self.enter)


class Catalog:
    """Scenarios as missions (see module docstring) plus the raw manifest the
    runner needs (targets, images, seed paths) that Mission has no field for."""

    def __init__(self, share=SHARE):
        self.share = share
        self.scenarios = {}
        self.missions = {}
        self.mission_scenario = {}   # mission id -> (scenario id, chair name or None)
        self.errors = []
        for p in sorted(glob.glob(os.path.join(share, "scenarios", "*", "scenario.yaml"))):
            try:
                d = _yaml(p)
                sc = Scenario(d, p)
                self.scenarios[sc.id] = sc
                self._add_missions(sc, d)
            except (KeyError, TypeError, yaml.YAMLError, OSError) as e:
                self.errors.append(f"{p}: {e}")

    def _mission_dict(self, sc, d, node, title, brief, steps, hints, checks, also_verifies, after):
        return {
            "id": None, "node": node, "title": title, "track": d.get("track", ""),
            "required": d.get("required", True), "minutes": d.get("minutes", 10),
            "target": sc.kind, "brief": brief, "steps": steps, "hints": hints,
            "checks": checks, "also_verifies": also_verifies, "after": after,
        }

    def _add_missions(self, sc, d):
        if sc.chairs:
            for chair, cd in sc.chairs.items():
                mid = cd.get("id") or f"{sc.id}-{chair}"
                brief = _brief_text(sc.dir, d.get("brief"), cd.get("brief_section"))
                md = self._mission_dict(
                    sc, d, cd.get("node", ""), cd.get("title", mid), brief,
                    list(cd.get("steps") or []), list(cd.get("hints") or []),
                    list(cd.get("checks") or []), list(cd.get("also_verifies") or []),
                    cd.get("after"),
                )
                md["id"] = mid
                self.missions[mid] = Mission(md, sc.source)
                self.mission_scenario[mid] = (sc.id, chair)
        else:
            brief = _brief_text(sc.dir, d.get("brief"))
            md = self._mission_dict(
                sc, d, d.get("node", ""), d.get("title", sc.id), brief,
                list(d.get("steps") or []), list(d.get("hints") or []),
                list(d.get("checks") or []), list(d.get("also_verifies") or []),
                d.get("after"),
            )
            md["id"] = sc.id
            self.missions[sc.id] = Mission(md, sc.source)
            self.mission_scenario[sc.id] = (sc.id, None)

    def for_node(self, node):
        return [m for m in self.missions.values() if node in m.nodes]

    def for_track(self, track):
        return [m for m in self.missions.values() if m.track == track]
