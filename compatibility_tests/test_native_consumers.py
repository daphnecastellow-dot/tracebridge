"""Contracts against the actual owning tools, supplied through explicit checkouts."""

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tracebridge import merge_packets, save, unwrap_native, validate, wrap_native


ROOT = Path(__file__).resolve().parents[1]


def owner_module(tool):
    variable = f"TRACEBRIDGE_{tool.upper()}_ROOT"
    if variable not in os.environ:
        raise RuntimeError(f"set {variable} to the owning tool checkout before running compatibility tests")
    path = Path(os.environ[variable]) / f"{tool}.py"
    spec = importlib.util.spec_from_file_location(f"native_contract_{tool}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeConsumerContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridgekeeper = owner_module("bridgekeeper")
        cls.hingecheck = owner_module("hingecheck")

    def fixture(self, tool):
        return getattr(self, tool).load(ROOT / "examples/native" / f"{tool}.json")

    def cli(self, *args):
        result = subprocess.run([sys.executable, str(ROOT / "tracebridge.py"), *map(str, args)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bridgekeeper_consumes_cli_restored_handoff(self):
        original = self.fixture("bridgekeeper")
        with tempfile.TemporaryDirectory() as td:
            packet, restored = Path(td) / "packet.json", Path(td) / "handoff.json"
            self.cli("wrap-native", ROOT / "examples/native/bridgekeeper.json", "--project", "north-reach",
                     "--snapshot-id", "bridge-015", "-o", packet)
            self.cli("unwrap-native", packet, "--id", "tb:bridgekeeper:north-reach:bridge-015", "-o", restored)
            received = self.bridgekeeper.load(restored)
        before = copy.deepcopy(received)
        self.assertEqual(received, original)
        self.assertEqual(self.bridgekeeper.audit(received), self.bridgekeeper.audit(original))
        self.assertEqual(self.bridgekeeper.render_markdown(received), self.bridgekeeper.render_markdown(original))
        self.assertEqual(received, before)

    def test_hingecheck_consumes_cli_restored_assumptions(self):
        original = self.fixture("hingecheck")
        with tempfile.TemporaryDirectory() as td:
            packet, restored = Path(td) / "packet.json", Path(td) / "hinges.json"
            self.cli("wrap-native", ROOT / "examples/native/hingecheck.json", "--project", "north-reach",
                     "--snapshot-id", "hinges-001", "-o", packet)
            self.cli("unwrap-native", packet, "--id", "tb:hingecheck:north-reach:hinges-001", "-o", restored)
            received = self.hingecheck.load(restored)
        before = copy.deepcopy(received)
        self.assertEqual(received, original)
        self.assertEqual(self.hingecheck.audit(received), self.hingecheck.audit(original))
        self.assertEqual(self.hingecheck.impact(received, "H001"), original["assumptions"][0]["dependents"])
        self.assertEqual(self.hingecheck.render_impact(received, "H001"), self.hingecheck.render_impact(original, "H001"))
        self.assertEqual(received, before)

    def test_mixed_packet_keeps_native_authority_namespaces_separate(self):
        bridge, hinges = self.fixture("bridgekeeper"), self.fixture("hingecheck")
        a = wrap_native(bridge, "north-reach", "bridge-015")
        b = wrap_native(hinges, "north-reach", "hinges-001")
        with tempfile.TemporaryDirectory() as td:
            first, second, merged = (Path(td) / name for name in ("a.json", "b.json", "merged.json"))
            save(first, a)
            save(second, b)
            self.cli("merge", first, second, "-o", merged)
            packet = json.loads(merged.read_text())
        received_bridge = unwrap_native(packet, a["records"][0]["id"])
        received_hinges = unwrap_native(packet, b["records"][0]["id"])
        self.bridgekeeper.validate(received_bridge)
        self.hingecheck.validate(received_hinges)
        self.assertEqual(received_bridge, bridge)
        self.assertEqual(received_hinges, hinges)
        self.assertEqual(received_bridge["authorities"][0]["id"], "A001")
        self.assertEqual(received_hinges["authorities"][0]["id"], "A001")
        self.assertNotEqual(received_bridge["authorities"][0], received_hinges["authorities"][0])

    def test_transport_validity_does_not_bypass_native_validators(self):
        bridge, hinges = self.fixture("bridgekeeper"), self.fixture("hingecheck")
        bridge["canonical"][0]["authorities"] = ["unknown-authority"]
        hinges["assumptions"][0]["dependents"][0]["dependency"] = "invented-dependency"
        cases = [(bridge, "bridge-015", self.bridgekeeper, self.bridgekeeper.BridgekeeperError),
                 (hinges, "hinges-001", self.hingecheck, self.hingecheck.HingecheckError)]
        for document, snapshot_id, owner, error in cases:
            with self.subTest(snapshot_id=snapshot_id):
                packet = wrap_native(document, "north-reach", snapshot_id)
                validate(packet)
                recovered = unwrap_native(packet, packet["records"][0]["id"])
                self.assertEqual(recovered, document)
                with self.assertRaises(error):
                    owner.validate(recovered)


if __name__ == "__main__":
    unittest.main()
