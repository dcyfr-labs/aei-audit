"""Markdown report: Sources, Method, Headline table, caveats, per-SOC sections, Files, Citation."""

from __future__ import annotations

from datetime import date

from . import __version__
from .audit import AuditRun, month_label
from .fetch import AEI_DATASET_URL, ONET_DATABASE_URL, ONET_VERSION, Release

FRAMING = (
    "These are **observed Claude usage shares**: of the conversations matched to a task, the share "
    "Anthropic's classifier labelled automation (Claude does the task) rather than augmentation "
    "(Claude helps a person do it). They are not job-loss probabilities, not evidence that AI "
    "performs a task well on its own, and not career advice."
)

CAVEATS = [
    FRAMING,
    'Counts are of *conversations matched to tasks*, not of workers. "Conversations matched to '
    'penetration-testing tasks" is accurate; "penetration testers use Claude" is not.',
    "A task with no published cell is **unmatched**, not zero. AEI suppresses cells below its "
    "aggregation thresholds, so low coverage means little observed usage or suppression, and the "
    "data cannot tell the two apart.",
    "Headline numbers are `claude_ai` (Claude chat and Cowork). The 1P API is shown separately and "
    "never blended: API traffic is mostly programmatic pipelines and reads as automation on almost "
    "every task.",
    "The occupation-level split is computed by Anthropic on all classified conversations for the "
    "occupation. The task mean is computed here over the published task rows only. They measure "
    "different things and are reported side by side.",
    "Month-over-month drift covers two monthly snapshots; treat small moves as noise.",
]

CITATION = """@online{anthropic2026aeiv6,
  author = {Maxim Massenkoff and Eva Lyubich and Szymon Sacher and Zoe Hitzig and Shaoyi Zhang and Ryan Heller and Peter McCrory},
  title = {Anthropic Economic Index report: Cadences},
  date = {2026-06-26},
  year = {2026},
  url = {https://www.anthropic.com/research/economic-index-june-2026-report}
}"""

ONET_ATTRIBUTION = (
    "This report includes information from the O\\*NET {v} Database by the U.S. Department of "
    "Labor, Employment and Training Administration (USDOL/ETA). Used under the CC BY 4.0 license. "
    "O\\*NET® is a trademark of USDOL/ETA. The authors have modified all or some of this "
    "information. USDOL/ETA has not approved, endorsed, or tested these modifications."
)


def _pct(x, nd: int = 1) -> str:
    return "n/a" if x is None else f"{x * 100:.{nd}f}%"


def _signed(x) -> str:
    return "n/a" if x is None else f"{x * 100:+.1f} pts"


