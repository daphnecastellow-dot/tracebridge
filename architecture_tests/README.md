# Architecture stress test

This suite exercises the ten-repository research architecture as one system without
turning the tools into one application.

The scenario is fictional. It follows a disputed warning-note detail and bell-count
conflict through the current boundaries:

1. Sourceweave records where the detail first appears among the examined sources.
2. Threadtrace narrows an overstrong claim without deleting its earlier wording.
3. Contradiction Atlas keeps conflicting contemporaneous counts open.
4. Negative Space records a failed search without converting not-found into absence.
5. Evidence Ledger keeps documentary evidence, secondhand reporting, repetition,
   stance, independence, and derivation separate.
6. Claim Drift records wording changes without assigning motive.
7. Provenance Lens distinguishes direct support, synthesis, inference, and a visible
   missing provenance bridge.
8. Hingecheck challenges an explicit independence assumption and returns a recheck
   set without mutating downstream records.
9. Bridgekeeper preserves canonical state, ordinary changes, corrections, and an
   unresolved item with a reopening condition.
10. Tracebridge transports selected records plus complete Bridgekeeper and Hingecheck
    snapshots without inventing links or collapsing local namespaces.

The owning repositories are checked out at exact commits in CI. Those pins are tested
contracts, not floating compatibility promises. If a peer tool changes, update its pin
only after this suite passes against the new exact commit.

Run locally by setting the nine `TRACEBRIDGE_*_ROOT` environment variables used in
`test_end_to_end_research_flow.py`, then:

```bash
python -m unittest discover -s architecture_tests -v
```

The goal is not to make every tool share one schema. The goal is to prove that a
research path can cross tool boundaries without losing the distinctions each tool is
responsible for protecting.
