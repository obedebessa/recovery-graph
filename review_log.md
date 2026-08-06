# Reviewer #2 Log — *The Recovery Graph*

Working protocol requested by the author: **after every section, critique the draft
as Reviewer #2, revise, and only then continue.** This log records, per section,
the referee-style concerns raised against the first draft and the revisions
applied before the section was frozen. Concern IDs are `R2.<section>.<n>`;
severity is (major)/(minor). Every "revision applied" is verifiable in the
shipped manuscript.

---

## Section 1 — Introduction

**R2.1.1 (major).** *The restore/recover distinction is practitioner folklore, not a
discovery.* ITIL speaks of "service restoration," DR practice distinguishes RTO of
systems vs. services, and every SRE knows a running pod is not a working service.
Claiming the distinction itself as the contribution invites rejection.
→ **Revision applied:** the introduction now concedes the point explicitly
("Practitioners have long distinguished, informally…") with citations to ITIL,
NIST SP 800-34, and the SRE book, and re-bases novelty on *formal semantics +
machine-readable representation + queryability/measurability*. The contribution
list (C1–C4) claims the model, algorithms, metrics, and governance/evaluation
design — never the bare distinction.

**R2.1.2 (major).** *The stated research question ("Can operational recovery be
represented as a graph…") is existential and unfalsifiable — any encoding is "a
graph."* → **Revision applied:** kept the question verbatim (it is the paper's
frame) but added an explicit decomposition note: it is operationalised into
RQ1–RQ4 (expressiveness, divergence, predictive utility, queryability/governance)
in the evaluation section, each with measurable outcomes.

