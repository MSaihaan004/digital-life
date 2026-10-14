"""Export Digital Life simulation metrics to CSV."""

import json
from pathlib import Path

from experiments.run_metadata import OutputExistsError, write_csv_exclusive

__all__ = ["CSV_COLUMNS", "export_metrics_csv"]


CSV_COLUMNS = [
    "tick",
    "total_population",
    "living_population",
    "births",
    "deaths",
    "average_energy",
    "average_speed",
    "average_vision",
    "average_metabolism",
    "average_size",
    "average_reproduction_threshold",
    "average_mutation_rate",
    "average_generation",
    "generation_counts",
]


def export_metrics_csv(history, filepath, overwrite=False):
    """Export recorded metrics to a CSV file.

    Column names and formats are unchanged. The write is atomic
    (temporary file + rename) and refuses to overwrite an existing
    file unless ``overwrite`` was explicitly requested.

    Args:
        history: An iterable of metric snapshots.
        filepath: Destination path for the CSV file.
        overwrite: Set True to explicitly replace an existing file.

    Returns:
        The Path of the generated CSV file.

    Raises:
        FileExistsError: If the destination exists and ``overwrite``
            is not True.
    """

    from experiments.run_metadata import OutputExistsError

    output_path = Path(filepath)

    if output_path.exists() and not overwrite:
        raise OutputExistsError(
            f"Refusing to overwrite existing output file: {output_path}. "
            "Choose a new path or request overwrite explicitly."
        )

    rows = []
    for snapshot in history:
        row = dict(snapshot)

        # Store the generation distribution as JSON text.
        row["generation_counts"] = json.dumps(
            row.get("generation_counts", {}),
            sort_keys=True,
        )

        rows.append(row)

    return write_csv_exclusive(
        output_path, rows, CSV_COLUMNS, overwrite=overwrite
    )