def _md(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _imp(x) -> str:
    return "n/a" if x is None else f"{x:.2f}"


def render(run: AuditRun, release: Release, manifest: dict, files: list[str]) -> str:
    mon = date.fromisoformat(run.month).strftime("%B %Y")
    cmp_ = date.fromisoformat(run.compare_month).strftime("%B %Y") if run.compare_month else None
    out: list[str] = []
    w = out.append

    w(f"# AEI task audit: {', '.join(r.title for r in run.results.values())}")
    w("")
    w(f"Generated {date.today().isoformat()} by `aei-audit` {__version__} from public data only. "
      f"Headline month: **{mon}** (`claude_ai`, global).")  # fmt: skip
    w("")
    w(f"> {FRAMING}")
    w("")

    w("## Sources")
    w("")
    w(f"- **Anthropic Economic Index**, release `{release.folder}` ({release.date}), report "
      f"[*{release.report_title.split(': ')[-1]}*]({release.report_url}). Dataset: {AEI_DATASET_URL} "
      f"(CC BY 4.0). Months in this release: {', '.join(m[:7] for m in run.months_available)}.")  # fmt: skip
    w(f"- **O\\*NET {ONET_VERSION} Database**, {ONET_DATABASE_URL}: task statements, task ratings "
      "(Importance, Frequency) and occupation titles.")  # fmt: skip
    w("")
    w("| File | Bytes | SHA-256 |")
    w("|---|---:|---|")
    for key in sorted(manifest):
        e = manifest[key]
        w(f"| [{key}]({e['url']}) | {e['bytes']:,} | `{e['sha256'][:16]}…` |")
    w("")

    w("## Method")
    w("")
    w("1. Every official O\\*NET task statement for each occupation is joined to AEI rows with "
      "`geo_id=GLOBAL`, `category_name=onet`, `hierarchy_level=0` by **Task ID** only. No fuzzy "
      "matching; tasks without a published cell are listed as unmatched.")  # fmt: skip
    w("2. Automation share per task = A / (A + U), where A and U are "
      "`collaboration_bucket_automation_pct` and `collaboration_bucket_augmentation_pct`. Tasks "
      "with A + U = 0 are excluded from means.")  # fmt: skip
    w("3. **Importance-weighted share** weights each matched task by its O\\*NET Importance (1–5), "
      "so a high share on a rarely important task does not dominate.")  # fmt: skip
    if cmp_:
        w(f"4. **Drift** = {mon} share minus {cmp_} share for the same task (`claude_ai`).")
    w("5. The **occupation-level split** comes from the `soc_occupation` rows for the same month; "
      "usage rank is by `pct` among all occupations published that month.")  # fmt: skip
    w("6. `low_count_flag` marks rows whose A + U falls short of ~100, a sign one bucket was "
      "suppressed.")  # fmt: skip
    w("")

    w(f"## Headline ({mon}, claude_ai)")
    w("")
    w("| SOC | Occupation | O\\*NET tasks | Matched (Core) | Task mean A/(A+U) | Imp-weighted | "
      "Occupation-level | Auto/Aug | Drift | API matched | API mean |")  # fmt: skip
    w("|---|---|---:|---|---:|---:|---:|---|---:|---:|---:|")
    for soc, r in run.results.items():
        s = r.summary
        occ = (s["occupation_level"].get("claude_ai") or {}).get("automation_share")
        w(f"| {soc} | {_md(r.title)} | {s['n_tasks']} | {s['n_matched']} ({s['n_core_matched']}/{s['n_core']}) "
          f"| {_pct(s['mean_auto_share'])} | {_pct(s['importance_weighted_auto_share'])} | {_pct(occ)} "
          f"| {s['n_automation_leaning']}/{s['n_augmentation_leaning']} | {_signed(s['mean_drift'])} "
          f"| {s['n_api_matched']} | {_pct(s['mean_api_share'])} |")  # fmt: skip
    w("")
    w("*Matched (Core)*: tasks with a published cell, and matched Core tasks over all Core tasks. "
      "*Auto/Aug*: matched tasks leaning automation vs augmentation. *API*: `1p_api`, same month, "
      "never blended into the other columns.")  # fmt: skip
    w("")

    w("## What the numbers do and do not say")
    w("")
    for c in CAVEATS:
        w(f"- {c}")
    w("")

    for soc, r in run.results.items():
        s = r.summary
        w(f"## {soc} {r.title}")
        w("")
        w(f"**Coverage:** {s['n_matched']} of {s['n_tasks']} O\\*NET tasks have a published "
          f"`claude_ai` cell for {mon} ({s['n_core_matched']} of {s['n_core']} Core tasks).")  # fmt: skip
        occ = s["occupation_level"].get("claude_ai")
        if occ:
            w("")
            w(f"**Occupation level:** {_pct(occ['automation_share'])} automation across all "
              f"conversations matched to this occupation, next to the {_pct(s['mean_auto_share'])} "
              f"mean over its {s['n_matched']} published task rows. Usage share "
              f"{occ['usage_share_pct']}% of `claude_ai` conversations, rank "
              f"{occ['usage_rank']} of {occ['n_ranked_occupations']} occupations.")  # fmt: skip
        api_occ = s["occupation_level"].get("1p_api")
        if api_occ and api_occ.get("automation_share") is not None:
            w("")
            api_line = (
                f"**1P API** (separate, not blended): {s['n_api_matched']} tasks matched, mean "
                f"{_pct(s['mean_api_share'])}; occupation level {_pct(api_occ['automation_share'])} automation."
            )
            w(api_line)
        w("")
        shown = {rec["Task ID"] for rec in s["top_automation"]}
        lowest = [rec for rec in s["top_augmentation"] if rec["Task ID"] not in shown]
        for heading, rows in (("Highest automation share", s["top_automation"]),
                              ("Lowest automation share", lowest)):  # fmt: skip
            if not rows:
                continue
            w(f"**{heading}** (matched tasks, `claude_ai`)")
            w("")
            w("| Task ID | Task | A/(A+U) | Importance |")
            w("|---|---|---:|---:|")
            for rec in rows:
                w(f"| {rec['Task ID']} | {_md(rec['Task'])} | {_pct(rec['automation_share'], 0)} "
                  f"| {_imp(rec['importance'])} |")  # fmt: skip
            w("")
        if s["unmatched"]:
            w(f"**Unmatched** ({len(s['unmatched'])} tasks, no published cell; not zero), by Importance")
            w("")
            w("| Task ID | Task | Type | Importance |")
            w("|---|---|---|---:|")
            for rec in s["unmatched"]:
                w(f"| {rec['Task ID']} | {_md(rec['Task'])} | {rec['Task Type']} | {_imp(rec['importance'])} |")
            w("")

    w("## Files")
    w("")
    for f in files:
        w(f"- `{f}`")
    w("")
    w("## Citation and licences")
    w("")
    w("AEI data © Anthropic, CC BY 4.0. Cite as:")
    w("")
    w("```bibtex")
    w(CITATION)
    w("```")
    w("")
    w(ONET_ATTRIBUTION.format(v=ONET_VERSION))
    w("")
    w(f"Interactive alternative: the Anthropic Economic Index explorer at "
      f"https://www.anthropic.com/economic-index. Headline file label: `{month_label(run.month)}`.")  # fmt: skip
    w("")
    return "\n".join(out)
