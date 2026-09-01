# Open Questions in the Evolution of the Bacterial Flagellum

*A short synthesis grounded in the flagellum/ATP corpus (516 papers, 1921–2025), retrieved via the corpus-rag service. Every claim below is traceable to a corpus document, cited by its internal corpus id (e.g. [Erhardt-2014]). A note on citation ids and an honesty caveat appear at the end.*

---

## Abstract

The bacterial flagellum is among the most-studied molecular machines, yet its evolutionary history remains only partially resolved. Decades of structural, genetic, and comparative work have converged on a clear picture of *what* the flagellum is and *how* it works, while leaving several *how-did-it-get-here* questions genuinely open. This note frames four such questions that the corpus itself surfaces — the direction of evolution between the flagellar export apparatus and the type III secretion system (T3SS), the origin and diversification of the ion-powered motor, the relationship between the bacterial flagellum and the archaeal archaellum, and the reconstruction of a minimal ancestral machine — and summarizes the specific evidence and the specific disagreements around each.

---

## 1. Introduction

The flagellum is a supramolecular motility machine built from roughly 30 different proteins, organized into a basal-body rotary motor, a hook acting as a universal joint, and a helical filament that serves as a propeller [Sowa-2008-b]. Estimates of the parts count vary with how one counts: at least 40 genes are involved, with at least 24 contributing proteins to the final structure [DeRosier-2006], and a widely-cited earlier figure of ~20 structural proteins plus ~30 more for construction, function, and maintenance [Shapiro-1995]. This complexity — a self-assembling, ion-powered, reversible rotary motor — is precisely what makes its evolution scientifically interesting.

Importantly, the mechanistic maturity of the field does not translate into a settled evolutionary account. The corpus is dense with structure and mechanism and comparatively thin on explicit macro-evolutionary modeling; where it does address origins, it repeatedly surfaces the same handful of unresolved questions. We treat those as the paper's organizing spine.

---

## 2. Open Question 1: Which came first — the flagellum or the T3SS?

The single most-developed evolutionary thread in the corpus is the deep relationship between the flagellar export apparatus and the virulence-associated T3SS. The two are "evolutionarily and functionally related" [Erhardt-2014]: roughly half of the ~20–25 T3SS proteins are conserved across type III systems, and most of these are also similar in sequence to basal-body proteins of the flagellum [Ghosh-2004]; up to eight flagellar-assembly gene products are homologous to conserved T3SS components [Stephens-1996]. Macnab put it most strongly — the flagellar pathway *is* a type III pathway, "differing only in the nature of its export substrates and in the fact that it operates via a working organelle of propulsion" [Macnab-1999].

**Where the consensus lies.** The preponderance of evidence in the corpus favors the flagellum as the *ancestral* system, with the virulence T3SS (Type IIIb) derived from it. Three lines support this: (i) flagella are ancient, present across most eubacteria and some archaea, and predate the metazoan/plant hosts that virulence systems target [Stephens-1996; Macnab-1999]; (ii) flagellar (Type IIIa) homologs are more similar to one another than to virulence (Type IIIb) components, consistent with Type IIIb arising from a duplicated flagellar set [Stephens-1996]; and (iii) Type IIIb systems are patchily distributed, often on plasmids or pathogenicity islands with anomalous base composition, implying later spread by horizontal gene transfer [Stephens-1996].

**Where it remains open.** A dissenting analysis holds that the T3SS is *as ancient* as the flagellar apparatus and that the two share a **common ancestor**, rather than the T3SS having descended from the flagellum [Ghosh-2004]. This is not a settled matter of degree but a genuine topological disagreement about the tree. The corpus does not contain the phylogenomic evidence that would adjudicate it — a real gap.

---

## 3. Open Question 2: How did the ion-powered motor originate and diversify?

The torque-generating core is strikingly conserved: five proteins — the stator (MotA/MotB or homologs) and the rotor proteins FliG, FliM, FliN — recur across motor types, and the FliG C-terminal domain is largely interchangeable between species [Yakushi-2006]. Chimeric motors that mix proton- and sodium-type components function [Sowa-2008-c], arguing that H⁺ and Na⁺ motors share a common ancestral mechanism that diversified mainly in its ion coupling.

**A concrete open puzzle: the selectivity filter.** A single aspartate in MotB/PomB (D32 in *E. coli* MotB [Sowa-2008]; D24 in PomB [Hu-2023]) is essential and universally conserved across stator families — which means it *cannot* be what distinguishes a sodium motor from a proton motor [Hu-2023]. Recent cryo-EM of the *Vibrio* PomAB complex located Na⁺ selectivity partly in three threonines of PomA (T158/T185/T186), conserved in all sodium stators [Hu-2023], revising the older view that the B subunit alone sets specificity. How ion selectivity is encoded — and therefore how it *changes* over evolution — is an active, unfinished structural problem.

