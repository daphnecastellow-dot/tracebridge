import copy
import tempfile
import unittest
from pathlib import Path

from tracebridge import (
    TracebridgeError,
    add_link,
    add_record,
    load,
    merge_packets,
    new_packet,
    render_markdown,
    render_mermaid,
    save,
    validate,
)


class TracebridgeTests(unittest.TestCase):
    def test_record_preserves_local_and_bridge_ids(self):
        packet = new_packet("sourceweave", "north-reach", "0.1")
        add_record(
            packet,
            "tb:sourceweave:north-reach:D004",
            "D004",
            "claim",
            "The warning note appears in the 1978 book.",
            {"presence": "present"},
        )
        record = packet["records"][0]
        self.assertEqual(record["origin_id"], "D004")
        self.assertEqual(record["origin"]["tool"], "sourceweave")
        self.assertEqual(record["payload"]["presence"], "present")

    def test_links_require_existing_records(self):
        packet = new_packet("evidence-ledger", "north-reach")
        add_record(packet, "tb:ledger:north:C001", "C001", "claim")
        with self.assertRaises(TracebridgeError):
            add_link(packet, "tb:ledger:north:C001", "missing", "supports")

    def test_merge_preserves_different_origins(self):
        a = new_packet("sourceweave", "north-reach")
        add_record(a, "tb:sourceweave:north:D004", "D004", "claim", "Later warning-note appearance.")

        b = new_packet("evidence-ledger", "north-reach")
        add_record(b, "tb:ledger:north:E002", "E002", "evidence", "1978 book reports a warning note.")

        merged = merge_packets([a, b])
        origins = {(r["origin"]["tool"], r["origin"]["project"]) for r in merged["records"]}
        self.assertEqual(origins, {("sourceweave", "north-reach"), ("evidence-ledger", "north-reach")})
        self.assertEqual(len(merged["merged_from"]), 2)

    def test_merge_refuses_incompatible_record_collision(self):
        a = new_packet("sourceweave", "north-reach")
        add_record(a, "tb:shared:north:X001", "X001", "claim", "One wording.")

        b = copy.deepcopy(a)
        b["records"][0]["text"] = "Different wording."
        validate(b)

        with self.assertRaises(TracebridgeError):
            merge_packets([a, b])

    def test_round_trip_and_renderers(self):
        packet = new_packet("provenance-lens", "north-reach")
        add_record(packet, "tb:lens:north:E001", "E001", "evidence", "The early log lacks the warning.")
        add_record(packet, "tb:lens:north:U001", "U001", "writing-unit", "The checked early log lacks the warning.")
        add_link(packet, "tb:lens:north:E001", "tb:lens:north:U001", "supports", "Direct support bridge.")

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "packet.json"
            save(path, packet)
            loaded = load(path)

        self.assertIn("writing-unit", render_markdown(loaded))
        self.assertIn("supports", render_mermaid(loaded))


if __name__ == "__main__":
    unittest.main()
