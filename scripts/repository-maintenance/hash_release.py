"""Compute reproducible file counts and aggregate SHA-256 values for a release candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache"}


def eligible(path: Path, *, whole_tree: bool = False) -> bool:
    relative = path.relative_to(ROOT)
    if not path.is_file() or path.suffix == ".pyc":
        return False
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    return not (whole_tree and relative.as_posix() == "RELEASE_SNAPSHOT.md")


def collect(paths: list[str], *, whole_tree: bool = False) -> list[Path]:
    files: set[Path] = set()
    for item in paths:
        path = ROOT / item
        if path.is_file() and eligible(path, whole_tree=whole_tree):
            files.add(path)
        elif path.is_dir():
            files.update(candidate for candidate in path.rglob("*") if eligible(candidate, whole_tree=whole_tree))
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def aggregate(files: list[Path]) -> dict[str, str | int]:
    records = []
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append(f"{relative}\t{digest}")
    payload = "\n".join(records).encode("utf-8")
    return {"files": len(files), "sha256": hashlib.sha256(payload).hexdigest()}


def main() -> None:
    groups = {
        "focus": ["plugins/rcf-focus/skills"],
        "address": ["plugins/rcf-address/skills"],
        "distill": ["plugins/rcf-distill/skills"],
        "theory": [
            "docs/theory.zh-CN.md",
            "docs/methodology",
            "docs/spec",
            "docs/dynamic-addressing",
            "docs/release-scope.md",
        ],
        "concepts": ["docs/concepts"],
        "lineage": [
            "docs/philosophy",
            "docs/comparisons",
            "docs/comparison-matrix.zh-CN.md",
            "docs/references.md",
        ],
    }
    result = {name: aggregate(collect(paths)) for name, paths in groups.items()}
    result["whole_tree"] = aggregate(collect(["."], whole_tree=True))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
