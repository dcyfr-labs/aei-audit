# Security Policy

## Reporting a vulnerability

Email hello@dcyfr.ai with a description, steps to reproduce, and the impact you see. Please do
not open a public GitHub issue for a security report.

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |

## What the tool does on your machine

- Downloads fixed URLs from `huggingface.co` and `www.onetcenter.org` over HTTPS, and nothing
  else.
- Writes only to its cache directory (`~/.cache/aei-audit` by default) and the `--out`
  directory.
- Reads `HF_TOKEN` from the environment if set and sends it only to `huggingface.co`. It never
  logs or writes the token.
- Records the size and SHA-256 of every downloaded file in `manifest.json` and in each run's
  `summary.json`, so a run can be checked against the files it used.
