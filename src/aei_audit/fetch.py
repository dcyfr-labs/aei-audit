"""Download and cache the public source files: AEI release CSVs (Hugging Face) and O*NET CSVs.

Plain ``requests`` against direct ``resolve/main`` URLs, no ``huggingface_hub``: anonymous HF API
calls are rate-limited, so every download retries with exponential backoff and honours
``Retry-After``. Set ``HF_TOKEN`` to send a bearer token to huggingface.co (never to other hosts).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

AEI_DATASET_URL = "https://huggingface.co/datasets/Anthropic/EconomicIndex"
AEI_RESOLVE_BASE = f"{AEI_DATASET_URL}/resolve/main"


@dataclass(frozen=True)
class Release:
    """One AEI release whose schema this tool implements."""

    key: str  # e.g. "2026_06_26"
    date: str  # e.g. "2026-06-26"
    report_title: str
    report_url: str
    files: dict[str, str]  # source -> path inside the release folder

    @property
    def folder(self) -> str:
        return f"release_{self.key}"

    def url(self, source: str) -> str:
        return f"{AEI_RESOLVE_BASE}/{self.folder}/{self.files[source]}"


RELEASES: dict[str, Release] = {
    "2026_06_26": Release(
        key="2026_06_26",
        date="2026-06-26",
        report_title="Anthropic Economic Index report: Cadences",
        report_url="https://www.anthropic.com/research/economic-index-june-2026-report",
        files={
            "claude_ai": "data/aei_claude_ai_2026-06-26.csv",
            "1p_api": "data/aei_1p_api_2026-06-26.csv",
            "documentation": "data_documentation.md",
        },
    ),
}

# Earlier releases exist on Hugging Face but use different file names and columns. They are
# listed so the CLI can say so plainly instead of failing on a missing file.
KNOWN_UNSUPPORTED_RELEASES = (
    "2026_03_24",
    "2026_01_15",
    "2025_09_15",
    "2025_03_27",
    "2025_02_10",
)

ONET_VERSION = "31.0"
ONET_DATABASE_URL = "https://www.onetcenter.org/database.html"
ONET_CSV_BASE = "https://www.onetcenter.org/dl_files/database/db_31_0_csv/"
ONET_FILES = ("task_statements.csv", "occupation_data.csv", "task_ratings.csv")

USER_AGENT = "aei-audit (+https://github.com/dcyfr-labs/aei-audit)"
RETRY_STATUS = {429, 500, 502, 503, 504}


def default_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "aei-audit"


def _headers(url: str) -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT}
    token = os.environ.get("HF_TOKEN")
    host = urlparse(url).hostname or ""
    if token and (host == "huggingface.co" or host.endswith(".huggingface.co")):
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _sleep_for(attempt: int, response: requests.Response | None, base: float) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After", "")
        if retry_after.isdigit():
            return min(float(retry_after), 300.0)
    return base * (2**attempt)


def download(
    url: str,
    dest: Path,
    *,
    retries: int = 6,
    backoff: float = 2.0,
    session: requests.Session | None = None,
    log=print,
) -> Path:
    """Stream ``url`` to ``dest`` atomically, retrying 429/5xx and connection errors."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    http = session or requests.Session()
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        response = None
        try:
            # The bearer header is built per request and requests drops Authorization on a
            # cross-host redirect, so HF_TOKEN never reaches the LFS/CDN host.
            response = http.get(url, headers=_headers(url), stream=True, timeout=(15, 120))
            if response.status_code in RETRY_STATUS:
                raise requests.HTTPError(f"HTTP {response.status_code}", response=response)
            response.raise_for_status()
            with open(part, "wb") as fh:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    fh.write(chunk)
            expected = response.headers.get("Content-Length")
            if expected and "gzip" not in response.headers.get("Content-Encoding", ""):
                if part.stat().st_size != int(expected):
                    raise OSError(f"truncated download: {part.stat().st_size} of {expected} bytes")
            part.replace(dest)
            return dest
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError, OSError) as exc:
            last_error = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status is not None and status not in RETRY_STATUS:
                break
            if attempt == retries:
                break
            wait = _sleep_for(attempt, response, backoff)
            log(f"  retry {attempt + 1}/{retries} for {url} in {wait:.0f}s ({exc})", file=sys.stderr)
            time.sleep(wait)
        finally:
            if response is not None:
                response.close()
    part.unlink(missing_ok=True)
    raise RuntimeError(f"download failed: {url}: {last_error}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _record(manifest: dict, key: str, url: str, path: Path) -> None:
    entry = manifest.get(key)
    stat = path.stat()
    if entry and entry.get("bytes") == stat.st_size and entry.get("url") == url:
        return
    manifest[key] = {
        "url": url,
        "path": str(path),
        "bytes": stat.st_size,
        "sha256": sha256(path),
        "fetched_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(timespec="seconds"),
    }


def fetch_all(
    release: Release,
    cache_dir: Path,
    *,
    sources: tuple[str, ...] = ("claude_ai", "1p_api"),
    refresh: bool = False,
    log=print,
) -> dict:
    """Ensure every needed file is cached. Returns the provenance manifest (url, bytes, sha256)."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cache_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    wanted: list[tuple[str, str, Path]] = []
    for source in (*sources, "documentation"):
        rel_path = release.files[source]
        wanted.append(
            (f"aei/{release.key}/{source}", release.url(source), cache_dir / "aei" / release.folder / rel_path)
        )
    for name in ONET_FILES:
        wanted.append((f"onet/{ONET_VERSION}/{name}", ONET_CSV_BASE + name, cache_dir / "onet" / ONET_VERSION / name))

    for key, url, path in wanted:
        if refresh or not path.exists():
            log(f"downloading {url}", file=sys.stderr)
            download(url, path, log=log)
        _record(manifest, key, url, path)

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def aei_path(release: Release, cache_dir: Path, source: str) -> Path:
    return cache_dir / "aei" / release.folder / release.files[source]


def onet_path(cache_dir: Path, name: str) -> Path:
    return cache_dir / "onet" / ONET_VERSION / name
