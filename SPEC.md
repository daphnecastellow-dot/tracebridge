# Tracebridge 0.1 packet specification

Tracebridge defines a small interchange surface. It deliberately leaves tool-specific semantics inside each tool.

## Packet

```json
{
  "format": "tracebridge/0.1",
  "created_at": "2026-10-04T22:00:00Z",
  "origin": {
    "tool": "sourceweave",
    "project": "north-reach",
    "tool_version": "0.1",
    "repository": "https://github.com/example/sourceweave"
  },
  "records": [],
  "links": []
}
```

Only `tool` and `project` are required inside `origin`.

## Record

```json
{
  "id": "tb:sourceweave:north-reach:D004",
  "origin_id": "D004",
  "kind": "claim",
  "text": "The warning note appears in the 1978 folklore book.",
  "origin": {
    "tool": "sourceweave",
    "project": "north-reach"
  },
  "payload": {}
}
```

Required fields:

- `id`
- `origin_id`
- `kind`
- `origin.tool`
- `origin.project`

`payload` is intentionally unconstrained JSON object data so a tool can preserve fields that have no shared Tracebridge equivalent.

## Link

```json
{
  "from": "tb:sourceweave:north-reach:D004",
  "to": "tb:sourceweave:north-reach:S002",
  "type": "cites",
  "note": "Detail is recorded in this source."
}
```

Links are directional. `related` may be used when direction has no stronger meaning.

## Current mappings

| Tool | Typical Tracebridge kinds | Typical links |
| --- | --- | --- |
| Threadtrace | `claim`, `source`, `note` | `revises`, `cites`, `derives-from` |
| Sourceweave | `source`, `claim`, `note` | `cites`, `derives-from`, `related` |
| Contradiction Atlas | `source`, `claim`, `conflict` | `contradicts`, `supports`, `related` |
| Negative Space | `hypothesis`, `check`, `source` | `checks`, `supports`, `contradicts` |
| Evidence Ledger | `claim`, `source`, `evidence` | `supports`, `contradicts`, `derives-from` |
| Provenance Lens | `source`, `evidence`, `writing-unit` | `supports`, `basis-for`, `derives-from` |
| Claim Drift | `source`, `version`, `transition` | `transforms`, `cites`, `related` |

The mapping is deliberately permissive. A tool may emit `other` and preserve its native structure in `payload` rather than forcing a misleading shared classification.

## Validation rules

A valid packet must:

1. use format `tracebridge/0.1`
2. provide packet origin tool and project
3. use unique record IDs
4. provide each record's local `origin_id`
5. use a recognized record kind
6. provide record origin tool and project
7. point every link at records that exist in the packet
8. use a recognized link type
9. avoid duplicate links with the same `from`, `to`, and `type`

## Merge rule

Packets may be merged when their records and links are compatible.

The same bridge ID may appear in more than one packet only when the complete record content is identical. A conflicting reuse of a bridge ID is an error, because silently choosing one version would destroy provenance.

Packet-level origins are preserved in `merged_from`; record-level origins remain attached to every record.

## Boundary rule

Tracebridge transports structure. It does not reinterpret it.

If one tool exports a field that another tool does not understand, that field belongs in `payload` and survives the handoff unchanged.
