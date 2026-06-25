# SPDX-License-Identifier: Apache-2.0
"""
Council catalog — load, validate, and merge council definitions.

Bundled councils live in the package (`councils/*.yaml`); a project may override
or add its own in `.council/councils/`. Project definitions win on id collision.

A malformed council fails LOUD (`schema.SchemaError`) — callers treat that as a
fail-closed state (the council is unusable; never silently half-loaded). Pure,
offline, stdlib + pyyaml.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from . import paths
from .schema import Council, SchemaError, parse_council


def _load_dir(d: Path) -> dict[str, Council]:
    out: dict[str, Council] = {}
    if not d.exists():
        return out
    for p in sorted(d.glob("*.yaml")):
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            raise SchemaError(f"could not read council file {p}: {exc}") from exc
        council = parse_council(data)
        out[council.id] = council
    return out


def load_councils(project_dir: Path | None = None) -> dict[str, Council]:
    """Return {id: Council} from bundled defs, overlaid with project defs."""
    councils = _load_dir(paths.bundled_councils_dir())
    project = project_dir / ".council" / "councils" if project_dir else paths.project_councils_dir()
    councils.update(_load_dir(project))
    return councils


def get_council(council_id: str, project_dir: Path | None = None) -> Council:
    councils = load_councils(project_dir)
    if council_id not in councils:
        raise SchemaError(f"unknown council: {council_id!r} (have: {', '.join(sorted(councils)) or 'none'})")
    return councils[council_id]


def list_councils(project_dir: Path | None = None) -> list[Council]:
    return [c for _, c in sorted(load_councils(project_dir).items())]
