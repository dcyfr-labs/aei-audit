"""Regression against the real 2026_06_26 release (downloads ~340 MB on first run).

Run with ``pytest -m slow``. Values were verified independently on 2026-11-07, including a
cross-check against the Anthropic Economic Index connector.
"""

from __future__ import annotations

import pytest

from aei_audit import fetch
from aei_audit.audit import run_audit

pytestmark = pytest.mark.slow

SOCS = ["15-1212.00", "15-1299.04", "15-1299.05", "15-1251.00"]

# soc: (tasks, matched, core_matched, core, mean, imp_weighted, auto, aug, drift, api_matched, api_mean)
HEADLINE = {
    "15-1212.00": (11, 3, 3, 11, 0.853, 0.854, 3, 0, 0.043, 3, 0.912),
    "15-1299.04": (22, 5, 5, 22, 0.742, 0.750, 5, 0, -0.012, 9, 0.963),
    "15-1299.05": (20, 10, 10, 20, 0.627, 0.625, 8, 2, 0.003, 11, 0.934),
    "15-1251.00": (17, 11, 9, 13, 0.676, 0.679, 10, 1, 0.006, 9, 0.933),
}

SPOTS = {
    "15-1212.00": {"5317": 0.90, "5321": 0.87, "5315": 0.79},
    "15-1299.04": {"21756": 0.90, "21758": 0.83, "21754": 0.64},
    "15-1299.05": {"21784": 0.90, "21783": 0.42, "21780": 0.47},
    "15-1251.00": {"1281": 0.38},
}

# soc: (occupation-level automation %, usage share %, usage rank, occupations ranked)
OCCUPATION = {
    "15-1212.00": (76.1, 0.01, 374, 718),
    "15-1299.05": (63.75, 0.12, 147, 718),
}


@pytest.fixture(scope="module")
def run():
    release = fetch.RELEASES["2026_06_26"]
    cache = fetch.default_cache_dir()
    fetch.fetch_all(release, cache)
    return run_audit(
        SOCS,
        {s: fetch.aei_path(release, cache, s) for s in ("claude_ai", "1p_api")},
        {n: fetch.onet_path(cache, n) for n in fetch.ONET_FILES},
        release=release.key,
    )


def test_months(run):
    assert run.month == "2026-05-01"
    assert run.compare_month == "2026-04-01"


@pytest.mark.parametrize("soc", SOCS)
def test_headline(run, soc):
    s = run.results[soc].summary
    got = (s["n_tasks"], s["n_matched"], s["n_core_matched"], s["n_core"], s["mean_auto_share"],
           s["importance_weighted_auto_share"], s["n_automation_leaning"], s["n_augmentation_leaning"],
           s["mean_drift"], s["n_api_matched"], s["mean_api_share"])  # fmt: skip
    assert got == pytest.approx(HEADLINE[soc])


@pytest.mark.parametrize("soc", SOCS)
def test_spot_values(run, soc):
    h = run.results[soc].headline.set_index("Task ID").automation_share
    for task_id, value in SPOTS[soc].items():
        assert h[task_id] == pytest.approx(value, abs=0.005), task_id


@pytest.mark.parametrize("soc", list(OCCUPATION))
def test_occupation_level(run, soc):
    occ = run.results[soc].summary["occupation_level"]["claude_ai"]
    assert (occ["automation_pct"], occ["usage_share_pct"], occ["usage_rank"], occ["n_ranked_occupations"]) == (
        pytest.approx(OCCUPATION[soc][0]),
        pytest.approx(OCCUPATION[soc][1]),
        OCCUPATION[soc][2],
        OCCUPATION[soc][3],
    )


def test_api_mean_above_claude_ai_mean(run):
    for soc in SOCS:
        s = run.results[soc].summary
        assert s["mean_api_share"] > s["mean_auto_share"], soc
