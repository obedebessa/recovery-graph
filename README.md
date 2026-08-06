# The Recovery Graph

This repository contains the IJCA-formatted manuscript and the reference artifact for:

> Obede Bessa. “The Recovery Graph: A Formal Model for Queryable Operational Continuity in Cloud-Native Systems.” 2026.

The paper distinguishes infrastructure restoration from operational recovery and introduces a typed, attributed, evidence-carrying graph for representing recovery dependencies, guarded transitions, evidence freshness, readiness, confidence, schedules, and governance queries.

## Contents

- `paper/recovery-graph-ijca.pdf` — submission-ready IJCA manuscript (A4, 17 pages).
- `manuscript/` — complete LaTeX source using the IJCA class and bibliography style.
- `artifact/rgkit.py` — reference model, checks, algorithms, metrics, worked example, and pathological variant.
- `artifact/example_report.txt` — expected report for the worked example.
- `review_log.md` — section-by-section internal review and revision record.

## Reproduce the artifact

Python 3.10 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 artifact/rgkit.py
python3 artifact/rgkit.py --selftest
python3 artifact/rgkit.py --pathological
```

The self-test should finish with `self-test OK`. The default run should match `artifact/example_report.txt`.

## Build the manuscript

With Tectonic:

```bash
cd manuscript
tectonic main.tex
```

Alternatively, use a current TeX Live installation with the standard LaTeX/BibTeX sequence.

## Status and rights

This is the author-prepared version submitted to the *International Journal of Computer Applications*. No open-source or Creative Commons license is granted. See `RIGHTS.md` before redistributing or reusing any part of the repository.

