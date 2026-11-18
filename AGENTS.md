# AGENTS.md

`aei-audit` joins O\*NET task statements to the Anthropic Economic Index (AEI) task-level release and reports, per task and per occupation, what share of matched Claude conversations were automation rather than augmentation. It runs from public data only and writes CSV, JSON and a Markdown report.

## Stack

- Python 3.11 or newer (`requires-python = ">=3.11"`; CI runs 3.11 and 3.12). Version `0.1.0` (`src/aei_audit/__init__.py`).
- Runtime dependencies: `pandas>=2.2`, `numpy>=1.26`, `requests>=2.31`. Dev: `pytest>=8`, `ruff>=0.6`.
- setuptools build, `src/` layout, console script `aei-audit = aei_audit.cli:main`. MIT.

## Layout

```
src/aei_audit/__init__.py   __version__
src/aei_audit/fetch.py      RELEASES, KNOWN_UNSUPPORTED_RELEASES, downloads with retry, cache, SHA-256 manifest
src/aei_audit/audit.py      load AEI + O*NET, Task-ID join, shares, drift, run_audit()
src/aei_audit/report.py     REPORT.md rendering and the fixed caveat text
src/aei_audit/cli.py        argparse CLI (exit 0 ok, 1 data/runtime error, 2 unknown or unsupported release)
tests/conftest.py           small synthetic AEI and O*NET files with the real column layout
tests/test_audit.py, test_cli_fetch.py   fast tests (25)
tests/test_integration.py   slow regression against the real release (12 tests, deselected by default)
examples/                   a sample report for the security occupations
CONTRIBUTING.md, SECURITY.md, README.md
```

## Commands

| Command | What it does |
|---|---|
| `uv venv && uv pip install -e '.[dev]'` | Install with dev tools (the documented path). `python -m venv` plus `pip install -e '.[dev]'` also works; CI uses pip. |
| `ruff check .` | Lint (rules E, F, W, I, B, UP; line length 120). |
| `ruff format --check .` | Format check. |
| `pytest` | Fast tests on synthetic fixtures, no network. `addopts` is `-m 'not slow'`. |
| `pytest -m slow` | Regression against the real `2026_06_26` release. Downloads roughly 300 MB on first run. Needs network. |
| `aei-audit --soc 15-1212 --out aei-audit-out` | Run an audit. Flags: `--soc` (repeatable), `--release`, `--month`, `--compare-month`, `--no-api`, `--refresh`, `--write-filtered`, `--cache-dir`. |

The cache lives in `~/.cache/aei-audit` (or `$XDG_CACHE_HOME/aei-audit`). Output goes to `aei-audit-out/` (gitignored).

## Invariants (from CONTRIBUTING.md and the code; a PR that breaks one is not merged)

1. **Exact Task-ID joins only.** No fuzzy matching. Pinned by `test_unmatched_task_is_kept_not_zeroed` in `tests/test_audit.py`.
2. **A missing cell is not zero.** Unmatched tasks stay in the output; zero-denominator rows are excluded from means (`test_zero_denominator_excluded_from_means`).
3. **`claude_ai` and `1p_api` are never blended** (`test_api_kept_separate`).
4. **Automation share is A / (A + U)**, importance-weighted mean uses O\*NET Importance (`test_automation_share_is_a_over_a_plus_u`, `test_importance_weighting`).
5. **Framing.** Report text says "conversations matched to X tasks", never "X workers use Claude", and keeps the caveats in `report.py`.
6. **Cite sources.** A new data source needs its URL, version or date, and licence in the report and README.
7. **`HF_TOKEN` goes only to huggingface.co**, never to a redirect host (`test_hf_token_only_sent_to_huggingface`).
8. **Unsupported releases are refused with exit 2** rather than parsed wrongly (`test_unsupported_release_exits_2`).

## CI

`.github/workflows/ci.yml` runs on pushes and pull requests to `main`. One job, `Lint and test (Python 3.11)` and `Lint and test (Python 3.12)`: `pip install -e '.[dev]'`, `ruff check .`, `ruff format --check .`, `pytest`. The slow suite does not run in CI.

## Adding an AEI release

Add a `Release` entry to `RELEASES` in `src/aei_audit/fetch.py` (folder, date, report URL, file names), add its spot values to `tests/test_integration.py`, and if the schema differs, list the key in `KNOWN_UNSUPPORTED_RELEASES` until the loader handles it. Update the "Supported releases" section of `README.md`.

## Gotchas

- Fast tests use only fixtures from `tests/conftest.py`. Add a fixture case for any behavior you change.
- `src/aei_audit/report.py` has a per-file `E501` ignore for the BibTeX author line; do not widen it.
- Do not commit anything from `aei-audit-out/` or the download cache; both hold bulk third-party data (CC BY 4.0 sources).
- The README begins with a `README-META` comment block; leave it in place.

## Never

- Add fuzzy or text-similarity matching, or fill gaps with 0.
- Average the 1P API share into the `claude_ai` figures.
- Reword report output into claims about workers, job loss or forecasts.
- Send `HF_TOKEN` or any credential to a host other than huggingface.co, or commit one.
- Edit `examples/` output by hand; regenerate it from a real run.
- Push to `main`.
