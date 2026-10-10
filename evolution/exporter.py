"""Export Digital Life simulation metrics to CSV."""

import csv
import json
from pathlib import Path


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


def export_metrics_csv(history, filepath):
    """Export recorded metrics to a CSV file.

    Args:
        history: An iterable of metric snapshots.
        filepath: Destination path for the CSV file.

    Returns:
        The Path of the generated CSV file.
    """

    output_path = Path(filepath)

    # Create the destination directory if it does not exist.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_COLUMNS,
            extrasaction="ignore",
        )

        writer.writeheader()

        for snapshot in history:
            row = dict(snapshot)

            # Store the generation distribution as JSON text.
            row["generation_counts"] = json.dumps(
                row.get("generation_counts", {}),
                sort_keys=True,
            )

            writer.writerow(row)

    return output_path
