# AEI task audit: Information Security Analysts, Penetration Testers, Information Security Engineers, Computer Programmers

Generated 2026-11-07 by `aei-audit` 0.1.0 from public data only. Headline month: **May 2026** (`claude_ai`, global).

> These are **observed Claude usage shares**: of the conversations matched to a task, the share Anthropic's classifier labelled automation (Claude does the task) rather than augmentation (Claude helps a person do it). They are not job-loss probabilities, not evidence that AI performs a task well on its own, and not career advice.

## Sources

- **Anthropic Economic Index**, release `release_2026_06_26` (2026-06-26), report [*Cadences*](https://www.anthropic.com/research/economic-index-june-2026-report). Dataset: https://huggingface.co/datasets/Anthropic/EconomicIndex (CC BY 4.0). Months in this release: 2026-04, 2026-05.
- **O\*NET 31.0 Database**, https://www.onetcenter.org/database.html: task statements, task ratings (Importance, Frequency) and occupation titles.

| File | Bytes | SHA-256 |
|---|---:|---|
| [aei/2026_06_26/1p_api](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2026_06_26/data/aei_1p_api_2026-06-26.csv) | 77,282,477 | `62197f003e001945…` |
| [aei/2026_06_26/claude_ai](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv) | 219,174,671 | `f974b358bce0e5a8…` |
| [aei/2026_06_26/documentation](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2026_06_26/data_documentation.md) | 7,397 | `1a01eeb7d34250b1…` |
| [onet/31.0/occupation_data.csv](https://www.onetcenter.org/dl_files/database/db_31_0_csv/occupation_data.csv) | 268,030 | `a09eae1d6609686e…` |
| [onet/31.0/task_ratings.csv](https://www.onetcenter.org/dl_files/database/db_31_0_csv/task_ratings.csv) | 39,006,755 | `52ee4ad320f1ca3c…` |
| [onet/31.0/task_statements.csv](https://www.onetcenter.org/dl_files/database/db_31_0_csv/task_statements.csv) | 3,461,375 | `4568e14d8db6f055…` |

## Method

1. Every official O\*NET task statement for each occupation is joined to AEI rows with `geo_id=GLOBAL`, `category_name=onet`, `hierarchy_level=0` by **Task ID** only. No fuzzy matching; tasks without a published cell are listed as unmatched.
2. Automation share per task = A / (A + U), where A and U are `collaboration_bucket_automation_pct` and `collaboration_bucket_augmentation_pct`. Tasks with A + U = 0 are excluded from means.
3. **Importance-weighted share** weights each matched task by its O\*NET Importance (1–5), so a high share on a rarely important task does not dominate.
4. **Drift** = May 2026 share minus April 2026 share for the same task (`claude_ai`).
5. The **occupation-level split** comes from the `soc_occupation` rows for the same month; usage rank is by `pct` among all occupations published that month.
6. `low_count_flag` marks rows whose A + U falls short of ~100, a sign one bucket was suppressed.

## Headline (May 2026, claude_ai)

| SOC | Occupation | O\*NET tasks | Matched (Core) | Task mean A/(A+U) | Imp-weighted | Occupation-level | Auto/Aug | Drift | API matched | API mean |
|---|---|---:|---|---:|---:|---:|---|---:|---:|---:|
| 15-1212.00 | Information Security Analysts | 11 | 3 (3/11) | 85.3% | 85.4% | 76.1% | 3/0 | +4.3 pts | 3 | 91.2% |
| 15-1299.04 | Penetration Testers | 22 | 5 (5/22) | 74.2% | 75.0% | 69.8% | 5/0 | -1.2 pts | 9 | 96.3% |
| 15-1299.05 | Information Security Engineers | 20 | 10 (10/20) | 62.7% | 62.5% | 63.7% | 8/2 | +0.3 pts | 11 | 93.4% |
| 15-1251.00 | Computer Programmers | 17 | 11 (9/13) | 67.6% | 67.9% | 63.3% | 10/1 | +0.6 pts | 9 | 93.3% |

*Matched (Core)*: tasks with a published cell, and matched Core tasks over all Core tasks. *Auto/Aug*: matched tasks leaning automation vs augmentation. *API*: `1p_api`, same month, never blended into the other columns.

## What the numbers do and do not say

- These are **observed Claude usage shares**: of the conversations matched to a task, the share Anthropic's classifier labelled automation (Claude does the task) rather than augmentation (Claude helps a person do it). They are not job-loss probabilities, not evidence that AI performs a task well on its own, and not career advice.
- Counts are of *conversations matched to tasks*, not of workers. "Conversations matched to penetration-testing tasks" is accurate; "penetration testers use Claude" is not.
- A task with no published cell is **unmatched**, not zero. AEI suppresses cells below its aggregation thresholds, so low coverage means little observed usage or suppression, and the data cannot tell the two apart.
- Headline numbers are `claude_ai` (Claude chat and Cowork). The 1P API is shown separately and never blended: API traffic is mostly programmatic pipelines and reads as automation on almost every task.
- The occupation-level split is computed by Anthropic on all classified conversations for the occupation. The task mean is computed here over the published task rows only. They measure different things and are reported side by side.
- Month-over-month drift covers two monthly snapshots; treat small moves as noise.

## 15-1212.00 Information Security Analysts

**Coverage:** 3 of 11 O\*NET tasks have a published `claude_ai` cell for May 2026 (3 of 11 Core tasks).

**Occupation level:** 76.1% automation across all conversations matched to this occupation, next to the 85.3% mean over its 3 published task rows. Usage share 0.01% of `claude_ai` conversations, rank 374 of 718 occupations.

**1P API** (separate, not blended): 3 tasks matched, mean 91.2%; occupation level 92.3% automation.

**Highest automation share** (matched tasks, `claude_ai`)

| Task ID | Task | A/(A+U) | Importance |
|---|---|---:|---:|
| 5317 | Modify computer security files to incorporate new software, correct errors, or change individual access status. | 90% | 4.10 |
| 5321 | Encrypt data transmissions and erect firewalls to conceal confidential information as it is being transmitted and to keep out tainted digital transfers. | 87% | 4.18 |
| 5315 | Confer with users to discuss issues such as computer data access needs, security violations, and programming changes. | 79% | 3.94 |

**Unmatched** (8 tasks, no published cell; not zero), by Importance

| Task ID | Task | Type | Importance |
|---|---|---|---:|
| 5314 | Develop plans to safeguard computer files against accidental or unauthorized modification, destruction, or disclosure and to meet emergency data processing needs. | Core | 4.40 |
| 5316 | Monitor current reports of computer viruses to determine when to update virus protection systems. | Core | 4.23 |
| 5320 | Perform risk assessments and execute tests of data processing system to ensure functioning of data processing activities and security measures. | Core | 4.12 |
| 5323 | Review violations of computer security procedures and discuss procedures with violators to ensure violations are not repeated. | Core | 4.04 |
| 5322 | Document computer security and emergency measures policies, procedures, and tests. | Core | 3.94 |
| 5319 | Monitor use of data files and regulate access to safeguard information in computer files. | Core | 3.89 |
| 5318 | Coordinate implementation of computer system plan with establishment personnel and outside vendors. | Core | 3.87 |
| 5313 | Train users and promote security awareness to ensure system security and to improve server and network efficiency. | Core | 3.81 |

## 15-1299.04 Penetration Testers

**Coverage:** 5 of 22 O\*NET tasks have a published `claude_ai` cell for May 2026 (5 of 22 Core tasks).

**Occupation level:** 69.8% automation across all conversations matched to this occupation, next to the 74.2% mean over its 5 published task rows. Usage share 0.04% of `claude_ai` conversations, rank 250 of 718 occupations.

**1P API** (separate, not blended): 9 tasks matched, mean 96.3%; occupation level 97.4% automation.

**Highest automation share** (matched tasks, `claude_ai`)

| Task ID | Task | A/(A+U) | Importance |
|---|---|---:|---:|
| 21756 | Gather cyber intelligence to identify vulnerabilities. | 90% | 4.56 |
| 21758 | Identify security system weaknesses, using penetration tests. | 83% | 4.74 |
| 21746 | Conduct network and security system audits, using established criteria. | 77% | 4.39 |
| 21754 | Document penetration test findings. | 64% | 4.84 |
| 21747 | Configure information systems to incorporate principles of least functionality and least access. | 57% | 3.40 |

**Unmatched** (17 tasks, no published cell; not zero), by Importance

| Task ID | Task | Type | Importance |
|---|---|---|---:|
| 21765 | Write audit reports to communicate technical and procedural findings and recommend solutions. | Core | 4.58 |
| 21761 | Maintain up-to-date knowledge of hacking trends. | Core | 4.53 |
| 21760 | Keep up with new penetration testing tools and methods. | Core | 4.47 |
| 21757 | Identify new threat tactics, techniques, or procedures used by cyber threat actors. | Core | 4.42 |
| 21752 | Develop security penetration testing processes, such as wireless, data networks, and telecommunication security tests. | Core | 4.37 |
| 21763 | Test the security of systems by attempting to gain access to networks, Web-based applications, or computers. | Core | 4.37 |
| 21755 | Evaluate vulnerability assessments of local computing environments, networks, infrastructures, or enclave boundaries. | Core | 4.32 |
| 21762 | Prepare and submit reports describing the results of security fixes. | Core | 4.11 |
| 21749 | Develop and execute tests that simulate the techniques of known cyber threat actors. | Core | 4.06 |
| 21753 | Discuss security solutions with information technology teams or management. | Core | 4.05 |
| 21745 | Collect stakeholder data to evaluate risk and to develop mitigation strategies. | Core | 3.94 |
| 21764 | Update corporate policies to improve cyber security. | Core | 3.93 |
| 21744 | Assess the physical security of servers, systems, or network devices to identify vulnerability to temperature, vandalism, or natural disasters. | Core | 3.89 |
| 21759 | Investigate security incidents, using computer forensics, network forensics, root cause analysis, or malware analysis. | Core | 3.88 |
| 21750 | Develop infiltration tests that exploit device vulnerabilities. | Core | 3.84 |
| 21748 | Design security solutions to address known device vulnerabilities. | Core | 3.75 |
| 21751 | Develop presentations on threat intelligence. | Core | 3.33 |

## 15-1299.05 Information Security Engineers

**Coverage:** 10 of 20 O\*NET tasks have a published `claude_ai` cell for May 2026 (10 of 20 Core tasks).

**Occupation level:** 63.7% automation across all conversations matched to this occupation, next to the 62.7% mean over its 10 published task rows. Usage share 0.12% of `claude_ai` conversations, rank 147 of 718 occupations.

**1P API** (separate, not blended): 11 tasks matched, mean 93.4%; occupation level 95.5% automation.

**Highest automation share** (matched tasks, `claude_ai`)

| Task ID | Task | A/(A+U) | Importance |
|---|---|---:|---:|
| 21784 | Troubleshoot security and network problems. | 90% | 3.74 |
| 21775 | Identify or implement solutions to information security problems. | 72% | 3.94 |
| 21767 | Conduct investigations of information security breaches to identify vulnerabilities and evaluate the damage. | 71% | 4.22 |
| 21772 | Develop or implement software tools to assist in the detection, prevention, and analysis of security threats. | 67% | 3.71 |
| 21781 | Review security assessments for computing environments or check for compliance with cybersecurity standards and regulations. | 64% | 3.76 |

**Lowest automation share** (matched tasks, `claude_ai`)

| Task ID | Task | A/(A+U) | Importance |
|---|---|---:|---:|
| 21783 | Train staff on, and oversee the use of, information security standards, policies, and best practices. | 42% | 4.28 |
| 21780 | Recommend information security enhancements to management. | 47% | 3.94 |
| 21779 | Provide technical support to computer users for installation and use of security products. | 57% | 3.38 |
| 21785 | Write reports regarding investigations of information security breaches or network evaluations. | 58% | 3.71 |
| 21773 | Develop or install software, such as firewalls and data encryption programs, to protect sensitive information. | 60% | 4.11 |

**Unmatched** (10 tasks, no published cell; not zero), by Importance

| Task ID | Task | Type | Importance |
|---|---|---|---:|
| 21776 | Identify security system weaknesses, using penetration tests. | Core | 4.56 |
| 21769 | Coordinate monitoring of networks or systems for security breaches or intrusions. | Core | 4.42 |
| 21766 | Assess the quality of security controls, using performance indicators. | Core | 4.41 |
| 21782 | Scan networks, using vulnerability assessment tools to identify vulnerabilities. | Core | 4.28 |
| 21774 | Develop response and recovery strategies for security breaches. | Core | 4.25 |
| 21777 | Oversee development of plans to safeguard computer files against accidental or unauthorized modification, destruction, or disclosure or to meet emergency data processing needs. | Core | 4.06 |
| 21771 | Develop information security standards and best practices. | Core | 3.94 |
| 21778 | Oversee performance of risk assessment or execution of system tests to ensure the functioning of data processing activities or security measures. | Core | 3.88 |
| 21770 | Coordinate vulnerability assessments or analysis of information security systems. | Core | 3.83 |
| 21768 | Coordinate documentation of computer security or emergency measure policies, procedures, or tests. | Core | 3.72 |

## 15-1251.00 Computer Programmers

**Coverage:** 11 of 17 O\*NET tasks have a published `claude_ai` cell for May 2026 (9 of 13 Core tasks).

**Occupation level:** 63.3% automation across all conversations matched to this occupation, next to the 67.6% mean over its 11 published task rows. Usage share 1.67% of `claude_ai` conversations, rank 9 of 718 occupations.

**1P API** (separate, not blended): 9 tasks matched, mean 93.3%; occupation level 91.5% automation.

**Highest automation share** (matched tasks, `claude_ai`)

| Task ID | Task | A/(A+U) | Importance |
|---|---|---:|---:|
| 1275 | Investigate whether networks, workstations, the central processing unit of the system, or peripheral equipment are responding to a program's instructions. | 96% | 3.26 |
| 1268 | Conduct trial runs of programs and software applications to be sure they will produce the desired information and that the instructions are correct. | 89% | 3.96 |
| 1269 | Compile and write documentation of program development and subsequent revisions, inserting comments in the coded instructions so others can understand the program. | 77% | 3.56 |
| 1267 | Correct errors by making appropriate changes and rechecking the program to ensure that the desired results are produced. | 74% | 4.38 |
| 1270 | Write, update, and maintain computer programs or software packages to handle specific jobs such as tracking inventory, storing or retrieving data, or controlling other equipment. | 72% | 4.15 |

**Lowest automation share** (matched tasks, `claude_ai`)

| Task ID | Task | A/(A+U) | Importance |
|---|---|---:|---:|
| 1281 | Train subordinates in programming and program coding. | 38% | 3.53 |
| 1276 | Prepare detailed workflow charts and diagrams that describe input, output, and logical operation, and convert them into a series of instructions coded in a computer language. | 51% | 3.58 |
| 21049 | Develop Web sites. | 52% | 3.24 |
| 1273 | Write, analyze, review, and rewrite programs, using workflow chart and diagram, and applying knowledge of computer capabilities, subject matter, and symbolic logic. | 62% | 4.42 |
| 1274 | Write or contribute to instructions or manuals to guide end users. | 65% | 3.27 |

**Unmatched** (6 tasks, no published cell; not zero), by Importance

| Task ID | Task | Type | Importance |
|---|---|---|---:|
| 1271 | Consult with managerial, engineering, and technical personnel to clarify program intent, identify problems, and suggest changes. | Core | 4.04 |
| 1278 | Consult with and assist computer operators or system analysts to define and resolve problems in running computer programs. | Core | 3.50 |
| 1277 | Perform systems analysis and programming tasks to maintain and control the use of computer systems software as a systems programmer. | Core | 3.28 |
| 1279 | Assign, coordinate, and review work and activities of programming personnel. | Core | 3.22 |
| 21050 | Train users on the use and function of computer programs. | Supplemental | 2.96 |
| 1280 | Collaborate with computer manufacturers and other users to develop new programming methods. | Supplemental | 2.84 |

## Files

- `audit_15-1212.00.csv`
- `audit_15-1212.00_may2026_headline.csv`
- `audit_15-1299.04.csv`
- `audit_15-1299.04_may2026_headline.csv`
- `audit_15-1299.05.csv`
- `audit_15-1299.05_may2026_headline.csv`
- `audit_15-1251.00.csv`
- `audit_15-1251.00_may2026_headline.csv`
- `summary.json`
- `REPORT.md`

## Citation and licences

AEI data © Anthropic, CC BY 4.0. Cite as:

```bibtex
@online{anthropic2026aeiv6,
  author = {Maxim Massenkoff and Eva Lyubich and Szymon Sacher and Zoe Hitzig and Shaoyi Zhang and Ryan Heller and Peter McCrory},
  title = {Anthropic Economic Index report: Cadences},
  date = {2026-06-26},
  year = {2026},
  url = {https://www.anthropic.com/research/economic-index-june-2026-report}
}
```

This report includes information from the O\*NET 31.0 Database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA). Used under the CC BY 4.0 license. O\*NET® is a trademark of USDOL/ETA. The authors have modified all or some of this information. USDOL/ETA has not approved, endorsed, or tested these modifications.

Interactive alternative: the Anthropic Economic Index explorer at https://www.anthropic.com/economic-index. Headline file label: `may2026`.
