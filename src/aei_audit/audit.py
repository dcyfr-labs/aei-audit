"""Join O*NET task statements to AEI task-level cells and compute automation shares.

Rules this module holds to:

* Join on O*NET Task ID only. A task with no AEI cell is kept and reported as unmatched; it is
  never dropped, fuzzy-matched or treated as zero (AEI suppresses cells below its thresholds).
* ``claude_ai`` and ``1p_api`` are computed separately and never blended.
* The occupation-level split (``category_name=soc_occupation``) is reported next to, not instead
  of, the mean over published task rows: AEI computes it on all classified conversations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

SOURCES = ("claude_ai", "1p_api")

TASK_METRICS = {
    "collaboration_bucket_automation_pct": "A",
    "collaboration_bucket_augmentation_pct": "U",
    "pct": "usage_share_pct",
    "ai_autonomy_mean": "ai_autonomy_mean",
    "human_only_time_mean": "human_only_time_mean",
    "human_with_ai_time_mean": "human_with_ai_time_mean",
    "use_case_work_pct": "use_case_work_pct",
}

OUTPUT_COLUMNS = [
    "O*NET-SOC Code", "Title", "Task ID", "Task", "Task Type", "importance", "freq_cat_mean",
    "source", "month", "matched", "usage_share_pct", "A", "U", "automation_share", "lean",
    "low_count_flag", "ai_autonomy_mean", "human_only_time_mean", "human_with_ai_time_mean",
    "use_case_work_pct",
]  # fmt: skip

TOP_N = 5


# --------------------------------------------------------------------------- loading


def load_aei(path: Path, source: str) -> pd.DataFrame:
    """Global rows only: O*NET tasks (level 0) and SOC occupations (level 0)."""
    df = pd.read_csv(
        path,
        dtype={"node_external_id": str, "date_start": str, "geo_id": str, "category_name": str},
        usecols=["date_start", "geo_id", "category_name", "hierarchy_level", "metric_id", "value",
                 "node_name", "node_external_id"],
    )  # fmt: skip
    keep = (df.geo_id == "GLOBAL") & (df.hierarchy_level == 0) & df.category_name.isin(["onet", "soc_occupation"])
    df = df.loc[keep].copy()
    df["source"] = source
    return df


def task_pivot(aei: pd.DataFrame) -> pd.DataFrame:
    """One row per (source, month, Task ID) with the task metrics as columns."""
    rows = aei[(aei.category_name == "onet") & aei.metric_id.isin(list(TASK_METRICS))]
    piv = rows.pivot_table(
        index=["source", "date_start", "node_external_id"], columns="metric_id", values="value"
    ).reset_index()
    piv = piv.rename(columns=TASK_METRICS)
    for col in TASK_METRICS.values():
        if col not in piv.columns:
            piv[col] = np.nan
    piv["node_external_id"] = piv.node_external_id.astype(str)
    piv.columns.name = None
    return piv


def load_onet(task_statements: Path, occupation_data: Path, task_ratings: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Task statements with Importance (IM) and expected frequency category (FT) attached."""
    ts = pd.read_csv(task_statements, dtype={"Task ID": str})
    occ = pd.read_csv(occupation_data)
    tr = pd.read_csv(task_ratings, dtype={"Task ID": str})
    tr["Category"] = pd.to_numeric(tr["Category"], errors="coerce")
    tr["Data Value"] = pd.to_numeric(tr["Data Value"], errors="coerce")

    imp = (
        tr[tr["Scale ID"] == "IM"][["Task ID", "Data Value"]]
        .rename(columns={"Data Value": "importance"})
        .drop_duplicates("Task ID")
    )
    freq = tr[tr["Scale ID"] == "FT"]
    # Expected frequency category: 1 = yearly or less ... 7 = hourly or more.
    freq_mean = (
        freq.assign(w=freq["Category"] * freq["Data Value"] / 100)
        .groupby("Task ID")
        .w.sum()
        .rename("freq_cat_mean")
        .reset_index()
    )
    ts = ts.merge(imp, on="Task ID", how="left").merge(freq_mean, on="Task ID", how="left")
    if not ts["Task ID"].is_unique:
        raise ValueError("O*NET Task IDs are not unique after joining ratings")
    return ts, occ


# --------------------------------------------------------------------------- computation


def month_key(month: str) -> str:
    """'2026-05' or '2026-05-01' -> '2026-05-01'."""
    parts = month.strip().split("-")
    if len(parts) < 2:
        raise ValueError(f"month must look like YYYY-MM, got {month!r}")
    return date(int(parts[0]), int(parts[1]), 1).isoformat()


