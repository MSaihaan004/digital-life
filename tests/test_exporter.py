import csv
import json

from evolution.exporter import CSV_COLUMNS, export_metrics_csv


def sample_history():
    return [
        {
            "tick": 1,
            "total_population": 101,
            "living_population": 100,
            "births": 1,
            "deaths": 0,
            "average_energy": 75.5,
            "average_speed": 0.6,
            "average_vision": 0.7,
            "average_metabolism": 0.4,
            "average_size": 0.5,
            "average_reproduction_threshold": 0.6,
            "average_mutation_rate": 0.1,
            "average_generation": 0.2,
            "generation_counts": {0: 99, 1: 1},
        },
        {
            "tick": 2,
            "total_population": 102,
            "living_population": 99,
            "births": 1,
            "deaths": 2,
            "average_energy": 68.0,
            "average_speed": 0.61,
            "average_vision": 0.69,
            "average_metabolism": 0.41,
            "average_size": 0.51,
            "average_reproduction_threshold": 0.59,
            "average_mutation_rate": 0.1,
            "average_generation": 0.3,
            "generation_counts": {0: 98, 1: 1},
        },
    ]


def test_exports_csv_header_and_rows(tmp_path):
    output_file = tmp_path / "metrics.csv"

    result = export_metrics_csv(
        sample_history(),
        output_file,
    )

    assert result == output_file
    assert output_file.exists()

    with output_file.open(
        newline="",
        encoding="utf-8",
    ) as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert reader.fieldnames == CSV_COLUMNS
    assert len(rows) == 2

    assert rows[0]["tick"] == "1"
    assert rows[0]["living_population"] == "100"
    assert rows[1]["tick"] == "2"
    assert rows[1]["births"] == "1"


def test_exports_generation_counts_as_json(tmp_path):
    output_file = tmp_path / "metrics.csv"

    export_metrics_csv(sample_history(), output_file)

    with output_file.open(
        newline="",
        encoding="utf-8",
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))

    generations = json.loads(rows[0]["generation_counts"])

    assert generations == {"0": 99, "1": 1}


def test_exports_empty_history(tmp_path):
    output_file = tmp_path / "empty.csv"

    export_metrics_csv([], output_file)

    assert output_file.exists()

    with output_file.open(
        newline="",
        encoding="utf-8",
    ) as csv_file:
        reader = csv.reader(csv_file)
        rows = list(reader)

    # An empty history should still produce a valid header.
    assert rows == [CSV_COLUMNS]


def test_creates_missing_directories(tmp_path):
    output_file = (
        tmp_path
        / "nested"
        / "exports"
        / "metrics.csv"
    )

    export_metrics_csv(sample_history(), output_file)

    assert output_file.exists()


def test_does_not_modify_original_history(tmp_path):
    history = sample_history()

    original_generation_counts = dict(
        history[0]["generation_counts"]
    )

    export_metrics_csv(
        history,
        tmp_path / "metrics.csv",
    )

    assert (
        history[0]["generation_counts"]
        == original_generation_counts
    )
