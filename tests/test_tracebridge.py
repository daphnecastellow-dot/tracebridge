import copy
import json
import subprocess
import sys
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
    wrap_native,
    unwrap_native,
)


class TracebridgeTests(unittest.TestCase):
    def native(self, tool):
        return json.loads((Path(__file__).resolve().parents[1] / "examples" / "native" / f"{tool}.json").read_text())

    def test_bridgekeeper_round_trip_preserves_distinct_state(self):
        native = self.native("bridgekeeper")
        native["future_field"] = {"opaque": [False, None, "α"]}
        original = copy.deepcopy(native)
        packet = wrap_native(native, "north-reach", native["bridge_id"])
        native["canonical"][0]["value"] = "changed outside packet"
        recovered = unwrap_native(packet, packet["records"][0]["id"])
        self.assertEqual(recovered, original)
        self.assertNotEqual(recovered["changes"], recovered["corrections"])
        self.assertEqual(recovered["supersedes"], ["bridge-014"])
        self.assertTrue(recovered["unresolved"][0]["reopen_when"])
        recovered["canonical"].clear()
        self.assertEqual(unwrap_native(packet, packet["records"][0]["id"]), original)

    def test_hingecheck_handoff_does_not_mutate_dependents(self):
        native = self.native("hingecheck")
        original = copy.deepcopy(native)
        packet = wrap_native(native, "north-reach", "hinges-001")
        recovered = unwrap_native(packet, packet["records"][0]["id"])
        self.assertEqual(native, original)
        self.assertEqual(recovered, original)
        self.assertEqual(recovered["assumptions"][0]["status"], "challenged")
        self.assertEqual(packet["links"], [])

    def test_native_snapshots_merge_and_keep_origin_and_collisions(self):
        bridge = self.native("bridgekeeper")
        hinge = self.native("hingecheck")
        a = wrap_native(bridge, "north-reach", bridge["bridge_id"])
        b = wrap_native(hinge, "north-reach", "hinges-001")
        merged = merge_packets([a, b])
        self.assertEqual(unwrap_native(merged, a["records"][0]["id"]), bridge)
        self.assertEqual(unwrap_native(merged, b["records"][0]["id"]), hinge)
        hinge["assumptions"][0]["status"] = "invalidated"
        with self.assertRaises(TracebridgeError):
            merge_packets([b, wrap_native(hinge, "north-reach", "hinges-001")])
        later = wrap_native(hinge, "north-reach", "hinges-002")
        self.assertEqual(len(merge_packets([b, later])["records"]), 2)

    def test_snapshot_addresses_escape_namespace_separators(self):
        native = self.native("hingecheck")
        a = wrap_native(native, "a:b", "c")
        b = wrap_native(native, "a", "b:c")
        self.assertNotEqual(a["records"][0]["id"], b["records"][0]["id"])

    def test_native_envelope_rejects_unsupported_or_mismatched_identity(self):
        for native in ({"format": "unknown/0.1"}, {"format": []}, []):
            with self.assertRaises(TracebridgeError):
                wrap_native(native, "north", "snapshot")
        with self.assertRaises(TracebridgeError):
            wrap_native(self.native("bridgekeeper"), "north", "wrong-bridge")
        with self.assertRaises(TracebridgeError):
            wrap_native(self.native("hingecheck"), "north", " ")
        packet = wrap_native(self.native("hingecheck"), "north", "snapshot")
        packet["records"][0]["payload"]["native_format"] = "bridgekeeper/0.1"
        with self.assertRaises(TracebridgeError):
            unwrap_native(packet, packet["records"][0]["id"])

    def test_native_cli_round_trip_and_overwrite_refusal(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            packet_path, restored = Path(td) / "packet.json", Path(td) / "restored.json"
            command = [sys.executable, str(root / "tracebridge.py"), "wrap-native",
                       str(root / "examples/native/hingecheck.json"), "--project", "north-reach",
                       "--snapshot-id", "hinges-001", "-o", str(packet_path)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            before = packet_path.read_bytes()
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual(packet_path.read_bytes(), before)
            record_id = load(packet_path)["records"][0]["id"]
            restore = [sys.executable, str(root / "tracebridge.py"), "unwrap-native", str(packet_path),
                       "--id", record_id, "-o", str(restored)]
            self.assertEqual(subprocess.run(restore, capture_output=True).returncode, 0)
            self.assertEqual(json.loads(restored.read_text()), self.native("hingecheck"))
            self.assertEqual(subprocess.run(restore, capture_output=True).returncode, 2)

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
