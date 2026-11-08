# Contributing to aei-audit

## Code of Conduct

This project follows the DCYFR Labs [Code of Conduct](https://github.com/dcyfr-labs/.github/blob/main/CODE_OF_CONDUCT.md).

## Licensing

By contributing, you agree that your contribution is licensed under the project's MIT License
and that you have the right to submit it under that license.

DCYFR is a trademark of Drew Gowan. Do not use it in a way that implies endorsement without
permission. Questions: [licensing@dcyfr.ai](mailto:licensing@dcyfr.ai).

## Ground rules for changes

These keep the output honest. A pull request that breaks one will not be merged.

1. **Exact Task-ID joins only.** No fuzzy or text-similarity matching. A task without a
   published cell stays in the output as unmatched.
2. **A missing cell is not zero.** Never fill gaps with 0 or drop them from the task count.
3. **Keep `claude_ai` and the 1P API separate.** No blended averages.
4. **Keep the framing.** Report text says "conversations matched to X tasks", never "X workers
   use Claude", and keeps the caveats in `report.py`.
5. **Cite sources.** Any new data source needs its URL, version or date, and licence in the
   report and README.

## Development

```bash
uv venv && uv pip install -e '.[dev]'
```

```bash
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest
```

Fast tests use small synthetic fixtures in `tests/conftest.py`. Add a fixture case for any
behaviour you change. `pytest -m slow` checks published values against the real release and
needs network access the first time.

## Adding a release

Add an entry to `RELEASES` in `src/aei_audit/fetch.py` with the folder, date, report URL and
file names, then add its spot values to `tests/test_integration.py`. If the schema changed,
list the release in `KNOWN_UNSUPPORTED_RELEASES` until the loader handles it.
