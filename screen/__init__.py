"""screen: a regulatory-surface fraud-measurement engine.

The registry (registry.py) encodes SEC regulatory surfaces where small-cap fraud leaves a
fingerprint. Extractors (extractors.py) turn each extractable surface into per-year aggregate
prevalence via one shared EDGAR client (edgar.py). The publication gate (publication_gate.py)
guarantees only aggregate, issuer-free output leaves the engine. See screen/README.md and
docs/SCREEN.md for the method.
"""
