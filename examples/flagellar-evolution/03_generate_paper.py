#!/usr/bin/env python3
"""Step 3: Generate the LaTeX paper from the corpus answers + reconstructed refs.

Reads answers.json (step 1) and bib.json (step 2) and emits a styled LaTeX
document with numbered \\cite references and a provenance/honesty note. The
per-section prose here is the human-authored synthesis of the retrieved answers;
this script is where you shape the narrative for a new topic.

Usage:
    python 03_generate_paper.py --answers answers.json --bib bib.json \
        --out paper/flagellar-evolution.tex
"""
import argparse
import json
import os
import sys


def cite(*pids):
    return "\\cite{" + ",".join(pids) + "}"


def fmt_ref(r):
    parts = []
    if r.get("authors", "").strip():
        parts.append(r["authors"].strip() + ".")
    t = r.get("title", "").strip().rstrip(".")
    if t:
        parts.append("\\emph{" + t + "}.")
    seg = r.get("journal", "").strip()
    if str(r.get("volume", "")).strip():
        seg += " " + str(r["volume"]).strip()
    if str(r.get("pages", "")).strip():
        seg += ":" + str(r["pages"]).strip()
    if str(r.get("year", "")).strip():
        seg += " (" + str(r["year"]).strip() + ")"
    if seg.strip():
        parts.append(seg.strip() + ".")
    s = " ".join(parts)
    for a_, b_ in [("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#")]:
        s = s.replace(a_, b_)
    return s


PREAMBLE = r"""\documentclass[11pt,letterpaper]{article}
\usepackage[margin=1in]{geometry}
\usepackage{lmodern}\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}
\usepackage{microtype}\usepackage{amsmath,amssymb}\usepackage{xcolor}
\usepackage[most]{tcolorbox}\usepackage{booktabs}\usepackage{enumitem}
\usepackage{fancyhdr}\usepackage{titlesec}\usepackage[hidelinks]{hyperref}
\definecolor{Ink}{HTML}{1B2A4A}\definecolor{Accent}{HTML}{8C4F2B}
\definecolor{MathBg}{HTML}{FAF6EE}\definecolor{Sky}{HTML}{D9E4F5}
\titleformat{\section}{\Large\bfseries\color{Ink}}{\thesection}{0.6em}{}
\titleformat{\subsection}{\large\bfseries\color{Accent}}{\thesubsection}{0.5em}{}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small\color{Ink}\textbf{Arca} --- Flagellar Evolution}
\fancyhead[R]{\small\thepage}\renewcommand{\headrulewidth}{0.4pt}
\newtcolorbox{keybox}[1]{enhanced,breakable,colback=Sky,colframe=Ink,
  fonttitle=\bfseries\color{white},coltitle=white,
  attach boxed title to top left={xshift=10pt,yshift=-8pt},
  boxed title style={colback=Ink,sharp corners},title={#1},arc=2mm,boxrule=0.8pt}
\newtcolorbox{caveatbox}{enhanced,breakable,colback=MathBg,colframe=Accent,
  fonttitle=\bfseries\color{Accent},title={Provenance \& honesty note},arc=1mm,boxrule=0.5pt}
\title{\color{Ink}\Huge\textbf{Open Questions in the Evolution of the Bacterial Flagellum}\\[6pt]
  \large\color{Accent}A corpus-grounded synthesis, built with Arca}
\author{Generated with Arca \\ \small retrieval + cited synthesis over a 516-paper corpus}
\date{\today}
\begin{document}\maketitle
"""

