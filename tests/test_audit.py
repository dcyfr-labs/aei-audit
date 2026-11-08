from __future__ import annotations

import math

import pytest

from aei_audit.audit import OUTPUT_COLUMNS, month_key, month_label, run_audit
from tests.conftest import MAY, SOC


def _run(files, **kw):
    aei = {k: files[k] for k in ("claude_ai", "1p_api") if k in files}
    onet = {k: files[k] for k in ("task_statements.csv", "occupation_data.csv", "task_ratings.csv")}
    return run_audit([SOC], aei, onet, release="test", **kw)


def _head(files, **kw):
    res = _run(files, **kw).results[SOC]
    return res, res.headline.set_index("Task ID")


def test_automation_share_is_a_over_a_plus_u(fixture_files):
    _, h = _head(fixture_files)
    assert h.loc["1", "automation_share"] == pytest.approx(0.8)
    assert h.loc["2", "automation_share"] == pytest.approx(0.3)
    assert h.loc["1", "lean"] == "automation"
    assert h.loc["2", "lean"] == "augmentation"


def test_unmatched_task_is_kept_not_zeroed(fixture_files):
    res, h = _head(fixture_files)
    assert "3" in h.index
    assert not h.loc["3", "matched"]
    assert math.isnan(h.loc["3", "automation_share"])
    assert h.loc["3", "lean"] == "unmatched"
    assert [r["Task ID"] for r in res.summary["unmatched"]] == ["3"]
    assert res.summary["n_tasks"] == 5


def test_zero_denominator_excluded_from_means(fixture_files):
    res, h = _head(fixture_files)
    assert h.loc["4", "matched"]
    assert math.isnan(h.loc["4", "automation_share"])
    assert h.loc["4", "lean"] == "no_split"
    # Mean over tasks with a share: 1 (0.8), 2 (0.3), 5 (A only -> 1.0); task 4 excluded.
    assert res.summary["mean_auto_share"] == pytest.approx(round((0.8 + 0.3 + 1.0) / 3, 3))


def test_partial_bucket_sets_low_count_flag(fixture_files):
    _, h = _head(fixture_files)
    assert h.loc["5", "low_count_flag"]
    assert not h.loc["1", "low_count_flag"]


def test_importance_weighting(fixture_files):
    res, _ = _head(fixture_files)
    # 1: 0.8*4, 2: 0.3*2, 5: 1.0*1  over weights 4+2+1
    expected = (0.8 * 4 + 0.3 * 2 + 1.0 * 1) / 7
    assert res.summary["importance_weighted_auto_share"] == pytest.approx(round(expected, 3))


def test_frequency_category_mean(fixture_files):
    _, h = _head(fixture_files)
    assert h.loc["1", "freq_cat_mean"] == pytest.approx(4.0)


def test_api_kept_separate(fixture_files):
    res, h = _head(fixture_files)
    assert h.loc["1", "api_share"] == pytest.approx(0.95)
    assert res.summary["n_api_matched"] == 3  # task 3 has API data but no claude_ai row; it is still counted
    assert res.summary["mean_auto_share"] < 0.8  # API values did not leak into the headline
    # Task 3 is unmatched in claude_ai even though the API has it.
    assert not h.loc["3", "matched"]


def test_api_matched_counts_tasks_with_api_share(fixture_files):
    _, h = _head(fixture_files)
    assert h["api_share"].notna().sum() == 3  # tasks 1, 2, 3


def test_drift_against_previous_month(fixture_files):
    res, h = _head(fixture_files)
    assert res.headline.columns[-1] == "drift_apr_to_may"
    assert h.loc["1", "drift_apr_to_may"] == pytest.approx(0.1)
    assert h.loc["2", "drift_apr_to_may"] == pytest.approx(0.0)
    assert res.summary["mean_drift"] == pytest.approx(0.05)


def test_country_and_higher_level_rows_ignored(fixture_files):
    _, h = _head(fixture_files)
    assert h.loc["2", "A"] == 30


def test_occupation_level_split(fixture_files):
    res, _ = _head(fixture_files)
    occ = res.summary["occupation_level"]["claude_ai"]
    assert occ["automation_pct"] == 55.5
    assert occ["automation_share"] == pytest.approx(0.555)
    assert occ["usage_rank"] == 2 and occ["n_ranked_occupations"] == 2
    assert res.summary["occupation_level"]["1p_api"] is None


def test_detail_has_every_source_and_month(fixture_files):
    res, _ = _head(fixture_files)
    assert list(res.detail.columns) == OUTPUT_COLUMNS
    # 5 tasks x 2 sources x 2 months
    assert len(res.detail) == 20


def test_month_selection(fixture_files):
    run = _run(fixture_files, month="2026-04")
    assert run.month == "2026-04-01" and run.compare_month is None
    assert run.results[SOC].summary["mean_drift"] is None
    with pytest.raises(ValueError, match="not in this release"):
        _run(fixture_files, month="2025-01")


def test_without_api(fixture_files):
    files = {k: v for k, v in fixture_files.items() if k != "1p_api"}
    res, h = _head(files)
    assert h["api_share"].isna().all()
    assert res.summary["mean_api_share"] is None


def test_unknown_soc_raises(fixture_files):
    aei = {"claude_ai": fixture_files["claude_ai"]}
    onet = {k: fixture_files[k] for k in ("task_statements.csv", "occupation_data.csv", "task_ratings.csv")}
    with pytest.raises(KeyError):
        run_audit(["11-1111.00"], aei, onet, release="test")


def test_month_helpers():
    assert month_key("2026-05") == MAY
    assert month_key("2026-05-01") == MAY
    assert month_label(MAY) == "may2026"
