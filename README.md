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

See [`SPEC.md`](SPEC.md).

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
