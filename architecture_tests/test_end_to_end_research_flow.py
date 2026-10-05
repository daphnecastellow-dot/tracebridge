"""End-to-end stress test for the ten-tool research architecture.

The case is fictional. The test exists to protect boundaries between tools, not to
establish facts about any real event.
"""

import copy
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

from tracebridge import (
    add_record,
    load,
    merge_packets,
    new_packet,
    save,
    unwrap_native,
    validate,
    wrap_native,
)


ROOT = Path(__file__).resolve().parents[1]

PEERS = {
    "threadtrace": ("TRACEBRIDGE_THREADTRACE_ROOT", "threadtrace.py"),
    "sourceweave": ("TRACEBRIDGE_SOURCEWEAVE_ROOT", "sourceweave.py"),
    "contradiction_atlas": ("TRACEBRIDGE_CONTRADICTION_ATLAS_ROOT", "contradiction_atlas.py"),
    "negative_space": ("TRACEBRIDGE_NEGATIVE_SPACE_ROOT", "negative_space.py"),
    "evidence_ledger": ("TRACEBRIDGE_EVIDENCE_LEDGER_ROOT", "evidence_ledger.py"),
    "provenance_lens": ("TRACEBRIDGE_PROVENANCE_LENS_ROOT", "provenance_lens.py"),
    "claim_drift": ("TRACEBRIDGE_CLAIM_DRIFT_ROOT", "claim_drift.py"),
    "bridgekeeper": ("TRACEBRIDGE_BRIDGEKEEPER_ROOT", "bridgekeeper.py"),
    "hingecheck": ("TRACEBRIDGE_HINGECHECK_ROOT", "hingecheck.py"),
}


