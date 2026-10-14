"""Shared run-metadata recording for Digital Life experiments.

The helpers here are additive: experiment CSV formats are left
unchanged. Each experiment may write a ``<experiment_id>_run_metadata.json``
sidecar capturing the exact configuration, code revision, and
per-run success/failure accounting so outputs can be traced back
to the conditions that produced them.
"""
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import config as config_module


CONFIG_FIELDS = (
    "WORLD_WIDTH", "WORLD_HEIGHT",
    "INITIAL_POPULATION", "INITIAL_FOOD",
    "STARTING_ENERGY", "MAX_ENERGY", "FOOD_ENERGY",
    "STARTING_HEALTH",
    "FOOD_TARGET_COUNT", "FOOD_MAX_COUNT", "FOOD_RESPAWN_PER_TICK",
    "MAX_AGE", "EAT_DISTANCE", "RANDOM_SEED",
    "REPRODUCTION_ENERGY_COST",
    "DEFAULT_TICKS_PER_SECOND", "MIN_TICKS_PER_SECOND",
    "MAX_TICKS_PER_SECOND",
)


def collect_config_snapshot():
    """Return current configuration values plus validation errors."""
    snapshot = {name: getattr(config_module, name) for name in CONFIG_FIELDS}
    return {
        "values": snapshot,
        "validation_errors": config_module.validate_config(),
    }


def write_metadata_sidecar(output_dir, metadata, overwrite=False):
    """Write ``<experiment_id>_run_metadata.json``; return its Path.

    Refuses to overwrite an existing sidecar unless ``overwrite``
    is explicitly requested. The metadata must identify the actual
    output files of the invocation (see ``extra["output_file"]``).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{metadata['experiment_id']}_run_metadata.json"
    return write_text_exclusive(
        path,
        json.dumps(metadata, indent=2, default=str),
        overwrite=overwrite,
    )


def code_revision():
    """Return the current git revision, or 'unknown' when unavailable."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def build_run_metadata(experiment_id, seeds, ticks, extra=None,
                       run_statuses=None):
    """Build a metadata record for one experiment invocation."""
    metadata = {
        "experiment_id": experiment_id,
        "seeds": list(seeds),
        "ticks": ticks,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "code_revision": code_revision(),
        "config": collect_config_snapshot(),
    }
    if extra:
        metadata["extra"] = dict(extra)
    statuses = list(run_statuses or [])
    metadata["runs"] = statuses
    metadata["successful_runs"] = sum(
        1 for s in statuses if s.get("status") == "success"
    )
    metadata["failed_runs"] = sum(
        1 for s in statuses if s.get("status") != "success"
    )
    return metadata


class OutputExistsError(FileExistsError):
    """Raised when an experiment output path already exists.

    The message names the colliding path so the caller can choose
    a new run directory or pass overwrite explicitly.
    """


def write_text_exclusive(path, text, overwrite=False, newline=None):
    """Write text atomically without silently overwriting outputs.

    The content is written to a temporary file in the same
    directory and linked into place with ``os.link``, which fails
    atomically if the destination already exists. Concurrent
    attempts to create the same output therefore cannot silently
    replace one another: exactly one wins, the rest receive
    ``OutputExistsError``. With ``overwrite=True`` the temporary
    file is moved into place with ``os.replace`` instead.

    Raises:
        OutputExistsError: If ``path`` exists and ``overwrite``
            was not explicitly requested.
    """
    path = Path(path)
    if path.exists() and not overwrite:
        raise OutputExistsError(
            f"Refusing to overwrite existing output file: {path}. "
            "Choose a new run directory or request overwrite explicitly."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline=newline) as tmp_file:
            tmp_file.write(text)
        if overwrite:
            os.replace(tmp_name, path)
        else:
            try:
                os.link(tmp_name, path)
            except FileExistsError:
                raise OutputExistsError(
                    f"Refusing to overwrite existing output file: {path}. "
                    "Choose a new run directory or request overwrite explicitly."
                )
            finally:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return path


def write_csv_exclusive(output_path, rows, fieldnames, overwrite=False):
    """Write CSV rows atomically with overwrite protection.

    ``fieldnames`` (the CSV schema) are written unchanged. Uses
    ``newline=""`` so output bytes match the project's existing
    CSV writer behavior on all platforms.
    """
    import csv
    import io

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames,
                            extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return write_text_exclusive(
        output_path, buffer.getvalue(), overwrite=overwrite, newline=""
    )


def unique_run_dir(base_dir, experiment_id):
    """Create a unique run directory; never reuse an existing one.

    Names look like ``<experiment_id>_20261015_003000`` with a
    numeric suffix on collision. Directory creation itself is the
    atomic collision guard (``exist_ok=False``).
    """
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    candidate = base_dir / f"{experiment_id}_{stamp}"
    counter = 0
    while True:
        try:
            candidate.mkdir(exist_ok=False)
            return candidate
        except FileExistsError:
            counter += 1
            candidate = base_dir / f"{experiment_id}_{stamp}_{counter}"
