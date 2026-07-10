# `screen/`: the regulatory-surface fraud-measurement engine

A small, tested engine that treats **SEC regulatory structure as the schema** for detection.
Each place in SEC regulation where small-cap fraud leaves a fingerprint is one entry in a
declarative registry; the engine runs the extractable entries and emits per-year aggregate
prevalence. Output is aggregate and issuer-free by construction. The methodology is in
[`../docs/SCREEN.md`](../docs/SCREEN.md).

```
screen/
  registry.py          the breadth: SurfaceSpec per SEC rule/form/item (groups A-F)
  signal.py            SurfaceSpec + YearAggregate data types; INSTRUMENTS
  edgar.py             one shared throttled/cached EDGAR full-text-search client
  extractors.py        FtsExtractor: SurfaceSpec -> per-year YearAggregate (pure fn of the client)
  aggregate.py         run_all + to_csv (through the publication gate)
  publication_gate.py  refuses any issuer-level column; only aggregates leave the engine
  run.py               entry point -> data/aggregates/screen_registry.csv
```

## Run

```bash
python3 -m screen.run [contact_email]     # writes data/aggregates/screen_registry.csv
python3 -m pytest -q                      # the test suite (no network; recorded fixtures)
```

## Design

- **Registry-driven.** Adding a regulatory surface = adding one `SurfaceSpec` to
  `registry.py`. If it is measurable from full-text search, that is all it takes: the generic
  `FtsExtractor` picks it up. Structured-data and per-issuer surfaces are documented in the
  registry now and get their own extractors in later phases.
- **Extractors are pure functions of the client.** No network lives in an extractor, so the
  test suite drives them with a fake client and runs offline.
- **The wall is architecture, not a promise.** `YearAggregate` has no issuer field, and
  `publication_gate.py` re-checks every emitted header against a denylist of issuer-identifying
  columns. Issuer-level scoring, ranking, and validation are a later, private phase and never
  enter this public output.

## Scope (Phase 1+2)

In: the registry, the shared client, the FTS extractors for the surfaces measurable now
(Section 16 evasion, going concern, material weakness, toxic dilution / ATM, reverse-split
reset, 8-K restatement and delisting triggers), the publication gate, and the test suite.

Out (later phases, mostly private): the per-issuer signal store, per-issuer scoring, the
learned-score benchmark, and the size-controlled out-of-sample validation harness against
market outcomes (delisting / drawdown).
