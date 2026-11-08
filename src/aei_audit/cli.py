"""``aei-audit`` command line."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from . import __version__, fetch
from .audit import load_aei, month_label, run_audit
from .report import FRAMING, render

DEFAULT_SOCS = ["15-1212.00", "15-1299.04", "15-1299.05", "15-1251.00"]
SOC_RE = re.compile(r"^\d{2}-\d{4}\.\d{2}$")


def _soc(value: str) -> str:
    v = value.strip()
    if re.fullmatch(r"\d{2}-\d{4}", v):
        v += ".00"
    if not SOC_RE.match(v):
        raise argparse.ArgumentTypeError(f"not an O*NET-SOC code: {value!r} (expected e.g. 15-1212.00)")
    return v


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aei-audit",
        description="Audit O*NET occupations against the Anthropic Economic Index: task-level "
        "automation vs augmentation shares from public data.",
        epilog=FRAMING.replace("**", ""),
    )
    p.add_argument("--soc", action="append", type=_soc, metavar="CODE",
                   help="O*NET-SOC code, repeatable (default: "
                        + ", ".join(DEFAULT_SOCS) + ")")  # fmt: skip
    p.add_argument("--release", default="2026_06_26", help="AEI release key (default: %(default)s)")
    p.add_argument("--month", help="headline month YYYY-MM (default: latest in the release)")
    p.add_argument("--compare-month", help="drift baseline YYYY-MM (default: the month before --month)")
    p.add_argument("--out", type=Path, default=Path("aei-audit-out"), help="output directory (default: %(default)s)")
    p.add_argument(
        "--cache-dir", type=Path, default=None, help=f"download cache (default: {fetch.default_cache_dir()})"
    )
    p.add_argument("--no-api", action="store_true", help="skip the 1P API file (77 MB)")
    p.add_argument("--refresh", action="store_true", help="re-download cached files")
    p.add_argument("--write-filtered", action="store_true",
                   help="also write the filtered global O*NET level-0 AEI rows (large)")  # fmt: skip
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    socs = list(dict.fromkeys(args.soc or DEFAULT_SOCS))

    release = fetch.RELEASES.get(args.release)
    if release is None:
        known = ", ".join(fetch.RELEASES)
        if args.release in fetch.KNOWN_UNSUPPORTED_RELEASES:
            print(f"aei-audit: release {args.release} exists but uses an older schema that is not "
                  f"implemented yet (supported: {known})", file=sys.stderr)  # fmt: skip
        else:
            print(f"aei-audit: unknown release {args.release} (supported: {known})", file=sys.stderr)
        return 2

    cache = args.cache_dir or fetch.default_cache_dir()
    sources = ("claude_ai",) if args.no_api else ("claude_ai", "1p_api")
    try:
        manifest = fetch.fetch_all(release, cache, sources=sources, refresh=args.refresh)
        run = run_audit(
            socs,
            {s: fetch.aei_path(release, cache, s) for s in sources},
            {n: fetch.onet_path(cache, n) for n in fetch.ONET_FILES},
            release=release.key,
            month=args.month,
            compare_month=args.compare_month,
        )
    except (KeyError, ValueError, RuntimeError) as exc:
        print(f"aei-audit: {exc.args[0] if exc.args else exc}", file=sys.stderr)
        return 1

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    label = month_label(run.month)
    files: list[str] = []
    for soc, r in run.results.items():
        for name, df in ((f"audit_{soc}.csv", r.detail), (f"audit_{soc}_{label}_headline.csv", r.headline)):
            df.to_csv(out / name, index=False)
            files.append(name)

    if args.write_filtered:
        name = "aei_filtered_global_onet_level0.csv"
        filt = pd.concat([load_aei(fetch.aei_path(release, cache, s), s) for s in sources], ignore_index=True)
        filt[filt.category_name == "onet"].to_csv(out / name, index=False)
        files.append(name)

    needed = [f"aei/{release.key}/{s}" for s in (*sources, "documentation")]
    needed += [f"onet/{fetch.ONET_VERSION}/{n}" for n in fetch.ONET_FILES]
    # Local cache paths stay out of the published outputs.
    used = {k: {f: v for f, v in manifest[k].items() if f != "path"} for k in needed}
    summary = {
        "meta": {
            "tool": f"aei-audit {__version__}",
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "release": release.folder,
            "report": {"title": release.report_title, "date": release.date, "url": release.report_url},
            "onet_version": fetch.ONET_VERSION,
            "headline": {
                "source": "claude_ai",
                "geo_id": "GLOBAL",
                "category_name": "onet",
                "hierarchy_level": 0,
                "month": run.month,
            },  # fmt: skip
            "compare_month": run.compare_month,
            "months_available": run.months_available,
            "sources": list(run.sources),
            "framing": FRAMING.replace("**", ""),
            "inputs": used,
        },
        "results": {soc: r.summary for soc, r in run.results.items()},
    }
    files += ["summary.json", "REPORT.md"]
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
    (out / "REPORT.md").write_text(render(run, release, used, files))

    for soc, r in run.results.items():
        s = r.summary
        occ = (s["occupation_level"].get("claude_ai") or {}).get("automation_share")
        print(f"{soc} {r.title}: {s['n_matched']}/{s['n_tasks']} tasks matched, task mean "
              f"{s['mean_auto_share']}, imp-weighted {s['importance_weighted_auto_share']}, "
              f"occupation {occ}, API mean {s['mean_api_share']}")  # fmt: skip
    print(f"wrote {len(files)} files to {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
