# Working paper

This directory holds a short, **aggregate-only** working paper that the repository
reproduces end to end. Scope matches the rest of this repo: market-level,
statistical, and reproducible from public SEC data — **no individual issuer is
named or characterized.**

- [`PAPER.md`](PAPER.md) — the full draft (AI-assisted; for the author to revise into
  their own voice). Every number is verified against the committed aggregate data.
- [`OUTLINE.md`](OUTLINE.md) — section-by-section structure, with every results
  claim mapped to its exact figure (F1–F4) and number.
- [`abstract.md`](abstract.md) — draft abstract.

Every figure and number regenerates from committed aggregate data via
[`../pipeline/make_figures.py`](../pipeline/make_figures.py); the figure → script →
number map is in [`../docs/RESULTS.md`](../docs/RESULTS.md) and the construction
detail is in [`../docs/METHODOLOGY.md`](../docs/METHODOLOGY.md).

**Status:** full draft, not yet posted. Venue and timing are the author's decision
(SSRN is the natural home for empirical law-and-finance work). The references in
`PAPER.md` are real but should be verified and formatted to the author's citation style
before any public posting.
