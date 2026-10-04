# Tracebridge handoff packet

**Demo:** North Reach warning-note chain

This fictional packet shows one record path crossing three independent tools without erasing where each record came from.

## Path

1. **Sourceweave** records that the warning-note detail is present in a 1978 folklore book.
2. **Evidence Ledger** carries that record forward as a secondhand report with unknown independence.
3. **Provenance Lens** uses the evidence to support a finished writing unit.

The records keep separate bridge IDs and separate native payloads. Tracebridge only transports the relationship.

## Visible chain

- `tb:sourceweave:north-reach:D004` **cites** `tb:sourceweave:north-reach:S002`
- `tb:evidence-ledger:north-reach:E002` **derives-from** `tb:sourceweave:north-reach:D004`
- `tb:evidence-ledger:north-reach:E002` **supports** `tb:provenance-lens:north-reach:U002`

No tool becomes authoritative merely because its record traveled farther.
