#!/usr/bin/env python3
"""Move provenance-aware records between independent tools without flattening them.\n\nThe bridge transports structure while preserving each record's native origin.\n"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

FORMAT = "tracebridge/0.1"
RECORD_KINDS = (
    "source", "claim", "evidence", "version", "conflict", "hypothesis",
    "check", "writing-unit", "transition", "note", "other",
)
LINK_TYPES = (
    "supports", "contradicts", "derives-from", "cites", "revises",
    "transforms", "basis-for", "checks", "related",
)


class TracebridgeError(Exception):
    pass


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_origin(tool: str, project: str, tool_version: str = "", repository: str = "") -> dict[str, str]:
    tool = tool.strip()
    project = project.strip()
    if not tool or not project:
        raise TracebridgeError("origin requires non-empty tool and project")
    origin = {"tool": tool, "project": project}
    if tool_version.strip():
        origin["tool_version"] = tool_version.strip()
    if repository.strip():
        origin["repository"] = repository.strip()
    return origin


def new_packet(tool: str, project: str, tool_version: str = "", repository: str = "") -> dict[str, Any]:
    return {
        "format": FORMAT,
        "created_at": now_utc(),
        "origin": clean_origin(tool, project, tool_version, repository),
        "records": [],
        "links": [],
    }


def find_record(packet: dict[str, Any], record_id: str) -> dict[str, Any]:
    for record in packet["records"]:
        if record["id"] == record_id:
            return record
    raise TracebridgeError(f"record not found: {record_id}")


def add_record(
    packet: dict[str, Any],
    record_id: str,
    origin_id: str,
    kind: str,
    text: str = "",
    payload: dict[str, Any] | None = None,
    origin_tool: str | None = None,
    origin_project: str | None = None,
) -> None:
    record_id = record_id.strip()
    origin_id = origin_id.strip()
    if not record_id or not origin_id:
        raise TracebridgeError("record id and origin id cannot be empty")
    if kind not in RECORD_KINDS:
        raise TracebridgeError(f"invalid record kind: {kind}")
    if any(r["id"] == record_id for r in packet["records"]):
        raise TracebridgeError(f"duplicate record id: {record_id}")

    if origin_tool or origin_project:
        origin = clean_origin(
            origin_tool or packet["origin"]["tool"],
            origin_project or packet["origin"]["project"],
        )
    else:
        origin = copy.deepcopy(packet["origin"])

    packet["records"].append({
        "id": record_id,
        "origin_id": origin_id,
        "kind": kind,
        "text": text,
        "origin": origin,
        "payload": copy.deepcopy(payload or {}),
    })


def add_link(packet: dict[str, Any], source: str, target: str, link_type: str, note: str = "") -> None:
    if link_type not in LINK_TYPES:
        raise TracebridgeError(f"invalid link type: {link_type}")
    find_record(packet, source)
    find_record(packet, target)
    key = (source, target, link_type)
    if any((x["from"], x["to"], x["type"]) == key for x in packet["links"]):
        raise TracebridgeError(f"duplicate link: {source} -> {target} ({link_type})")
    packet["links"].append({"from": source, "to": target, "type": link_type, "note": note})


def validate(packet: dict[str, Any]) -> None:
    if not isinstance(packet, dict) or packet.get("format") != FORMAT:
        raise TracebridgeError("unsupported packet format")
    if not isinstance(packet.get("created_at"), str) or not packet["created_at"].strip():
        raise TracebridgeError("packet requires created_at")

    origin = packet.get("origin")
    if not isinstance(origin, dict):
        raise TracebridgeError("packet requires origin")
    clean_origin(str(origin.get("tool", "")), str(origin.get("project", "")))

    if not isinstance(packet.get("records"), list) or not isinstance(packet.get("links"), list):
        raise TracebridgeError("packet requires records and links lists")

    ids: set[str] = set()
    for record in packet["records"]:
        if not isinstance(record, dict):
            raise TracebridgeError("record must be an object")
        rid = record.get("id")
        if not isinstance(rid, str) or not rid.strip() or rid in ids:
            raise TracebridgeError("invalid or duplicate record id")
        ids.add(rid)
        if not isinstance(record.get("origin_id"), str) or not record["origin_id"].strip():
            raise TracebridgeError(f"{rid}: missing origin_id")
        if record.get("kind") not in RECORD_KINDS:
            raise TracebridgeError(f"{rid}: invalid record kind")
        rorigin = record.get("origin")
        if not isinstance(rorigin, dict):
            raise TracebridgeError(f"{rid}: missing origin")
        clean_origin(str(rorigin.get("tool", "")), str(rorigin.get("project", "")))
        if not isinstance(record.get("payload"), dict):
            raise TracebridgeError(f"{rid}: payload must be an object")
        if "text" in record and not isinstance(record["text"], str):
            raise TracebridgeError(f"{rid}: text must be a string")

    seen_links: set[tuple[str, str, str]] = set()
    for link in packet["links"]:
        if not isinstance(link, dict):
            raise TracebridgeError("link must be an object")
        source = link.get("from")
        target = link.get("to")
        link_type = link.get("type")
        if source not in ids or target not in ids:
            raise TracebridgeError(f"link points to unknown record: {source} -> {target}")
        if link_type not in LINK_TYPES:
            raise TracebridgeError(f"invalid link type: {link_type}")
        key = (source, target, link_type)
        if key in seen_links:
            raise TracebridgeError(f"duplicate link: {source} -> {target} ({link_type})")
        seen_links.add(key)


def load(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise TracebridgeError(f"packet not found: {p}")
    try:
        packet = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TracebridgeError(f"invalid JSON: {exc}") from exc
    validate(packet)
    return packet


def save(path: str | Path, packet: dict[str, Any]) -> None:
    validate(packet)
    Path(path).write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def merge_packets(packets: list[dict[str, Any]]) -> dict[str, Any]:
    if not packets:
        raise TracebridgeError("merge requires at least one packet")
    for packet in packets:
        validate(packet)

    merged = new_packet("tracebridge", "merged")
    merged["merged_from"] = []
    origins_seen: set[str] = set()
    records: dict[str, dict[str, Any]] = {}
    links: dict[tuple[str, str, str], dict[str, Any]] = {}

    for packet in packets:
        origin_key = json.dumps(packet["origin"], sort_keys=True, ensure_ascii=False)
        if origin_key not in origins_seen:
            merged["merged_from"].append(copy.deepcopy(packet["origin"]))
            origins_seen.add(origin_key)

        for record in packet["records"]:
            existing = records.get(record["id"])
            if existing is None:
                cloned = copy.deepcopy(record)
                records[record["id"]] = cloned
                merged["records"].append(cloned)
            elif existing != record:
                raise TracebridgeError(f"record collision with incompatible content: {record['id']}")

        for link in packet["links"]:
            key = (link["from"], link["to"], link["type"])
            existing = links.get(key)
            if existing is None:
                cloned = copy.deepcopy(link)
                links[key] = cloned
                merged["links"].append(cloned)
            elif existing != link:
                raise TracebridgeError(
                    f"link collision with incompatible content: {link['from']} -> {link['to']} ({link['type']})"
                )

    validate(merged)
    return merged


def render_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Tracebridge handoff packet",
        "",
        f"Format: {packet['format']}",
        f"Origin: {packet['origin']['tool']} / {packet['origin']['project']}",
        f"Created: {packet['created_at']}",
        "",
    ]

    if packet.get("merged_from"):
        lines += ["## Merged from", ""]
        for origin in packet["merged_from"]:
            lines.append(f"- {origin['tool']} / {origin['project']}")
        lines.append("")

    lines += ["## Records", ""]
    if not packet["records"]:
        lines += ["_No records._", ""]
    for record in packet["records"]:
        lines += [
            f"### {record['id']}",
            "",
            f"- Kind: {record['kind']}",
            f"- Origin: {record['origin']['tool']} / {record['origin']['project']} / {record['origin_id']}",
        ]
        if record.get("text"):
            lines += ["", record["text"]]
        if record.get("payload"):
            lines += ["", "Native payload:", ""]
            for line in json.dumps(record["payload"], indent=2, ensure_ascii=False).splitlines():
                lines.append("    " + line)
        lines.append("")

    lines += ["## Links", ""]
    if not packet["links"]:
        lines += ["_No links._", ""]
    else:
        for link in packet["links"]:
            note = f" - {link['note']}" if link.get("note") else ""
            lines.append(f"- {link['from']} --{link['type']}--> {link['to']}{note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_mermaid(packet: dict[str, Any]) -> str:
    lines = ["flowchart LR"]
    node_for: dict[str, str] = {}
    for index, record in enumerate(packet["records"], start=1):
        node = f"N{index:03d}"
        node_for[record["id"]] = node
        label_text = record.get("text") or record["origin_id"]
        label = f"{record['kind']} · {label_text}".replace('"', "'").replace("\n", " ")
        lines.append(f'  {node}["{label}"]')
    for link in packet["links"]:
        lines.append(f'  {node_for[link["from"]]} -->|"{link["type"]}"| {node_for[link["to"]]}')
    return "\n".join(lines) + "\n"


def summary(packet: dict[str, Any]) -> str:
    origins = {(r["origin"]["tool"], r["origin"]["project"]) for r in packet["records"]}
    return (
        f"{len(packet['records'])} record(s), {len(packet['links'])} link(s), "
        f"{len(origins)} record origin(s)"
    )


def parse_payload(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise TracebridgeError(f"invalid payload JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise TracebridgeError("payload JSON must be an object")
    return parsed


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tracebridge",
        description="Pass provenance-aware records between independent research tools.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    q = sub.add_parser("new")
    q.add_argument("file")
    q.add_argument("--tool", required=True)
    q.add_argument("--project", required=True)
    q.add_argument("--tool-version", default="")
    q.add_argument("--repository", default="")

    q = sub.add_parser("record")
    q.add_argument("file")
    q.add_argument("--id", required=True)
    q.add_argument("--origin-id", required=True)
    q.add_argument("--kind", choices=RECORD_KINDS, required=True)
    q.add_argument("--text", default="")
    q.add_argument("--payload-json", default="{}")
    q.add_argument("--origin-tool")
    q.add_argument("--origin-project")

    q = sub.add_parser("link")
    q.add_argument("file")
    q.add_argument("source")
    q.add_argument("target")
    q.add_argument("--type", choices=LINK_TYPES, required=True)
    q.add_argument("--note", default="")

    for name in ("show", "validate"):
        q = sub.add_parser(name)
        q.add_argument("file")

    for name in ("render", "graph"):
        q = sub.add_parser(name)
        q.add_argument("file")
        q.add_argument("-o", "--output")

    q = sub.add_parser("merge")
    q.add_argument("files", nargs="+")
    q.add_argument("-o", "--output", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "new":
            if Path(args.file).exists():
                raise TracebridgeError(f"refusing to overwrite existing file: {args.file}")
            save(args.file, new_packet(args.tool, args.project, args.tool_version, args.repository))
            print(f"created {args.file}")
            return 0

        if args.command == "merge":
            packets = [load(path) for path in args.files]
            save(args.output, merge_packets(packets))
            print(args.output)
            return 0

        packet = load(args.file)
        if args.command == "record":
            add_record(
                packet,
                args.id,
                args.origin_id,
                args.kind,
                args.text,
                parse_payload(args.payload_json),
                args.origin_tool,
                args.origin_project,
            )
            save(args.file, packet)
            print(args.id)
        elif args.command == "link":
            add_link(packet, args.source, args.target, args.type, args.note)
            save(args.file, packet)
            print(f"{args.source} -> {args.target}")
        elif args.command == "show":
            print(summary(packet))
        elif args.command == "validate":
            print(f"ok: {args.file}")
        else:
            output = {"render": render_markdown, "graph": render_mermaid}[args.command](packet)
            if args.output:
                Path(args.output).write_text(output, encoding="utf-8")
                print(args.output)
            else:
                print(output, end="")
        return 0
    except TracebridgeError as exc:
        print(f"tracebridge: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
