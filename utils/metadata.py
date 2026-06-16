"""Utility for writing dataset metadata JSON files."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from settings import ROOT_DIR


class Source(TypedDict, total=False):
    """Provenance record for a raw external data source."""

    name: str
    url: str | None
    download_date: str | None
    description: str | None


class _MetadataEncoder(json.JSONEncoder):
    """JSON encoder that handles Path objects and tuples."""

    def default(self, obj: object) -> object:
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

    def encode(self, obj: object) -> str:
        return super().encode(self._convert(obj))

    def _convert(self, obj: object) -> object:
        if isinstance(obj, tuple):
            return list(obj)
        if isinstance(obj, dict):
            return {k: self._convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._convert(item) for item in obj]
        return obj


def _get_git_commit() -> str | None:
    """Return the current short git commit hash.

    Returns:
        Short commit hash, or None if git is unavailable.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT_DIR,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _to_relative(path: Path | str) -> str:
    """Convert path to POSIX string relative to repo root.

    Args:
        path: Absolute or relative path.

    Returns:
        POSIX path string relative to ROOT_DIR, or absolute POSIX string if
        path is outside the repo.
    """
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return resolved.as_posix()


def write_metadata(
    output_dir: Path | str,
    *,
    script: str,
    inputs: list[Path | str],
    outputs: list[Path | str],
    params: dict,
    description: str,
    sources: list[Source] | None = None,
) -> None:
    """Write a metadata.json file to the given output directory.

    Creates or overwrites metadata.json in output_dir with provenance
    information about the dataset: which script produced it, from which
    inputs, with which parameters, and when.

    Args:
        output_dir: Directory where metadata.json is written.
        script: Path to the producing script — pass __file__.
        inputs: Input file paths consumed by the script.
        outputs: Output file paths written by the script.
        params: Script parameters used for this run.
        description: Human-readable description of the dataset.
        sources: Raw external data sources. Defaults to [].

    Raises:
        OSError: If metadata.json cannot be written.
    """
    metadata = {
        "description": description,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "script": _to_relative(script),
        "git_commit": _get_git_commit(),
        "params": params,
        "inputs": [_to_relative(p) for p in inputs],
        "outputs": [_to_relative(p) for p in outputs],
        "sources": sources if sources is not None else [],
    }

    output_path = Path(output_dir) / "metadata.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, cls=_MetadataEncoder)
