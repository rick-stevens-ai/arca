# Example: from corpus to a cited paper with Arca

This is a complete, reproducible worked example of the Arca workflow end to end:

> **build an index over a paper corpus → query it with grounded, cited answers →
> assemble those answers into a short, properly-referenced paper (LaTeX → PDF).**

The showcase corpus is a 516-paper collection on the **bacterial flagellum and
ATP synthase** (parsed to `.md`/`.mmd`), and the deliverable is a short synthesis,
*"Open Questions in the Evolution of the Bacterial Flagellum."* The finished PDF is
in [`paper/`](paper/).

Everything here uses Arca's own API — the same `search`/`answer` tools the fleet
hits over MCP — so it doubles as a template for turning any corpus into a cited
write-up.

## Pipeline

| Step | Script | What it does |
|------|--------|--------------|
| 0 | `arca-build-index` | Build a FAISS index over the corpus `.md`/`.mmd` (Arca CLI) |
| 1 | `01_query_corpus.py` | Ask the corpus N grounded questions via `arca_answer` |
| 2 | `02_extract_citations.py` | LLM-extract real bibliographic metadata from cited PDFs |
| 3 | `03_generate_paper.py` | Emit LaTeX with numbered `\cite` refs from the answers |
| 4 | `build_paper.sh` | Two-pass `pdflatex` → `paper/flagellar-evolution.pdf` |

Steps 1–3 are the reusable core; 0 and 4 are corpus- and format-specific.

## Prerequisites

- Arca installed (`pip install -e .` from the repo root) and reachable embedding +
  generation endpoints (defaults target the fleet Argo proxy; override with the
  `ARCA_*` env vars in `arca/config.py`).
- The corpus parsed to `.md` (and/or `.mmd`), one file per paper, basename = paper id.
- For step 4: a TeX Live install with `pdflatex` (see the repo's `latex` notes).

## Run it

```bash
# 0. Build an index over the flagellum corpus (adjust the path to your parsed set)
ARCA_INDEX_NAME=flagellum \
  arca-build-index --source /path/to/PDF-Flagellum-ATP --name flagellum

# 1. Query the corpus — grounded, cited answers (writes answers.json)
python 01_query_corpus.py --index flagellum --out answers.json

# 2. Reconstruct real references from the cited papers (writes bib.json)
python 02_extract_citations.py --source /path/to/PDF-Flagellum-ATP \
  --answers answers.json --out bib.json

# 3. Generate the LaTeX (writes paper/flagellar-evolution.tex)
python 03_generate_paper.py --answers answers.json --bib bib.json \
  --out paper/flagellar-evolution.tex

# 4. Compile to PDF
bash build_paper.sh paper/flagellar-evolution.tex
```

## Why the citation-extraction step (2) matters

Corpus ids are internal keys derived from source-file provenance, and automated
author-year keying produces collisions (e.g. `Sowa-2008-b`, `-c`, `-d` are three
*different* papers). Step 2 opens each cited PDF's parsed header and has an LLM
extract the true authors/title/journal/year — never inventing fields it can't
verify — so the final reference list is honest. The generated paper carries a
provenance note documenting any id→reference corrections.

## Honesty stance

Every claim in the generated paper traces to a passage Arca actually retrieved.
Where the corpus doesn't cover something (this set is thin on the explicit
irreducible-complexity debate, for instance), the paper says so rather than
padding. Volume/page numbers are LLM-extracted from parsed headers and should be
cross-checked against DOIs before external publication.
