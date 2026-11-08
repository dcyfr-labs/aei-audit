from __future__ import annotations

import json

import pytest
import requests

from aei_audit import cli, fetch
from tests.conftest import SOC


class FakeResponse:
    def __init__(self, status, body=b"", headers=None):
        self.status_code = status
        self._body = body
        self.headers = {"Content-Length": str(len(body)), **(headers or {})}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)

    def iter_content(self, chunk_size):
        yield self._body

    def close(self):
        pass


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, **kw):
        self.calls.append((url, headers))
        return self.responses.pop(0)


def test_download_retries_429_then_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    session = FakeSession([FakeResponse(429, headers={"Retry-After": "1"}), FakeResponse(200, b"a,b\n1,2\n")])
    dest = fetch.download("https://huggingface.co/x.csv", tmp_path / "x.csv", session=session, log=lambda *a, **k: None)
    assert dest.read_bytes() == b"a,b\n1,2\n"
    assert len(session.calls) == 2


def test_download_does_not_retry_404(tmp_path):
    session = FakeSession([FakeResponse(404)])
    with pytest.raises(RuntimeError):
        fetch.download("https://huggingface.co/x.csv", tmp_path / "x.csv", session=session, log=lambda *a, **k: None)
    assert len(session.calls) == 1
    assert not (tmp_path / "x.csv.part").exists()


def test_hf_token_only_sent_to_huggingface(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    assert fetch._headers("https://huggingface.co/datasets/x")["Authorization"] == "Bearer hf_test"
    assert "Authorization" not in fetch._headers("https://www.onetcenter.org/x.csv")
    assert "Authorization" not in fetch._headers("https://huggingface.co.evil.example/x")


def test_release_urls():
    r = fetch.RELEASES["2026_06_26"]
    assert r.url("claude_ai") == (
        "https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/"
        "release_2026_06_26/data/aei_claude_ai_2026-06-26.csv"
    )


@pytest.mark.parametrize("raw,expected", [("15-1212.00", "15-1212.00"), ("15-1212", "15-1212.00")])
def test_soc_argument(raw, expected):
    assert cli._soc(raw) == expected


def test_soc_argument_rejects_garbage():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["--soc", "hacker"])


def test_unsupported_release_exits_2(capsys):
    assert cli.main(["--release", "2025_09_15"]) == 2
    assert "older schema" in capsys.readouterr().err


def test_cli_end_to_end(fixture_files, tmp_path, monkeypatch):
    manifest = {}
    for key in ("aei/2026_06_26/claude_ai", "aei/2026_06_26/1p_api", "aei/2026_06_26/documentation",
                *(f"onet/{fetch.ONET_VERSION}/{n}" for n in fetch.ONET_FILES)):  # fmt: skip
        manifest[key] = {"url": f"https://example.test/{key}", "path": "/local", "bytes": 1, "sha256": "0" * 64}
    monkeypatch.setattr(fetch, "fetch_all", lambda *a, **k: manifest)
    monkeypatch.setattr(fetch, "aei_path", lambda release, cache, source: fixture_files[source])
    monkeypatch.setattr(fetch, "onet_path", lambda cache, name: fixture_files[name])

    out = tmp_path / "out"
    assert cli.main(["--soc", SOC, "--out", str(out)]) == 0
    names = {p.name for p in out.iterdir()}
    assert names == {f"audit_{SOC}.csv", f"audit_{SOC}_may2026_headline.csv", "summary.json", "REPORT.md"}

    summary = json.loads((out / "summary.json").read_text())
    assert summary["meta"]["headline"]["month"] == "2026-05-01"
    assert all("path" not in e for e in summary["meta"]["inputs"].values())
    assert summary["results"][SOC]["n_matched"] == 4

    report = (out / "REPORT.md").read_text()
    for phrase in ("observed Claude usage shares", "not job-loss probabilities", "not career advice",
                   "conversations matched to", "@online{anthropic2026aeiv6", "O\\*NET 31.0",
                   "Unmatched", "never blended"):  # fmt: skip
        assert phrase in report, phrase