def owner_module(name):
    variable, filename = PEERS[name]
    if variable not in os.environ:
        raise RuntimeError(f"set {variable} to the owning tool checkout before running architecture tests")
    path = Path(os.environ[variable]) / filename
    spec = importlib.util.spec_from_file_location(f"architecture_contract_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EndToEndResearchFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name in PEERS:
            setattr(cls, name, owner_module(name))

    def build_case(self):
        tt = self.threadtrace
        sw = self.sourceweave
        ca = self.contradiction_atlas
        ns = self.negative_space
        el = self.evidence_ledger
        pl = self.provenance_lens
        cd = self.claim_drift
        bk = self.bridgekeeper
        hc = self.hingecheck

        lineage = sw.new_project("North Reach warning-note lineage")
        sw_log = sw.add_source(lineage, "1904 station log", "primary", "1904-11-03")
        sw_news = sw.add_source(lineage, "1904 newspaper", "contemporary-report", "1904-11-04")
        sw_book = sw.add_source(lineage, "1978 folklore book", "later-retelling", "1978")
        sw.add_relation(lineage, sw_book, sw_news, "derived-from")
        note_detail = sw.add_detail(lineage, "A warning note was left.")
        sw.observe(lineage, sw_log, note_detail, "absent", "Checked log entry contains no warning-note reference.")
        sw.observe(lineage, sw_news, note_detail, "absent", "Checked contemporary report contains no warning-note reference.")
        sw.observe(lineage, sw_book, note_detail, "present", "Later book reports a warning note.")

        trail = tt.new_trail("North Reach claim trail")
        trail_id = tt.add_item(
            trail,
            "A warning note existed before the event.",
            "inference",
            source="1978 folklore book",
        )
        tt.revise_item(
            trail,
            trail_id,
            "The 1978 folklore book reports that a warning note was left.",
            "The later-source wording is documented; historical existence remains unresolved.",
            status="documented",
        )
        tt.add_source(trail, trail_id, "1978 folklore book")

        conflicts = ca.new_project("North Reach bell-count conflict")
        ca_log = ca.add_source(conflicts, "1904 station log", "primary", "1904-11-03")
        ca_news = ca.add_source(conflicts, "1904 newspaper", "contemporary-report", "1904-11-04")
        c_log = ca.add_claim(conflicts, "The station log records three bell rings.", [ca_log])
        c_news = ca.add_claim(conflicts, "The newspaper reports two bell rings.", [ca_news])
        conflict_id = ca.add_conflict(conflicts, c_log, c_news, "count", "The checked contemporaneous records disagree.")

        absence = ns.new_project("North Reach negative-space check")
        hypothesis_id = ns.add_hypothesis(absence, "A contemporaneous warning-note record exists.")
        check_id = ns.add_check(
            absence,
            hypothesis_id,
            "1904 station archive",
            "catalog and page review",
            "contemporaneous warning-note record",
            "not-found",
            "No matching warning-note record was found in the reviewed material.",
        )

        ledger = el.new_project("North Reach evidence ledger")
        ledger_claim = el.add_claim(ledger, "A warning note was left before the event.")
        el_log = el.add_source(ledger, "1904 station log", "primary", "1904-11-03")
        el_book = el.add_source(ledger, "1978 folklore book", "later-retelling", "1978")
        e_log = el.add_entry(
            ledger,
            ledger_claim,
            "The checked station log contains no warning-note reference.",
            "documentary-record",
            "contradicts",
            "independent",
            [el_log],
        )
        e_book = el.add_entry(
            ledger,
            ledger_claim,
            "The 1978 folklore book reports a warning note.",
            "secondhand-report",
            "supports",
            "unknown",
            [el_book],
        )
        e_repeat = el.add_entry(
            ledger,
            ledger_claim,
            "A later article repeats the folklore book's warning-note account.",
            "repetition",
            "supports",
            "dependent",
            derived_from=[e_book],
        )

        drift = cd.new_project("North Reach wording drift")
        cd_news = cd.add_source(drift, "1904 newspaper", "contemporary-report", "1904-11-04")
        cd_book = cd.add_source(drift, "1978 folklore book", "later-retelling", "1978")
        v_early = cd.add_version(drift, "A bell was heard before dawn.", [cd_news])
        v_late = cd.add_version(drift, "A warning bell rang three times before dawn.", [cd_book])
        transition_id = cd.add_drift(
            drift,
            v_early,
            v_late,
            "addition",
            "bell",
            "warning bell",
            "Warning framing appears in the later wording.",
        )
        cd.add_drift(
            drift,
            v_early,
            v_late,
            "quantity-shift",
            "",
            "three times",
            "A specific count appears in the later wording.",
        )

        lens = pl.new_project(
            "North Reach finished reasoning",
            "The 1978 book reports a warning note. Checked contemporaneous records do not mention one. "
            "The detail may have entered the currently examined lineage later.",
        )
        pl_log = pl.add_source(lens, "1904 station log", "primary", "1904-11-03")
        pl_news = pl.add_source(lens, "1904 newspaper", "contemporary-report", "1904-11-04")
        pl_book = pl.add_source(lens, "1978 folklore book", "later-retelling", "1978")
        pe_book = pl.add_evidence(lens, "The 1978 folklore book reports a warning note.", [pl_book])
        pe_log = pl.add_evidence(lens, "The checked station log contains no warning-note reference.", [pl_log])
        pe_news = pl.add_evidence(lens, "The checked newspaper contains no warning-note reference.", [pl_news])
        u_book = pl.add_unit(lens, "The 1978 folklore book reports a warning note.", "direct-support", [pe_book])
        u_early = pl.add_unit(
            lens,
            "The checked contemporaneous records do not mention a warning note.",
            "synthesis",
            [pe_log, pe_news],
        )
        u_inference = pl.add_unit(
            lens,
            "The warning-note detail may have entered the currently examined lineage later.",
            "inference",
            basis_units=[u_book, u_early],
        )
        u_gap = pl.add_unit(
            lens,
            "The warning note definitely existed in 1904.",
            "missing-bridge",
        )

        hinges = hc.new_project("North Reach assumption dependencies")
        hc.add_authority(
            hinges,
            "A001",
            "Sourceweave lineage relation",
            f"sourceweave:north-reach:{sw_book}",
            "tool-record",
        )
        hinge_id = hc.add_assumption(
            hinges,
            "The 1978 folklore book is independent of the 1904 newspaper.",
            "uncertain",
            ["A001"],
            "Recheck when the source-lineage relationship changes.",
        )
        hc.add_dependent(
            hinges,
            hinge_id,
            e_book,
            "evidence",
            "relies-on",
            "Independence affects whether the later report counts as separate corroboration.",
        )
        hc.add_dependent(
            hinges,
            hinge_id,
            u_inference,
            "writing-unit",
            "weakens-if-false",
            "The finished wording depends partly on source independence.",
        )

        handoff = bk.new_handoff("North Reach stress case", "bridge-e2e-001")
        bk.add_authority(
            handoff,
            "A001",
            "Provenance Lens inference",
            f"provenance-lens:north-reach:{u_inference}",
            "tool-record",
        )
        bk.add_authority(
            handoff,
            "A002",
            "Sourceweave lineage detail",
            f"sourceweave:north-reach:{note_detail}",
            "tool-record",
        )
        bk.set_canonical(
            handoff,
            "warning-note-current-state",
            "later-source report; contemporaneous support not found in checked records",
            ["A001", "A002"],
            "Current project wording preserves the support boundary.",
        )
        bk.add_transition(
            handoff,
            "changes",
            "independence-assessment",
            "unknown",
            "challenged",
            "A source-lineage relationship was recorded.",
            ["A002"],
        )
        bk.add_transition(
            handoff,
            "corrections",
            "station-log-date",
            "1904-11-04",
            "1904-11-03",
            "A transcription date was corrected.",
            ["A002"],
        )
        bk.add_unresolved(
            handoff,
            "warning-note-existence",
            "Historical existence of the warning note remains unresolved.",
            reopen_when="A contemporaneous source documenting the note is found.",
        )

        return {
            "trail": trail,
            "trail_id": trail_id,
            "lineage": lineage,
            "sw_book": sw_book,
            "note_detail": note_detail,
            "conflicts": conflicts,
            "conflict_id": conflict_id,
            "absence": absence,
            "hypothesis_id": hypothesis_id,
            "check_id": check_id,
            "ledger": ledger,
            "e_book": e_book,
            "e_repeat": e_repeat,
            "drift": drift,
            "transition_id": transition_id,
            "lens": lens,
            "u_inference": u_inference,
            "u_gap": u_gap,
            "hinges": hinges,
            "hinge_id": hinge_id,
            "handoff": handoff,
        }

    def test_research_states_remain_distinct(self):
        case = self.build_case()

        first = self.sourceweave.first_appearance(case["lineage"], case["note_detail"])
        self.assertEqual(first["id"], case["sw_book"])

        trail_item = case["trail"]["items"][0]
        self.assertEqual(trail_item["status"], "documented")
        self.assertEqual(trail_item["history"][1]["previous_claim"], "A warning note existed before the event.")

        conflict = case["conflicts"]["conflicts"][0]
        self.assertEqual(conflict["id"], case["conflict_id"])
        self.assertEqual(conflict["status"], "open")

        hypothesis = case["absence"]["hypotheses"][0]
        self.assertEqual(hypothesis["status"], "open")
        self.assertEqual(case["absence"]["checks"][0]["outcome"], "not-found")

        repeated = next(item for item in case["ledger"]["entries"] if item["id"] == case["e_repeat"])
        self.assertEqual(repeated["independence"], "dependent")
        self.assertEqual(repeated["derived_from"], [case["e_book"]])

        transition = case["drift"]["transitions"][0]
        self.assertEqual(transition["id"], case["transition_id"])
        self.assertEqual({change["type"] for change in transition["changes"]}, {"addition", "quantity-shift"})

    def test_finished_reasoning_keeps_inference_and_missing_bridge_visible(self):
        case = self.build_case()
        findings = self.provenance_lens.audit(case["lens"])
        self.assertTrue(any("missing-bridge" in finding for finding in findings))
        inference = next(unit for unit in case["lens"]["units"] if unit["id"] == case["u_inference"])
        gap = next(unit for unit in case["lens"]["units"] if unit["id"] == case["u_gap"])
        self.assertEqual(inference["kind"], "inference")
        self.assertEqual(gap["kind"], "missing-bridge")

    def test_challenged_hinge_surfaces_impact_without_mutating_other_tools(self):
        case = self.build_case()
        ledger_before = copy.deepcopy(case["ledger"])
        lens_before = copy.deepcopy(case["lens"])

        self.hingecheck.change_status(
            case["hinges"],
            case["hinge_id"],
            "challenged",
            "The later book is recorded as derived from the newspaper.",
            ["A001"],
        )
        impacted = self.hingecheck.impact(case["hinges"], case["hinge_id"])

        self.assertEqual({item["id"] for item in impacted}, {case["e_book"], case["u_inference"]})
        self.assertEqual(case["hinges"]["assumptions"][0]["status"], "challenged")
        self.assertEqual(case["ledger"], ledger_before)
        self.assertEqual(case["lens"], lens_before)

    def packet_for(self, tool, origin_id, kind, text_value, native_record):
        packet = new_packet(tool, "north-reach", "0.1")
        add_record(
            packet,
            f"tb:{tool}:north-reach:{origin_id}",
            origin_id,
            kind,
            text_value,
            {"native_record": copy.deepcopy(native_record)},
        )
        return packet

    def test_tracebridge_round_trip_preserves_boundaries_across_all_peer_tools(self):
        case = self.build_case()

        self.bridgekeeper.validate(case["handoff"])
        self.hingecheck.validate(case["hinges"])

        packets = [
            self.packet_for(
                "threadtrace",
                case["trail_id"],
                "claim",
                case["trail"]["items"][0]["claim"],
                case["trail"]["items"][0],
            ),
            self.packet_for(
                "sourceweave",
                case["note_detail"],
                "claim",
                "A warning note was left.",
                next(item for item in case["lineage"]["details"] if item["id"] == case["note_detail"]),
            ),
            self.packet_for(
                "contradiction-atlas",
                case["conflict_id"],
                "conflict",
                "Contemporaneous bell-count records disagree.",
                case["conflicts"]["conflicts"][0],
            ),
            self.packet_for(
                "negative-space",
                case["check_id"],
                "check",
                "A contemporaneous warning-note record was not found in the reviewed material.",
                case["absence"]["checks"][0],
            ),
            self.packet_for(
                "evidence-ledger",
                case["e_book"],
                "evidence",
                "The 1978 folklore book reports a warning note.",
                next(item for item in case["ledger"]["entries"] if item["id"] == case["e_book"]),
            ),
            self.packet_for(
                "provenance-lens",
                case["u_inference"],
                "writing-unit",
                "The warning-note detail may have entered the currently examined lineage later.",
                next(item for item in case["lens"]["units"] if item["id"] == case["u_inference"]),
            ),
            self.packet_for(
                "claim-drift",
                case["transition_id"],
                "transition",
                "Later wording adds warning framing and a count.",
                case["drift"]["transitions"][0],
            ),
        ]

        bridge_packet = wrap_native(case["handoff"], "north-reach", case["handoff"]["bridge_id"])
        hinge_packet = wrap_native(case["hinges"], "north-reach", "hinges-e2e-001")
        packets.extend([bridge_packet, hinge_packet])

        merged = merge_packets(packets)
        validate(merged)

        expected_origins = {
            "threadtrace",
            "sourceweave",
            "contradiction-atlas",
            "negative-space",
            "evidence-ledger",
            "provenance-lens",
            "claim-drift",
            "bridgekeeper",
            "hingecheck",
        }
        self.assertEqual({item["origin"]["tool"] for item in merged["records"]}, expected_origins)
        self.assertEqual(len(merged["merged_from"]), len(expected_origins))
        self.assertEqual(merged["links"], [])

        same_local_id = [item for item in merged["records"] if item["origin_id"] == "T001"]
        self.assertGreaterEqual(len(same_local_id), 2)
        self.assertEqual(len({item["id"] for item in same_local_id}), len(same_local_id))

        restored_bridge = unwrap_native(merged, bridge_packet["records"][0]["id"])
        restored_hinges = unwrap_native(merged, hinge_packet["records"][0]["id"])
        self.assertEqual(restored_bridge, case["handoff"])
        self.assertEqual(restored_hinges, case["hinges"])
        self.bridgekeeper.validate(restored_bridge)
        self.hingecheck.validate(restored_hinges)
        self.assertNotEqual(restored_bridge["changes"], restored_bridge["corrections"])

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "architecture-flow.json"
            save(path, merged)
            reloaded = load(path)
        self.assertEqual(reloaded["records"], merged["records"])
        self.assertEqual(reloaded["links"], merged["links"])


if __name__ == "__main__":
    unittest.main()
