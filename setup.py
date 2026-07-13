"""Setuptools build hook for embedding the source revision in wheels."""
from __future__ import annotations

import os
import re
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


ROOT = Path(__file__).resolve().parent
_SHA = re.compile(r"^[0-9a-f]{40}$")
_BUILD_REVISION = re.compile(r"^(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})$")


def _read_git_revision() -> str | None:
    dot_git = ROOT / ".git"
    if dot_git.is_file():
        marker = dot_git.read_text(encoding="utf-8").strip()
        if not marker.startswith("gitdir: "):
            return None
        git_dir = (ROOT / marker.removeprefix("gitdir: ")).resolve()
    elif dot_git.is_dir():
        git_dir = dot_git
    else:
        return None

    head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if _SHA.fullmatch(head):
        return head
    if not head.startswith("ref: "):
        return None
    ref = head.removeprefix("ref: ")
    ref_path = git_dir / ref
    if ref_path.is_file():
        value = ref_path.read_text(encoding="utf-8").strip()
        return value if _SHA.fullmatch(value) else None
    packed_refs = git_dir / "packed-refs"
    if packed_refs.is_file():
        for line in packed_refs.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith(("#", "^")):
                value, name = line.split(" ", 1)
                if name == ref and _SHA.fullmatch(value):
                    return value
    return None


def _build_revision() -> str:
    configured = os.environ.get("EDUFLOW_BUILD_REVISION", "").strip()
    if configured:
        if not _BUILD_REVISION.fullmatch(configured):
            raise RuntimeError(
                "EDUFLOW_BUILD_REVISION must be a 40-character Git SHA or "
                "a sha256:<64-hex> source-tree digest"
            )
        return configured
    return _read_git_revision() or "unknown"


class build_py(_build_py):
    def run(self) -> None:
        super().run()
        target = Path(self.build_lib) / "eduflow" / "_build_info.py"
        target.write_text(
            "\"\"\"Build metadata generated while packaging EduFlow.\"\"\"\n"
            f"BUILD_REVISION = {_build_revision()!r}\n",
            encoding="utf-8",
        )


setup(cmdclass={"build_py": build_py})