def month_label(month: str) -> str:
    """'2026-05-01' -> 'may2026'."""
    return date.fromisoformat(month).strftime("%b%Y").lower()


def short_month(month: str) -> str:
    """'2026-04-01' -> 'apr'."""
    return date.fromisoformat(month).strftime("%b").lower()


def add_shares(m: pd.DataFrame) -> pd.DataFrame:
    """automation_share = A / (A + U); NaN when unmatched or when A + U is zero."""
    m = m.copy()
    m["matched"] = m.A.notna() | m.U.notna()
    denom = m.A.fillna(0) + m.U.fillna(0)
    with np.errstate(invalid="ignore", divide="ignore"):
        m["automation_share"] = np.where(denom > 0, m.A.fillna(0) / denom.where(denom > 0), np.nan)
    m["lean"] = np.select(
        [m.automation_share > 0.5, m.automation_share < 0.5, m.automation_share == 0.5, m.matched],
        ["automation", "augmentation", "tie", "no_split"],
        default="unmatched",
    )
    # Published buckets sum to ~100; a partial sum means one bucket was suppressed.
    m["low_count_flag"] = denom.between(0.01, 95)
    return m


def occupation_split(aei: pd.DataFrame, soc: str, source: str, month: str) -> dict | None:
    """Occupation-level A/U and usage share from the soc_occupation rows, with usage rank."""
    occ = aei[(aei.category_name == "soc_occupation") & (aei.source == source) & (aei.date_start == month)]
    if occ.empty:
        return None
    wide = occ.pivot_table(index="node_external_id", columns="metric_id", values="value")
    if soc not in wide.index:
        return None
    row = wide.loc[soc]
    a = row.get("collaboration_bucket_automation_pct", np.nan)
    u = row.get("collaboration_bucket_augmentation_pct", np.nan)
    pct = row.get("pct", np.nan)
    ranked = wide["pct"].dropna().rank(ascending=False, method="min") if "pct" in wide else pd.Series(dtype=float)
    share = a / (a + u) if pd.notna(a) and pd.notna(u) and (a + u) > 0 else None
    return {
        "source": source,
        "month": month,
        "automation_pct": _num(a),
        "augmentation_pct": _num(u),
        "automation_share": round(float(share), 4) if share is not None else None,
        "usage_share_pct": _num(pct),
        "usage_rank": int(ranked[soc]) if soc in ranked.index else None,
        "n_ranked_occupations": int(ranked.size),
    }


def _num(x) -> float | None:
    return None if x is None or pd.isna(x) else float(x)


def _round(x, nd: int = 3) -> float | None:
    return None if x is None or pd.isna(x) else round(float(x), nd)


def _records(df: pd.DataFrame, cols: list[str]) -> list[dict]:
    out = df[cols].to_dict("records")
    for rec in out:
        for k, v in rec.items():
            if isinstance(v, float) and np.isnan(v):
                rec[k] = None
            elif isinstance(v, np.generic):
                rec[k] = v.item()
    return out


@dataclass
class SocResult:
    soc: str
    title: str
    detail: pd.DataFrame  # every task x source x month
    headline: pd.DataFrame  # claude_ai, selected month, with compare/API columns
    summary: dict = field(default_factory=dict)


