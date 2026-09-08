"""Pinned images (docs/range.md, "Images"). Container images only in this
slice: cloud images are pulled and GPG-verified for VM targets, which this
build does not yet drive.
"""
import os
import subprocess

import yaml

from .. import SHARE


class Image:
    def __init__(self, key, d):
        self.key = key
        self.kind = d.get("kind", "container")
        self.ref = d.get("ref", "")
        self.digest = d.get("digest", "")
        self.about = d.get("about", "")
        self.size_mb = int(d.get("size_mb", 0))
        self.url = d.get("url")
        self.checksum_url = d.get("checksum_url")
        self.sha256 = d.get("sha256")
        self.gpg_key = d.get("gpg_key")

    @property
    def pinned(self):
        return f"{self.ref}@{self.digest}"


def load(share=SHARE):
    path = os.path.join(share, "images.yaml")
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return {k: Image(k, v) for k, v in data.items() if isinstance(v, dict)}


def present(key, images=None):
    """True when the pinned digest is already pulled. False for anything that
    is not a container image or not found, never raises."""
    images = images if images is not None else load()
    img = images.get(key)
    if img is None or img.kind != "container":
        return False
    try:
        r = subprocess.run(["podman", "image", "exists", img.pinned], timeout=10)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def pull(key, images=None):
    """-> (ok, message). Pins by digest, so the pull is self-verifying
    (docs/range.md, "Images")."""
    images = images if images is not None else load()
    img = images.get(key)
    if img is None:
        return False, f"Unknown image {key!r}."
    if img.kind != "container":
        return False, f"{key!r} is a {img.kind} image; only container images can be pulled in this build."
    try:
        r = subprocess.run(["podman", "pull", img.pinned], capture_output=True, text=True, timeout=1800)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return False, "podman: not found"
    except subprocess.TimeoutExpired:
        return False, "timed out"
