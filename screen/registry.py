"""The regulatory-surface registry: the breadth of SEC regulation, made computable.

Each entry is a SurfaceSpec tied to a specific rule/form/item. Surfaces with a non-empty
`fts_queries` are extractable now from public EDGAR full-text search (Phase 1+2); the rest are
documented here so the registry IS the full breadth, and are wired to structured-data or
per-issuer extractors in later phases. Adding regulatory coverage = adding a SurfaceSpec (and,
when extractable, an extractor), never a new pipeline.
"""
from .signal import SurfaceSpec

REGISTRY = [
    # --- A. Ownership & insider disclosure ---
    SurfaceSpec(
        id="sec16_evasion",
        instrument="A",
        citation="Exchange Act Section 16(a); Rule 16a-1; Schedule 13D/13G",
        description=(
            "Pre-funded warrant paired with a 'beneficial ownership limitation' blocker keeps a "
            "holder under the 5%/10% threshold, avoiding Form 3/4/5 and 13D beneficial-ownership "
            "disclosure. The paired structure routes dilution around insider reporting."),
        fts_queries={
            "prefunded_warrant": '"pre-funded warrant"',
            "ownership_blocker": '"beneficial ownership limitation"',
            "paired": '"pre-funded warrant" "beneficial ownership limitation"',
        },
    ),
    SurfaceSpec(
        id="insider_no_skin",
        instrument="A",
        citation="Exchange Act Section 16(a); Form 4",
        description=(
            "A capital raise with near-zero insider open-market Form 4 purchases: insiders take "
            "cash via warrants rather than buying equity. Needs per-issuer Form 4 parsing."),
        fts_queries={},  # per-issuer, deferred
    ),
    # --- B. Periodic disclosure quality ---
    SurfaceSpec(
        id="going_concern",
        instrument="B",
        citation="Reg S-X; PCAOB AS 2415 (going concern)",
        description="Auditor substantial-doubt / going-concern language: solvency distress.",
        fts_queries={"going_concern": '"substantial doubt" "going concern"'},
    ),
    SurfaceSpec(
        id="material_weakness",
        instrument="B",
        citation="SOX Section 404; Reg S-K Item 308; Item 9A",
        description="Disclosed material weakness in internal control over financial reporting.",
        # Specific to an actual disclosure; the bare phrase "material weakness" is 10-K
        # boilerplate (it appears in risk factors even absent a finding).
        fts_queries={"material_weakness": '"identified a material weakness"'},
    ),
    SurfaceSpec(
        id="resource_mismatch",
        instrument="B",
        citation="Reg S-X (financial statements); XBRL frames",
        description=(
            "A technology claim with R&D near zero and revenue near zero (the capability-signal "
            "test). Computed from XBRL, not FTS; see pipeline/informativeness.py."),
        fts_queries={},  # XBRL-based, handled by the informativeness path
    ),
    # --- C. Auditor & gatekeeper ---
    SurfaceSpec(
        id="auditor_churn",
        instrument="C",
        citation="Exchange Act Form 8-K Item 4.01 (changes in registrant's certifying accountant)",
        description=(
            "Frequency and direction of auditor changes and disclosed disagreements. Best from "
            "the structured 8-K item index; per-issuer, deferred."),
        fts_queries={},
    ),
    # --- D. Capital formation ---
    SurfaceSpec(
        id="toxic_dilution",
        instrument="D",
        citation="Securities Act; Forms S-1/S-3/424B; Reg D Form D",
        description=(
            "Variable-rate / death-spiral convertible language and at-the-market (ATM) facilities: "
            "structures that convert at a discount to a falling price, compounding dilution."),
        fts_queries={
            "atm_facility": '"at-the-market offering"',
            "variable_rate_convertible": '"variable rate convertible"',
        },
    ),
    SurfaceSpec(
        id="dilution_reset",
        instrument="D",
        citation="Exchange listing standards (bid-price compliance); 8-K",
        description="Reverse stock split: the post-dilution reset used to regain bid-price compliance.",
        fts_queries={"reverse_split": '"reverse stock split"'},
    ),
    SurfaceSpec(
        id="share_explosion",
        instrument="D",
        citation="Reg S-X; XBRL (shares outstanding)",
        description="Shares-outstanding growth multiple. Computed from XBRL per issuer; deferred.",
        fts_queries={},
    ),
    # --- E. Trigger events ---
    SurfaceSpec(
        id="restatement",
        instrument="E",
        citation="Form 8-K Item 4.02 (non-reliance on previously issued financials)",
        description=(
            "Non-reliance / restatement language: prior financials can no longer be relied upon. "
            "Measured in the 10-K to keep the filer denominator consistent with the other signals."),
        fts_queries={"non_reliance": '"should no longer be relied upon"'},
    ),
    SurfaceSpec(
        id="delist_notice",
        instrument="E",
        citation="Exchange listing standards; Form 8-K Item 3.01 (delisting / listing-rule failure)",
        description=(
            "An actual exchange deficiency the filer is working to cure. 'regain compliance' is "
            "specific to a live deficiency remediation, unlike generic 'listing' risk-factor text."),
        fts_queries={"regain_compliance": '"regain compliance"'},
    ),
    # --- F. Entity & market structure ---
    SurfaceSpec(
        id="theme_pivot",
        instrument="F",
        citation="Reg S-K Item 101 (business description); former-name history",
        description="Narrative rotation into a hot theme (AI/crypto/quantum). See F1-F5 for the AI cut.",
        fts_queries={},  # covered by the AI-label pipeline; other themes deferred
    ),
    SurfaceSpec(
        id="foreign_control",
        instrument="F",
        citation="Forms 20-F / 6-K; Reg S-K Item 101",
        description="Genuine foreign control and offshore counterparty structure. Per-issuer; deferred.",
        fts_queries={},
    ),
]


def extractable():
    """Surfaces that can be measured now from FTS alone (have queries)."""
    return [s for s in REGISTRY if s.fts_queries]


def by_id(surface_id):
    for s in REGISTRY:
        if s.id == surface_id:
            return s
    raise KeyError(surface_id)