# The narrative below is the human-authored synthesis of the step-1 answers.
# It is intentionally checked in as prose (not regenerated) so the example is
# deterministic; regenerate it by editing here after re-running the queries.
BODY_TEMPLATE = r"""
\begin{abstract}\noindent The bacterial flagellum is among the most-studied molecular
machines, yet its evolutionary history remains only partially resolved. This note frames
four open questions the corpus itself surfaces---the direction of evolution between the
flagellar export apparatus and the type~III secretion system (T3SS), the origin and
diversification of the ion-powered motor, the bacterial-flagellum/archaellum relationship,
and reconstruction of a minimal ancestral machine---with the specific evidence and
disagreements around each. All claims are retrieved from the corpus via Arca.\end{abstract}
\tableofcontents\vspace{1em}

\section{Introduction}
The flagellum is a supramolecular motility machine of $\sim$30 proteins---a basal-body
rotary motor, a hook, and a helical filament %(Sowa-2008-b)%. At least 40 genes are
involved, $\ge$24 contributing proteins to the final structure %(DeRosier-2006)%, with an
earlier count of $\sim$20 structural plus $\sim$30 assembly/maintenance proteins
%(Shapiro-1995)%. Mechanistic maturity has not produced a settled evolutionary account;
where the corpus addresses origins it surfaces the same open questions, which organize this note.

\section{Which came first --- the flagellum or the T3SS?}
The flagellar export apparatus and virulence T3SS are ``evolutionarily and functionally
related'' %(Erhardt-2014)%: about half of the T3SS proteins are conserved and similar to
flagellar basal-body proteins %(Ghosh-2004)%, and up to eight flagellar-assembly products
are T3SS homologs %(Stephens-1996)%. Macnab held the flagellar pathway \emph{is} a type~III
pathway %(Macnab-1999)%.
\begin{keybox}{Consensus vs.\ the live disagreement}
Most evidence favors the flagellum as \textbf{ancestral}, with virulence T3SS derived from
it---flagellar antiquity %(Stephens-1996,Macnab-1999)%, closer similarity among flagellar
homologs, and patchy plasmid/island distribution implying later horizontal transfer
%(Stephens-1996)%. \emph{But} a dissenting analysis argues the two share a \textbf{common
ancestor} rather than one descending from the other %(Ghosh-2004)%---an unresolved
topological disagreement.
\end{keybox}

\section{Origin and diversification of the ion-powered motor}
The torque core is conserved: stator (MotA/MotB or homologs) plus rotor FliG/FliM/FliN,
with FliG largely interchangeable across species %(Yakushi-2006)%; proton/sodium chimeras
function %(Sowa-2008-c)%. A single conserved MotB/PomB aspartate (D32; D24 in PomB) is
essential but \emph{cannot} explain selectivity %(Hu-2023)%; cryo-EM places Na$^+$
selectivity partly in three PomA threonines %(Hu-2023)%. Stators span single-ion,
multiple-stator, and dual-ion systems ($\ge$65 species carry $\ge$2 stators)
%(Sowa-2008)%, some with lineage-specific parts like MotX/MotY %(Yakushi-2006,Jaques-1999)%.
The open question is the order and drivers of this diversification %(Minamino-2011)%.

\section{Flagellum vs.\ archaellum --- one origin or two?}
Archaeal genomes contain \textbf{no homologs} of bacterial flagellins, rod, hook, ring,
switch, or Mot proteins %(Thomas-2001)%; archaeal filaments are thinner, glycosylated,
leader-peptide-processed, and lack the central assembly channel %(Thomas-2001,Thomas-2002)%.
Archaeal flagellins instead resemble \textbf{type~IV pilins} %(Thomas-2002)%. The reading
is independent, convergent evolution of rotary swimming %(Thomas-2002)%---with shared
chemotaxis control bolted onto a non-homologous motor %(Thomas-2001)%.

\section{Can we reconstruct a minimal ancestral machine?}
That ATPase activity is \emph{dispensable} for type~III export %(Erhardt-2014)% reframes
the ``flagellum from a proto-F\textsubscript{o}F\textsubscript{1} ATP synthase'' story: a
proton-powered primordial export system may precede an ATPase \emph{added later}
%(Erhardt-2014)%, implying a secretion pore ancestral to both motor and ATPase. The corpus
carries no full ancestral-state reconstruction and is candid it lacks the
irreducible-complexity debate %(Sowa-2008-b)%. The tractable open question: the smallest
selectable sub-assembly on a credible path to the modern motor.

\section{Synthesis: a conserved core, an unconserved history}
A conserved functional core (rotor--stator electrostatics %(Berry-1993,Yakushi-2006)%, the
export apparatus, the three-part body plan) sits amid lineage-specific elaboration
%(Sowa-2008-b)%. The machine is conserved; its history is not agreed. The productive
questions---order, coupling ion, ancestral pore---are answerable with phylogenomics and
ancestral-sequence reconstruction, defining the most useful corpus augmentation.

\begin{caveatbox}
Generated by retrieving passages from a 516-paper flagellum/ATP corpus via Arca and
synthesizing with an LLM; every claim traces to a retrieved passage. References were
reconstructed by extracting metadata from the parsed source PDFs. Note the corpus key
\texttt{Sowa-2008} resolves to Biquet-Bisquert et al.\ (2021) and \texttt{Sowa-2008-b} to
Terashima et al.\ (2017)---automated author-year keying collisions, corrected here. No
bibliographic detail was invented; unverifiable fields were left blank. Volume/page numbers
are LLM-extracted and should be cross-checked against DOIs before external use.
\end{caveatbox}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", default="answers.json")
    ap.add_argument("--bib", default="bib.json")
    ap.add_argument("--out", default="paper/flagellar-evolution.tex")
    a = ap.parse_args()

    bib = json.load(open(a.bib))
    refs, order = bib["refs"], bib["order"]

    # Replace %(id,id)% markers in the template with \cite{...}
    body = BODY_TEMPLATE
    import re
    for m in set(re.findall(r"%\(([^)]+)\)%", body)):
        ids = [x.strip() for x in m.split(",")]
        # only cite ids that made it into the bibliography
        ids = [i for i in ids if i in refs]
        repl = cite(*ids) if ids else ""
        body = body.replace(f"%({m})%", repl)

    bibitems = "\n".join(f"\\bibitem{{{pid}}} {fmt_ref(refs[pid])}" for pid in order)
    tail = ("\n\\begin{thebibliography}{99}\n\\small\n" + bibitems +
            "\n\\end{thebibliography}\n\\end{document}\n")

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w").write(PREAMBLE + body + tail)
    print(f"wrote {a.out} ({len(order)} references)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
