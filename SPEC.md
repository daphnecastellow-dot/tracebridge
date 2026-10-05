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
| Bridgekeeper | `other` (native handoff snapshot) | None inferred; native authority and supersession pointers remain in payload |
| Hingecheck | `other` (native assumption snapshot) | None inferred; native dependency and authority pointers remain in payload |

The mapping is deliberately permissive. A tool may emit `other` and preserve its native structure in `payload` rather than forcing a misleading shared classification.

## Native snapshot profile

`wrap-native` and `unwrap-native` use the existing format and schema unchanged.
They support `bridgekeeper/0.1` and `hingecheck/0.1` documents.

The packet origin identifies the native tool, the explicit caller-supplied project
namespace, and tool version `0.1`. One `other` record carries:

```json
{
  "native_format": "bridgekeeper/0.1",
  "native_document": {
    "format": "bridgekeeper/0.1",
    "project": "North Reach research",
    "bridge_id": "bridge-015"
  }
}
```

The abbreviated document above illustrates the envelope only. The actual payload
contains the entire input document, including all native fields and extension fields.
It is copied without modification. The record's `origin_id` is the snapshot ID, and
its bridge ID is `tb:<tool>:<escaped-project>:<escaped-snapshot-id>`.
Project and snapshot ID components are percent-encoded with no additional safe
characters, so embedded colons cannot collide with namespace separators.

Bridgekeeper's snapshot ID must equal its native `bridge_id`. Hingecheck requires a
caller-assigned snapshot ID because native assumption IDs identify assumptions, not
whole project snapshots. Changed snapshots must use new IDs. A merge of incompatible
snapshots under the same bridge ID fails under the existing collision rule.

Unwrapping selects an explicit record ID, checks the envelope format, native format,
tool identity, and Bridgekeeper identity when applicable, then returns a deep copy of
the native document. It restores JSON values rather than original file formatting.
Neither operation establishes native validity: run the owning tool's validator first.

### Preserved semantic boundaries

| Native structure | Transport treatment |
| --- | --- |
| Bridgekeeper `canonical` | Preserve explicit declarations and authority IDs; infer no canonicality |
| Bridgekeeper `changes` and `corrections` | Preserve separate lists, reasons, and before/after values |
| Bridgekeeper `unresolved` | Preserve questions, notes, and reopening conditions |
| Bridgekeeper `supersedes` | Preserve bridge IDs without deleting or synthesizing earlier handoffs |
| Both tools' `authorities` | Preserve full pointer objects and literal locations; do not resolve them |
| Hingecheck assumptions and `status_history` | Preserve statuses, reasons, and authority references |
| Hingecheck `dependents` | Preserve local IDs, kinds, dependency types, and notes without creating evidence records or changing conclusions |

The snapshot profile emits no shared links. A native `relies-on` or `invalid-if-false`
dependency is not a shared `supports` link. A declared correction is not a generic
text revision. Record-level projections may be designed later, but this profile
does not claim to implement them or automatically import native snapshots into a tool.

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
