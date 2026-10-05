# Tracebridge

**Version:** 0.1  
**Status:** experimental

Tracebridge is a small interoperability layer for passing **provenance-aware records between independent research tools**.

Its central rule:

> **Interoperability should preserve provenance, not erase boundaries.**

Tracebridge does not merge the tools into one application. It defines a compact handoff packet that lets one tool pass records to another while keeping the origin, local identifier, record type, and provenance relationships visible.

## What a packet contains

A Tracebridge packet records:

- the packet format and creation time
- the originating tool and project
- records with stable bridge IDs
- each record's original local ID
- a shared record kind
- optional human-readable text or label
- tool-specific payload preserved as JSON
- explicit links between records

Shared record kinds:

- `source`
- `claim`
- `evidence`
- `version`
- `conflict`
- `hypothesis`
- `check`
- `writing-unit`
- `transition`
- `note`
- `other`

Shared link types:

- `supports`
- `contradicts`
- `derives-from`
- `cites`
- `revises`
- `transforms`
- `basis-for`
- `checks`
- `related`

Tool-specific details remain inside `payload`; Tracebridge does not force every project into one ontology.

## Stable bridge IDs

A record keeps both:

- `origin_id`: the identifier used inside the source tool, such as `E003`
- `id`: a Tracebridge identifier such as `tb:sourceweave:north-reach:D004`

The bridge ID is an address across tools. The origin ID remains the local name inside the tool that created the record.

## Quick start

```bash
python tracebridge.py new packet.json \
  --tool sourceweave \
  --project north-reach

python tracebridge.py record packet.json \
  --id tb:sourceweave:north-reach:D004 \
  --origin-id D004 \
  --kind claim \
  --text "The warning note appears in the 1978 folklore book."

python tracebridge.py record packet.json \
  --id tb:sourceweave:north-reach:S002 \
  --origin-id S002 \
  --kind source \
  --text "1978 folklore book"

python tracebridge.py link packet.json \
  tb:sourceweave:north-reach:D004 \
  tb:sourceweave:north-reach:S002 \
  --type cites

python tracebridge.py validate packet.json
python tracebridge.py render packet.json -o handoff.md
python tracebridge.py graph packet.json -o handoff.mmd
```

## Merge without flattening

`merge` combines packets while preserving each record's origin metadata.

It refuses incompatible duplicate IDs. If two packets contain the same bridge ID with identical content, the duplicate is harmless. If the same bridge ID carries different content, Tracebridge stops and reports the collision.

```bash
python tracebridge.py merge sourceweave.json evidence-ledger.json -o combined.json
```

## Current tool mappings

Tracebridge v0.1 includes a documented mapping for:

- Threadtrace
- Sourceweave
- Contradiction Atlas
- Negative Space
- Evidence Ledger
- Provenance Lens
- Claim Drift
- Bridgekeeper (complete native continuity snapshots)
- Hingecheck (complete native assumption snapshots)

See [`SPEC.md`](SPEC.md).

## Native snapshots without semantic conversion

Bridgekeeper and Hingecheck can cross the existing `tracebridge/0.1` surface as an
`other` record containing their complete native JSON document. This is transport,
not a conversion to a shared state model. Unknown native fields survive too.

```bash
python tracebridge.py wrap-native examples/native/bridgekeeper.json \
  --project north-reach --snapshot-id bridge-015 -o continuity-packet.json
python tracebridge.py wrap-native examples/native/hingecheck.json \
  --project north-reach --snapshot-id hinges-001 -o assumptions-packet.json
python tracebridge.py merge continuity-packet.json assumptions-packet.json -o combined.json
python tracebridge.py unwrap-native combined.json \
  --id tb:bridgekeeper:north-reach:bridge-015 -o restored-handoff.json
```

The project argument is an explicit cross-tool namespace; it does not rewrite the
native project or title. Bridgekeeper uses its native `bridge_id` as the snapshot
ID. Hingecheck has no native snapshot ID, so the caller assigns a stable ID to that
specific snapshot and uses a new ID when its content changes. Merge refuses changed
content under a reused ID. IDs escape namespace separators.

Changes and corrections remain separate lists. Canonical declarations, unresolved
items, reopening conditions, supersession, authority locations, assumption status
history, and exact dependency types remain native payload data. No links or
downstream conclusions are inferred. These commands refuse to overwrite output files.

Validate the native input with its owning tool before wrapping it. Tracebridge checks
the supported native format and envelope identity, not native semantic validity.
Unwrapping restores the JSON value, not its original whitespace or byte formatting.
This first integration supports whole snapshots; automatic per-record conversion,
dependency resolution, and import into another tool are not implemented.

## Outputs

Tracebridge can produce:

- JSON handoff packets
- a Markdown packet report
- a Mermaid relationship graph
- structural validation results

## What Tracebridge does not do

Tracebridge is not a database.

It does not decide which tool is authoritative.

It does not resolve contradictions.

It does not assign truth scores.

It does not reinterpret a tool's private payload merely because another tool can read the packet.

It gives the instruments a compatible plug shape while leaving each instrument intact.

## Tests

```bash
python -m unittest discover -s tests -v
```

## License and reuse

**No reuse license has been granted.**

This public build is available for inspection and development by its maintainers. Do not assume that public visibility grants permission to copy, redistribute, modify, sell, incorporate, or relicense the code or documentation.

See [`COPYRIGHT.md`](COPYRIGHT.md).

## Working principle

Interoperability should preserve provenance, not erase boundaries.