**Diversification is real and recent-looking.** Stator systems span single-ion (MotAB/PomAB), multiple-stator genomes (≥65 species carry two or more stators; *V. alginolyticus* runs Na⁺ PomAB polar and H⁺ MotAB lateral systems), and genuinely dual-ion stators (*Bacillus clausii* MotAB couples H⁺ or Na⁺; *B. alcalophilus* MotPS couples Na⁺/K⁺/Rb⁺) [Sowa-2008]. Some lineages bolt on extra parts — the *Vibrio* Na⁺ motor requires outer-membrane MotX/MotY that engineered hybrid motors do without [Yakushi-2006; Jaques-1999]. The open question is the *order and drivers* of this diversification: which coupling ion is ancestral, and how many times has switching occurred?

---

## 4. Open Question 3: Flagellum vs. archaellum — one origin or two?

Comparative data force a sharp conclusion. The archaeal motility organelle (archaellum) does the same job by entirely different means: archaeal genomes contain **no homologs** of bacterial flagellins, rod, hook, ring, switch, or Mot proteins [Thomas-2001]. Archaeal filaments are thinner (10–14 nm vs. ~20 nm), built from multiple glycosylated flagellins made with cleaved leader peptides, and — critically — appear to lack the central assembly channel that defines bacterial flagellar growth [Thomas-2001; Thomas-2002]. Instead, archaeal flagellins resemble **type IV pilins**, and archaellum assembly factors resemble type IV pilus NTPases and membrane proteins [Thomas-2002].

The corpus's own reading is that flagellar biogenesis "may have evolved independently in these two domains of life" [Thomas-2002] — convergent evolution of rotary swimming from unrelated parts. A telling wrinkle: archaea retain bacterial-like chemotaxis genes (*cheA/cheW/cheY*) bolted onto a non-homologous motor [Thomas-2001], so the *control system* is shared while the *machine* is not. Open questions: is the archaellum/type-IV-pilus link ancestral or convergent in turn, and what does a channel-less assembly mechanism imply about the minimal requirements for a rotary filament?

---

## 5. Open Question 4: Can we reconstruct a minimal ancestral machine?

The T3SS thread offers the corpus's clearest stab at a stepwise origin. The observation that ATPase activity is *dispensable* for type III export [Erhardt-2014] reframes the classic "flagellum from a proto-F₀F₁ ATP synthase" story: rather than ATP hydrolysis being foundational, a **proton-powered primordial export system** may have come first, with a proto-F₁-ATPase *added later* to facilitate export [Erhardt-2014]. That inverts the intuitive order (energy module first) and suggests a plausible ancestral intermediate — a secretion pore that predates both the motor and the ATPase.

But the corpus does not carry a full ancestral-state reconstruction, and it is candid about a related gap: it lacks substantive treatment of the irreducible-complexity debate and detailed origin scenarios, pointing outward to work not in the set (e.g. Pallen & Matzke's origin-of-flagella analysis, referenced but not contained) [Sowa-2008-b]. The open question is empirical and tractable: what is the smallest functional sub-assembly (secretion-only? secretion-plus-rotation?) that is both selectable and on a credible path to the modern motor?

---

## 6. Synthesis: a conserved core, an unconserved history

Across all four questions a single pattern recurs — a **strongly conserved functional core** (rotor–stator electrostatics, the export apparatus, the three-part body plan) surrounded by **lineage-specific elaboration** (divergent peripheral motor structures seen by electron cryotomography [Sowa-2008-b], extra stator parts, alternate ion couplings). The machine is conserved; its *history* is not agreed. The productive open questions are therefore less "could this evolve?" and more "in what order, powered by which ion, and from which pre-existing pore?" These are answerable with phylogenomics and ancestral-sequence reconstruction — methods largely outside the current corpus, which defines the most useful direction for augmenting it.

---

## 7. A note on citations and honesty

The bracketed ids (e.g. [Sowa-2008-c]) are the **internal keys of the corpus-rag index**, assigned from source-file provenance, not verified bibliographic references. Some ids are known to be imperfect: the automated author-year naming from the augmentation step produced disambiguated collisions (e.g. `Sowa-2008-b`, `-c`, `-d`) that do not all correspond to Sowa & Berry — `Sowa-2008-b`, for instance, maps to a Terashima/Minamino structural review in the parsed text. The claims are faithful to the retrieved passages; the id→full-citation mapping should be corrected against the actual PDFs before this note is used as anything but an internal synthesis. No author, journal, or bibliographic detail has been invented to paper over that gap.

*Generated with corpus-rag (`corpus_answer`) over the flagellum corpus; retrieval + synthesis via the m1 LiteLLM aggregator. Source passages are on disk in `~/Dropbox/PDF-Flagellum-ATP/`.*
