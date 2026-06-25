# SPDX-License-Identifier: Apache-2.0
"""
Path resolution for the `.council/` namespace.

All project-local state (decision records, dissent log, config, optional project
council overrides + model registry) lives under `.council/`, resolvable via
$COUNCIL_DIR or the current working directory. Bundled package data (the
council definitions, the lens roster, the default model registry) lives inside
the installed package.
"""

from __future__ import annotations

import os
from pathlib import Path


def council_dir() -> Path:
    """Resolve the project `.council/` directory: $COUNCIL_DIR or ./.council."""
    override = os.environ.get("COUNCIL_DIR")
    return Path(override) if override else (Path.cwd() / ".council")


def decisions_dir() -> Path:
    return council_dir() / "decisions"


def dissent_dir() -> Path:
    return council_dir() / "dissent"


def config_path() -> Path:
    return council_dir() / "config.toml"


def project_models_path() -> Path:
    """Project-level model registry override (if the user pins their own)."""
    return council_dir() / "council-models.json"


def project_councils_dir() -> Path:
    """Project-level council-definition overrides."""
    return council_dir() / "councils"


def package_dir() -> Path:
    return Path(__file__).resolve().parent


def bundled_councils_dir() -> Path:
    return package_dir() / "councils"


def bundled_lenses_path() -> Path:
    return package_dir() / "lenses.yaml"


def bundled_models_path() -> Path:
    return package_dir() / "council-models.json"