def audit_soc(
    soc: str,
    tasks: pd.DataFrame,
    occupations: pd.DataFrame,
    piv: pd.DataFrame,
    aei: pd.DataFrame,
    *,
    month: str,
    compare_month: str | None,
    sources: tuple[str, ...] = SOURCES,
) -> SocResult:
    t = tasks[tasks["O*NET-SOC Code"] == soc].copy()
    titles = occupations.loc[occupations["O*NET-SOC Code"] == soc, "Title"]
    if titles.empty:
        raise KeyError(f"{soc} is not an O*NET-SOC code in this O*NET version")
    title = str(titles.iloc[0])

    months = sorted(piv.date_start.unique())
    frames = []
    for src in sources:
        for mo in months:
            p = piv[(piv.source == src) & (piv.date_start == mo)]
            mm = t.merge(p.drop(columns=["source", "date_start"]), left_on="Task ID",
                         right_on="node_external_id", how="left")  # fmt: skip
            mm["source"] = src
            mm["month"] = mo
            frames.append(mm)
    detail = add_shares(pd.concat(frames, ignore_index=True))
    detail = detail[OUTPUT_COLUMNS].sort_values(["source", "month", "automation_share"], ascending=[True, True, False])

    def share_by_task(src: str, mo: str | None) -> pd.Series:
        if mo is None or src not in sources:
            return pd.Series(dtype=float)
        sel = detail[(detail.source == src) & (detail.month == mo)]
        return sel.set_index("Task ID").automation_share

    head = detail[(detail.source == "claude_ai") & (detail.month == month)].copy()
    prev_col = f"{short_month(compare_month)}_share" if compare_month else "compare_share"
    drift_col = f"drift_{short_month(compare_month)}_to_{short_month(month)}" if compare_month else "drift"
    head[prev_col] = head["Task ID"].map(share_by_task("claude_ai", compare_month))
    head["api_share"] = head["Task ID"].map(share_by_task("1p_api", month))
    head[drift_col] = head.automation_share - head[prev_col]

    matched = head[head.matched]
    w = matched.dropna(subset=["automation_share", "importance"])
    rec_cols = ["Task ID", "Task", "automation_share", "importance"]
    summary = {
        "title": title,
        "n_tasks": len(head),
        "n_matched": int(head.matched.sum()),
        "n_core": int((head["Task Type"] == "Core").sum()),
        "n_core_matched": int(((head["Task Type"] == "Core") & head.matched).sum()),
        "mean_auto_share": _round(matched.automation_share.mean()) if len(matched) else None,
        "importance_weighted_auto_share": (
            _round((w.automation_share * w.importance).sum() / w.importance.sum()) if len(w) else None
        ),
        "n_automation_leaning": int((matched.lean == "automation").sum()),
        "n_augmentation_leaning": int((matched.lean == "augmentation").sum()),
        "mean_drift": _round(head[drift_col].mean()) if head[drift_col].notna().any() else None,
        "n_api_matched": int(head.api_share.notna().sum()),
        "mean_api_share": _round(head.api_share.mean()) if head.api_share.notna().any() else None,
        "occupation_level": {src: occupation_split(aei, soc, src, month) for src in sources},
        "top_automation": _records(matched.nlargest(TOP_N, "automation_share"), rec_cols),
        "top_augmentation": _records(matched.nsmallest(TOP_N, "automation_share"), rec_cols),
        "unmatched": _records(
            head[~head.matched].sort_values("importance", ascending=False),
            ["Task ID", "Task", "Task Type", "importance"],
        ),
    }
    return SocResult(soc=soc, title=title, detail=detail, headline=head, summary=summary)


@dataclass
class AuditRun:
    release: str
    month: str
    compare_month: str | None
    sources: tuple[str, ...]
    months_available: list[str]
    results: dict[str, SocResult]


def run_audit(
    socs: list[str],
    aei_files: dict[str, Path],
    onet_files: dict[str, Path],
    *,
    release: str,
    month: str | None = None,
    compare_month: str | None = None,
) -> AuditRun:
    """Load sources, pick months, and audit each SOC code. ``aei_files`` maps source -> CSV path."""
    if "claude_ai" not in aei_files:
        raise ValueError("claude_ai is required: headline numbers are claude_ai only")
    sources = tuple(s for s in SOURCES if s in aei_files)
    aei = pd.concat([load_aei(aei_files[s], s) for s in sources], ignore_index=True)
    piv = task_pivot(aei)
    tasks, occupations = load_onet(
        onet_files["task_statements.csv"], onet_files["occupation_data.csv"], onet_files["task_ratings.csv"]
    )

    months = sorted(piv[piv.source == "claude_ai"].date_start.unique())
    if not months:
        raise ValueError("no claude_ai task rows found in this release")
    sel = month_key(month) if month else months[-1]
    if sel not in months:
        raise ValueError(f"month {sel[:7]} is not in this release (available: {', '.join(m[:7] for m in months)})")
    if compare_month:
        cmp_ = month_key(compare_month)
        if cmp_ not in months:
            raise ValueError(f"compare month {cmp_[:7]} is not in this release")
    else:
        earlier = [m for m in months if m < sel]
        cmp_ = earlier[-1] if earlier else None

    results = {
        soc: audit_soc(soc, tasks, occupations, piv, aei, month=sel, compare_month=cmp_, sources=sources)
        for soc in socs
    }
    return AuditRun(release=release, month=sel, compare_month=cmp_, sources=sources,
                    months_available=list(months), results=results)  # fmt: skip
