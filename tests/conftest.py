"""Small synthetic AEI + O*NET files with the real column layout."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

AEI_COLS = ["date_start", "date_end", "geo_id", "geo_level", "category_name", "hierarchy_level",
            "metric_id", "value", "node_name", "node_external_id"]  # fmt: skip

SOC = "99-0001.00"
APR, MAY = "2026-04-01", "2026-05-01"


def _aei_row(month, metric, value, node, category="onet", geo="GLOBAL", level=0):
    end = {"2026-04-01": "2026-05-01", "2026-05-01": "2026-06-01"}[month]
    geo_level = "global" if geo == "GLOBAL" else "country"
    return [month, end, geo, geo_level, category, level, metric, value, f"node {node}", node]


def _task(month, task_id, a, u, pct=0.5):
    rows = [_aei_row(month, "pct", pct, task_id)]
    if a is not None:
        rows.append(_aei_row(month, "collaboration_bucket_automation_pct", a, task_id))
    if u is not None:
        rows.append(_aei_row(month, "collaboration_bucket_augmentation_pct", u, task_id))
    return rows


def _write(path: Path, header: list[str], rows: list[list]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


@pytest.fixture
def fixture_files(tmp_path: Path) -> dict[str, Path]:
    # Tasks: 1 matched 80/20, 2 matched 30/70, 3 unmatched, 4 zero denominator, 5 partial (A only)
    claude = []
    claude += _task(MAY, "1", 80, 20) + _task(APR, "1", 70, 30)
    claude += _task(MAY, "2", 30, 70) + _task(APR, "2", 30, 70)
    claude += _task(MAY, "4", 0, 0)
    claude += _task(MAY, "5", 60, None)
    # Same task in a country row and at a higher hierarchy level: must be ignored.
    claude.append(_aei_row(MAY, "collaboration_bucket_automation_pct", 1, "2", geo="USA"))
    claude.append(_aei_row(MAY, "collaboration_bucket_automation_pct", 1, "2", level=1))
    # Occupation-level split.
    for month, a in ((MAY, 55.5), (APR, 50.0)):
        claude.append(_aei_row(month, "collaboration_bucket_automation_pct", a, SOC, "soc_occupation"))
        claude.append(_aei_row(month, "collaboration_bucket_augmentation_pct", 100 - a, SOC, "soc_occupation"))
        claude.append(_aei_row(month, "pct", 0.2, SOC, "soc_occupation"))
        claude.append(_aei_row(month, "pct", 0.9, "99-0002.00", "soc_occupation"))

    api = _task(MAY, "1", 95, 5) + _task(MAY, "2", 90, 10) + _task(MAY, "3", 99, 1)

    statements = [
        [SOC, "Test Occupation", "1", "Write the thing.", "Core", 10, "08/2023", "Incumbent"],
        [SOC, "Test Occupation", "2", "Talk to people.", "Core", 10, "08/2023", "Incumbent"],
        [SOC, "Test Occupation", "3", "Plan the safeguards.", "Supplemental", 10, "08/2023", "Incumbent"],
        [SOC, "Test Occupation", "4", "Zero bucket task.", "Core", 10, "08/2023", "Incumbent"],
        [SOC, "Test Occupation", "5", "Partial bucket task.", "Core", 10, "08/2023", "Incumbent"],
        ["99-0002.00", "Other Occupation", "9", "Other work.", "Core", 10, "08/2023", "Incumbent"],
    ]
    importance = {"1": 4.0, "2": 2.0, "3": 5.0, "4": 3.0, "5": 1.0, "9": 3.0}
    ratings = []
    for tid, im in importance.items():
        soc = "99-0002.00" if tid == "9" else SOC
        ratings.append([soc, "t", tid, "task", "IM", "Importance", "", im, 10, "", "", "", "N", "08/2023", "Incumbent"])
        # FT: half category 2, half category 6 -> mean 4.0
        for cat in (2, 6):
            ratings.append([soc, "t", tid, "task", "FT", "Frequency", cat, 50.0, 10, "", "", "", "N", "08/2023", "Inc"])

    onet = tmp_path / "onet"
    return {
        "claude_ai": _write(tmp_path / "aei_claude_ai.csv", AEI_COLS, claude),
        "1p_api": _write(tmp_path / "aei_1p_api.csv", AEI_COLS, api),
        "task_statements.csv": _write(
            onet / "task_statements.csv",
            [
                "O*NET-SOC Code",
                "Title",
                "Task ID",
                "Task",
                "Task Type",
                "Incumbents Responding",
                "Date",
                "Domain Source",
            ],
            statements,
        ),  # fmt: skip
        "occupation_data.csv": _write(
            onet / "occupation_data.csv",
            ["O*NET-SOC Code", "Title", "Description"],
            [[SOC, "Test Occupation", "d"], ["99-0002.00", "Other Occupation", "d"]],
        ),
        "task_ratings.csv": _write(
            onet / "task_ratings.csv",
            [
                "O*NET-SOC Code",
                "Title",
                "Task ID",
                "Task",
                "Scale ID",
                "Scale Name",
                "Category",
                "Data Value",
                "N",
                "Standard Error",
                "Lower CI Bound",
                "Upper CI Bound",
                "Recommend Suppress",
                "Date",
                "Domain Source",
            ],
            ratings,
        ),  # fmt: skip
    }