**R2.1.3 (major).** *Sweeping empirical claims without support* ("systems rarely
know how to recover services"). → **Revision applied:** every incident claim in
the opening is now tied to a primary post-incident source (CrowdStrike PIR +
Microsoft KB, Meta engineering blog, GitLab postmortem, AWS Kinesis summary) and
the generalisation is delegated to systematic studies (Gunawi et al. SoCC'16,
Ghosh et al. SoCC'22, Uptime Institute) rather than asserted. Anthropomorphic
phrasing ("systems know") was removed from the body text.

**R2.1.4 (minor).** *CrowdStrike 2024 is an endpoint incident, not cloud-native —
using it as the lead example risks a scope objection.* → **Revision applied:**
kept (it is the clearest public case of restore-vs-recover divergence and of
recovery-only dependencies) but explicitly flagged in §2 as "outside the cloud
itself," used as evidence of the *pattern's* generality, not of cloud specifics.

**R2.1.5 (minor).** *Original contribution list mixed concepts, metrics, and
artifacts in one flat enumeration of six items mirroring the model's vocabulary.*
→ **Revision applied:** restructured into four contributions (model / algorithms
/ metrics / architecture+evaluation), with the six named concepts (Recovery
Graph, Recovery Dependency Edge, Recovery Readiness, Known-Good Evidence,
Recovery Confidence, Recovery Path) introduced inside C1–C2 where they belong.

**R2.1.6 (minor).** *A scope paragraph is needed: readers will assume the graph
claims to shorten outages by existing.* → **Revision applied:** added "Scope."
paragraph stating the model makes knowledge explicit, not actions correct, and
that outcome claims are deferred to the evaluation design.

---

## Section 2 — Motivation and problem analysis

**R2.2.1 (major).** *Causal overreach on incidents.* First draft said Meta "could
not recover for six hours because tooling was down" — the public report does not
quantify the tooling contribution. → **Revision applied:** all incident sentences
now state only what the primary source states ("internal tooling and even
physical-access systems depended on the failed network, materially slowing
recovery"); no invented durations or counterfactuals anywhere in §2.

**R2.2.2 (major).** *Anecdote selection bias: five pathologies cherry-picked from
famous outages.* → **Revision applied:** added an explicit bounding paragraph at
the end of §2 acknowledging that public reports over-represent large operators,
plus a forward reference to the threats-to-validity section and to RQ1/RQ2, which
test generality on independent systems. Systematic studies are cited alongside
each anecdote where available.

**R2.2.3 (major).** *P1–P5 must map onto the model or they are rhetorical.* A
reviewer will check whether every pathology has a counterpart mechanism.
→ **Revision applied:** added Table 1 (pathology → missing knowledge →
requirement R1–R6); §3 was subsequently written against R1–R6, and the
requirement labels are referenced when the corresponding mechanism is defined
(edge typology for R1, seeds/acyclicity for R2, evidence for R3, levels/gates
for R4, queries/metrics for R5/R6).

**R2.2.4 (minor).** *"The ability to recover is a claim that expires" — nice
phrase, but it must be cashed out formally,* otherwise it reads as marketing.
→ **Revision applied:** kept the sentence, and §3.6's evidence semantics
(validity horizons, freshness decay, readiness) implement exactly this; the
phrase recurs there as the informal reading of Definition 7.

**R2.2.5 (minor).** *GitLab example: say precisely "no mechanism yielded a working
restore when needed" rather than "all backups were broken,"* which the postmortem
does not literally say. → **Revision applied:** wording aligned to the
postmortem's own summary.

---
## Section 3 — The Recovery Graph model

**R2.3.1 (major).** *The total order 𝓛 = D<P<F<O is too coarse: real systems live in
partial orders of degraded operation (read-only mode, region-local mode).* →
**Revision applied:** added an explicit defence after Def. 2 — the mechanisms are
parametric in 𝓛 and require only a finite lattice; the partial-order extension is
discussed in §9 rather than silently ignored. "Functional" is defined to include
degraded serving so the coarse order is not vacuous.

**R2.3.2 (major).** *The confidence formula is ad hoc: why min over hard
prerequisites, why multiplicative, why linear decay, why ω_s = 1/2?* →
**Revision applied:** (i) min is now argued as a modelling commitment (hard
recovery is conjunctive; weakest-link), not an estimate; (ii) the decay function
is generalised to an admissible family (any non-increasing φ with φ=1 fresh, φ=0
at expiry), with linear as default and a sensitivity analysis added to the RQ3
design; (iii) ω_s is declared a parameter with default, not a constant of nature;
(iv) a boxed Remark states outright that C is *not* a probability, that no
independence assumptions are made, and that calibration is future work. This
pre-empts the strongest quantitative objection instead of hiding from it.

**R2.3.3 (major).** *Theorem 1 originally claimed "the system is recoverable iff…"
— the model cannot certify the world, only the declared knowledge.* →
**Revision applied:** theorem renamed **Modelled recoverability**; an explicit
paragraph after the proof sketch states the exposure (unmodelled dependencies
defeat certified plans) and ties it to the RDC/drift machinery, turning the
limitation into a measured quantity. Corollary "optimism of omission" was added
to make the direction of the error precise — under-modelling can only make RTO
estimates optimistic — and §5 mandates reporting RTO together with RDC.

**R2.3.4 (major).** *Concurrency semantics of guards under-specified: what if a
node regresses mid-run?* → **Revision applied:** Assumption A1 (monotone runs)
is now explicit in Def. 6: planned recovery assumes no regression; a regression
event ends the run and re-plans. This is the standard PERT-style idealisation
and is listed as a construct-validity threat in §7.

**R2.3.5 (minor).** *Why only two gate stages (start/complete)?* → **Revision
applied:** the action-graph construction shows start gates bind (v,P) and
complete gates bind (v,O); a footnote-level sentence notes per-level gating is a
strict generalisation obtainable by extending θ to 𝓛, omitted for economy.
[Kept in text via the parametric definition of 𝒜.]

**R2.3.6 (minor).** *Prop. 1 (incomparability) is trivially true — presenting it as
a theorem is grandstanding.* → **Revision applied:** demoted in rhetoric ("the
proposition is deliberately modest — an existence claim, provable by
exhibition") and the *empirical magnitude* (ρ) is delegated to RQ2 — which is
where the scientific content lives.

**R2.3.7 (minor).** *Consistency rules in the paper must match what the artifact
actually checks.* → **Revision applied:** rules renumbered so that C2, C4, C5, C6
correspond one-to-one with `rgkit.check()` outputs; §3.8 states exactly which
subset the reference implementation enforces.

## Section 4 — Queryable recovery

**R2.4.1 (major, self-caught).** *The first design used dominator trees
(Lengauer–Tarjan) for bottleneck analysis. This is incorrect under the model's
own semantics:* dominators characterise unavoidability when a node needs *some*
path from the root (or-semantics), but hard recovery edges compose
conjunctively — a node needs *all* its prerequisites — under which every closure
member is unavoidable and dominators degenerate. → **Revision applied:**
bottleneck analysis rebuilt on **blocking centrality** B(x) = total weight of
nodes whose hard closure contains x, which under conjunctive semantics coincides
with counterfactual impact; the text discloses the correction explicitly ("a
subtlety we ourselves initially got wrong") and identifies where dominators
*do* become correct (alternative recovery routes / and-or graphs), marked future
work. The self-correction is retained in print deliberately: reviewers trust
papers that show their working.

**R2.4.2 (minor).** *"Query algebra" overclaimed novelty — these are standard graph
operations.* → **Revision applied:** the section now claims *operations + a
mapping onto standard property-graph languages* (Cypher/GQL), citing the
languages rather than inventing one; novelty rests in the model, not the query
machinery.

**R2.4.3 (minor).** *The Cypher example must be well-formed against the declared
schema.* → **Revision applied:** schema (labels, REQUIRES properties,
EVIDENCED_BY) defined in §4.4 before the figure; the figure's query uses only
declared labels/properties; the fuller catalogue moved to the appendix.

## Section 5 — Metrics

**R2.5.1 (major).** *Weighted-mean indices (RRI, REC, RCS) mask tier-1 holes —
a governance metric that averages away the finding is worse than none.* →
**Revision applied:** the suite *specifies* reporting with tier-1 minima and
distributions ("never as a single scalar"), and the worked example is used in
the text as the cautionary instance (weighted RCS 0.35 vs tier-1 min ≈ 0).

**R2.5.2 (major).** *Graph density is a weak metric — density of a knowledge graph
is not a system property.* → **Revision applied:** δ and ρ are reclassified as
*descriptive statistics of the model* with an explicit "must not appear as
optimisation targets" sentence; their scientific role (quantifying Prop. 1 in
the field, anomaly detection for under-modelling) is stated. The metric is kept
because the specification mandates it, but its epistemic status is now honest.

**R2.5.3 (major).** *Metrics monotone in evidence invite evidence manufacturing.*
→ **Revision applied:** a failure-modes paragraph names the gaming vector for
each metric and pairs it with a mitigation that is part of the model
(provenance, separation of policy-setter from measured party, audit sampling,
attested-and-testable "irrelevant" classifications).

**R2.5.4 (minor).** *Each metric must be computable by the artifact or the paper
overclaims.* → **Revision applied:** verified — all six are implemented in
`rgkit.metrics()` and the worked-example table is generated by it.

## Section 6 — Reference architecture and governance

**R2.6.1 (major).** *The compliance mapping flirts with legal overclaim ("aligns
with DORA" reads as "makes you compliant").* → **Revision applied:** the claim is
now stated with precision: the graph "supports the production of evidence" for
regulatory obligations, followed by an explicit "we do not claim that deploying
it constitutes compliance with any instrument."

**R2.6.2 (major).** *Population story hand-waves the hard part: hardness/softness
of edges is counterfactual knowledge no harvester possesses.* → **Revision
applied:** the machines-propose/owners-attest division is made the centrepiece
of §6.1, with the explicit statement that classification encodes counterfactual
knowledge unobtainable from a healthy system, and RDC framed as the adjudication
backlog measure.

**R2.6.3 (minor).** *Who sets evidence policy matters more than the formulas — if
service owners set their own req(v), the metrics are self-grades.* → **Revision
applied:** "separation of claim and assessment" subsection added; policy
(req, TTLs, weights) belongs to a resilience function, not the measured party.

**R2.6.4 (minor).** *Self-reference: the graph is itself a recovery dependency.* →
**Revision applied:** made explicit ("self-reference, closed"): the platform must
satisfy its own C6 rule and be a seed. This also pre-empts the smart-aleck
reviewer question, which is precisely Reviewer #2's job to ask.

## Section 7 — Evaluation design and feasibility illustration

**R2.7.1 (major).** *A model paper with no empirical results is vulnerable at any
top venue; the design must be sharp enough to be criticised, and the paper must
not smuggle results in through the example.* → **Revision applied:** the section
opens by explicitly separating demonstrated (formalisation, implementation,
end-to-end computation) from measured (RQ1–RQ4, no results reported); the worked
example is labelled, twice, as a computed illustration on a declared instance
that "validates executability, not effectiveness"; durations are labelled
assumptions in both the text and the appendix.

**R2.7.2 (major).** *RQ3's baselines could straw-man: a weak runbook makes B2 look
good.* → **Revision applied:** B1 must be authored before graph modelling by
non-authors (contamination control); the closing sentences state exactly which
comparison licenses which conclusion (B0 → value of ordering knowledge; B1 →
value of formalisation) and that neither speaks to authoring cost.

**R2.7.3 (major).** *Duration calibration circularity: calibrating d and measuring
prediction error on the same runs would be invalid.* → **Revision applied:**
disjoint-runs requirement stated in §7.4 and repeated under internal validity.

**R2.7.4 (minor).** *Pre-registered expectations were missing — without them,
"design" is unfalsifiable posture.* → **Revision applied:** concrete
expectations added where defensible (κ ≥ 0.6 for RQ1; H2: ρ ≥ 0.5 for RQ2,
with the note that refutation would undercut the paper's own motivation) and
deliberately omitted where they would be numerology (no MAPE target is
promised for RQ3; error is reported, not guaranteed).

**R2.7.5 (minor).** *Worked-example numbers must be reproducible.* → **Revision
applied:** every number in §7.6, Table 4, and the two computed figures is
generated by `rgkit` in the artifact, including the pathological-variant cycle
report; the self-test asserts the formal properties claimed in §3.

## Section 8 — Related work

**R2.8.1 (major).** *CMDB and Terraform's resource graph are close enough that a
reviewer from industry will ask "isn't this just a CMDB with TTLs?"* →
**Revision applied:** both get dedicated treatment: Terraform's graph is
acknowledged as a true dependency DAG and delimited by semantics (resources vs.
capability levels, no evidence, ends at σ≥P); the CMDB is named "the closest
ancestor in spirit," its failure mode diagnosed (no executable semantics, no
expiring evidence → terminal drift), and the difference located on exactly
those axes. Answering the question in print beats hoping it isn't asked.

**R2.8.2 (major).** *Terminology collision with rollback-recovery's "recovery
line" could confuse distributed-systems readers.* → **Revision applied:**
explicit disambiguation sentence added (their recovery line is a consistent
cut; our recovery path is a prerequisite closure).

**R2.8.3 (minor).** *The positioning table's ●/◐/○ judgments must be defensible
row by row.* → **Revision applied:** every row's ◐ entries are justified in the
prose of the corresponding paragraph (e.g., BC standards get ● only on
governance; chaos gets ◐ on evidence because it produces but does not retain).

**R2.8.4 (minor).** *Chaos engineering should be positioned as symbiotic, not
competing — otherwise the paper alienates its most natural adopters.* →
**Revision applied:** "evidence producer for a store that has not existed;
the relationship is symbiotic, not competitive."

## Section 9 — Discussion; Section 10 — Conclusion

**R2.9.1 (major).** *The discussion must state when NOT to use the model;
universal applicability claims are a tell of immature work.* → **Revision
applied:** closing subsection "When not to use this" (small systems: the
checklist is the better technology), plus four explicitly numbered
expressiveness boundaries (total order, conjunctive-only, deterministic
durations, A1).

**R2.9.2 (minor).** *Security of the graph itself (recon value) unaddressed in
draft.* → **Revision applied:** paragraph added, including the genuine
availability-vs-confidentiality tension of the C6 offline copy.

**R2.9.3 (minor).** *Conclusion originally claimed "the Recovery Graph shortens
recovery" — unsupported by anything in the paper.* → **Revision applied:**
conclusion now enumerates what was shown vs. what remains open, and closes on
the falsifiable framing ("we invite the community to answer them
adversarially").

## Cross-cutting final pass

- Verified: every constant in the manuscript that derives from the worked
  example (19, 57, 15, 0.754, 0.867, 0.844, 0.922, 0.353, 0.002, 6 hops,
  130 min, critical chain, blocking top-3, the {k8s, wiki} cycle) matches
  `rgkit` output exactly.
- Verified: all six mandated concept names, all six mandated metrics, all five
  mandated figures (plus three additional), RQ1–RQ4, threats, and
  reproducibility are present.
- Verified: no dependence on, or mention of, any prior framework of the
  author's (standalone requirement).
