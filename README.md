# The Recovery Graph

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22017711.svg)](https://doi.org/10.5281/zenodo.22017711)

This repository contains the IJCA-formatted manuscript and the reference artifact for:

> Obede Bessa Rocha da Silva. “The Recovery Graph: A Formal Model for Queryable Operational Continuity in Cloud-Native Systems.” 2026.

The paper distinguishes infrastructure restoration from operational recovery and introduces a typed, attributed, evidence-carrying graph for representing recovery dependencies, guarded transitions, evidence freshness, readiness, confidence, schedules, and governance queries.

## Read and cite the paper

- [Read the searchable author preprint](paper/Recovery_Graph_Preprint_v1.0.pdf)
- [Open the archived preprint and DOI](https://doi.org/10.5281/zenodo.22017711)
- The cover identifies the manuscript as an unrefereed author version submitted
  to IJCA and uses the author's complete publication name.
- Use GitHub's **Cite this repository** control for citation formats.

**APA**

> Rocha da Silva, O. B. (2026). *The Recovery Graph: A Formal Model for
> Queryable Operational Continuity in Cloud-Native Systems* (Version 1.0)
> [Preprint]. Zenodo. https://doi.org/10.5281/zenodo.22017711

**BibTeX**

```bibtex
@techreport{rocha_da_silva_recovery_graph_2026,
  author  = {Obede Bessa Rocha da Silva},
  title   = {The Recovery Graph: A Formal Model for Queryable Operational Continuity in Cloud-Native Systems},
  year    = {2026},
  version = {1.0},
  doi     = {10.5281/zenodo.22017711},
  url     = {https://doi.org/10.5281/zenodo.22017711},
  note    = {Preprint; unrefereed author version submitted to IJCA}
}
```

## Contents

- `paper/recovery-graph-ijca.pdf` — submission-ready IJCA manuscript (A4, 17 pages).
- `paper/Recovery_Graph_Preprint_v1.0.pdf` — public author preprint with standardized metadata cover.
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
