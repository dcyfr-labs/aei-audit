<!-- README-META
  tlp_clearance: GREEN
  status: active
  name: aei-audit
  description: Task-level audit of Anthropic Economic Index automation shares against O*NET task statements
  last_validated: 2026-11-07
-->

# aei-audit

`aei-audit` joins every O\*NET task statement for the occupations you name to the
[Anthropic Economic Index](https://www.anthropic.com/economic-index) (AEI) task-level release
and reports, per task, what share of matched Claude conversations were automation rather than
augmentation. It uses public data only and caches the downloads locally.

For each occupation it reports:

- A / (A + U) per task, where A and U are AEI's automation and augmentation buckets
- an importance-weighted mean, using O\*NET task Importance
- month-over-month drift between the two monthly snapshots in the release
- the 1P API share, shown next to the `claude_ai` figures and never blended into them
- Anthropic's own occupation-level split and usage rank, for comparison
- every task with no published cell, listed as unmatched (never dropped, never zero)

## Read this first

These are **observed Claude usage shares**. They are not job-loss probabilities, not proof that
AI performs a task well on its own, and not career advice.

- The counts are of **conversations matched to tasks**, not of workers. "Conversations matched
  to penetration-testing tasks" is accurate. "Penetration testers use Claude" is not.
- A task with no published cell is unmatched. AEI suppresses cells below its aggregation
  thresholds, so a gap means little observed usage or suppression, and the data cannot tell
  which.
- Task IDs are matched exactly. There is no fuzzy matching of task text.
- `claude_ai` (Claude chat and Cowork) and the 1P API are different populations. API traffic is
  mostly programmatic and reads as automation on almost every task, so the two are reported
  side by side and never averaged together.
- Two monthly snapshots make a short series. Treat small drift as noise.

## Quick start

Python 3.11 or newer.

```bash
pipx install git+https://github.com/dcyfr-labs/aei-audit
```

```bash
aei-audit --soc 15-1212 --soc 15-1299.05 --out aei-audit-out
```

The first run downloads about 300 MB (AEI `claude_ai` and 1P API files, plus three O\*NET CSVs)
into `~/.cache/aei-audit` (or `$XDG_CACHE_HOME/aei-audit`). Later runs read the cache and take a
couple of seconds. With no `--soc`, it audits four security and programming occupations as a
demo.

| Option | Meaning |
|---|---|
| `--soc CODE` | O\*NET-SOC code, repeatable. `15-1212` is read as `15-1212.00`. |
| `--release KEY` | AEI release folder. Default `2026_06_26`. |
| `--month YYYY-MM` | Headline month. Default: the latest in the release. |
| `--compare-month YYYY-MM` | Drift baseline. Default: the month before the headline month. |
| `--no-api` | Skip the 1P API file (saves about 77 MB). |
| `--refresh` | Download again even if cached. |
| `--write-filtered` | Also write the global level-0 AEI task rows used for the join. |
| `--cache-dir PATH` | Cache location. |

Set `HF_TOKEN` if Hugging Face rate-limits you. It is sent only to `huggingface.co`.

### Output

| File | Contents |
|---|---|
| `audit_<soc>.csv` | Every task, every source, every month, long format |
| `audit_<soc>_<month>_headline.csv` | One row per task for the headline month, with the comparison month, API share and drift |
| `summary.json` | Headline numbers per occupation, input URLs, sizes and SHA-256 hashes |
| `REPORT.md` | Sources, method, headline table, caveats, per-occupation sections, citations |

A full example is in [examples/security-occupations-2026-06-26.md](examples/security-occupations-2026-06-26.md).

## No-code alternative

Anthropic publishes an interactive explorer for the same data at
<https://www.anthropic.com/economic-index>, and an Economic Index connector for Claude. Use those
if you want to browse occupations and tasks without running anything. This tool exists for
reproducible, file-based output with every unmatched task listed.

## What this is not

- Not a forecast of employment, wages or exposure.
- Not a measure of output quality. A conversation labelled automation tells you how the person
  used Claude, not whether the result was good.
- Not a survey of workers. AEI samples conversations, and an occupation's tasks are matched by a
  classifier.
- Not a substitute for the AEI reports, which describe the method, sampling and thresholds in
  full.

## Supported releases

`2026_06_26` (v6, monthly snapshots for April and May 2026). Earlier releases use a different
schema and are refused with an explicit message rather than parsed wrongly.

## Development

```bash
uv venv && uv pip install -e '.[dev]'
```

```bash
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest
```

`pytest -m slow` runs the regression suite against the real release (downloads the data on first
run).

## Sources and citation

**Anthropic Economic Index**, release `2026_06_26`, published 2026-06-26.
Dataset: <https://huggingface.co/datasets/Anthropic/EconomicIndex>.
Report: <https://www.anthropic.com/research/economic-index-june-2026-report>.
Licensed CC BY 4.0.

```bibtex
@online{anthropic2026aeiv6,
  author = {Maxim Massenkoff and Eva Lyubich and Szymon Sacher and Zoe Hitzig and Shaoyi Zhang and Ryan Heller and Peter McCrory},
  title = {Anthropic Economic Index report: Cadences},
  date = {2026-06-26},
  year = {2026},
  url = {https://www.anthropic.com/research/economic-index-june-2026-report}
}
```

**O\*NET 31.0 Database**, <https://www.onetcenter.org/database.html>.

This tool uses information from the O\*NET 31.0 Database by the U.S. Department of Labor,
Employment and Training Administration (USDOL/ETA). Used under the CC BY 4.0 license. O\*NET® is
a trademark of USDOL/ETA. The authors have modified all or some of this information. USDOL/ETA
has not approved, endorsed, or tested these modifications.

This project is not affiliated with or endorsed by Anthropic.

## License

Code: [MIT](LICENSE). The data it downloads keeps its own licences (CC BY 4.0 for both sources).

## About DCYFR

`aei-audit` is maintained by **DCYFR Labs**. **DCYFR** is a trademark of Drew Gowan.
<https://www.dcyfr.ai>
