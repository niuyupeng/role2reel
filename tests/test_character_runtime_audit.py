from __future__ import annotations

import argparse
import copy
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import scripts.audit_character_runtime as runtime_audit
from scripts.audit_character_runtime import audit_runtime, parse_args


def valid_documents():
    cognitive = {
        "character_id": "character-1",
        "contract": {"purpose": "comprehension_and_private_judgment"},
        "resources": [{"id": "cog-1", "character_id": "character-1"}],
    }
    speech = {
        "character_id": "character-1",
        "contract": {"purpose": "expression_retrieval_after_private_judgment"},
        "entries": [{"id": "speech-1", "character_id": "character-1", "approval_state": "approved"}],
    }
    turn_state = {
        "turns": [
            {
                "turn": 1,
                "character_id": "character-1",
                "perceived_cue": "The other person closes the folder.",
                "literal_read": "The folder is no longer available.",
                "attribution": "A test of whether the character will pursue.",
                "judgment_or_question": "Clarify the cost without pleading.",
                "surface": {
                    "action": "Keeps one hand on the folder.",
                    "spatial_relation": None,
                    "gaze": "At the other person's hand.",
                    "expression": None,
                    "silence": False,
                    "dialogue": "还谈吗？",
                },
                "consequence": ["The other person must accept or explicitly end the negotiation."],
            }
        ],
        "decision_traces": [
            {
                "turn": 1,
                "character_id": "character-1",
                "comprehension_retrieval": {
                    "cognitive_resource_ids": ["cog-1"],
                    "memory_ids": [],
                    "relationship_claim_ids": [],
                    "common_ground_proposition_ids": [],
                    "second_order_belief_ids": [],
                    "checked_unknown_or_excluded_resource_ids": [],
                },
                "private_interpretation": "The offer is being withdrawn without saying so.",
                "pragmatic_attribution": "A test of whether the character will pursue.",
                "inferences": [
                    {"status": "no_new_inference", "proposition": "The cost remains undefined."}
                ],
                "belief_delta": [
                    {"status": "no_change", "proposition": "The other person's intent remains unresolved."}
                ],
                "stance": "contained pursuit",
                "social_objective": "Keep the negotiation open.",
                "expression_retrieval": {
                    "retrieval_status": "matched",
                    "speech_corpus_entry_ids": ["speech-1"],
                    "relationship_register": "formal",
                    "action_or_silence_options": ["keep one hand on the folder"],
                    "wording_options": [],
                },
            }
        ],
    }
    return turn_state, cognitive, speech


def valid_multi_character_documents():
    turn_state, cognitive_1, speech_1 = valid_documents()
    cognitive_1["resources"][0]["id"] = "cog-1"
    speech_1["entries"][0]["id"] = "speech-1"
    trace_1 = turn_state["decision_traces"][0]
    trace_1["comprehension_retrieval"].update(
        {
            "cognitive_resource_ids": ["cog-1"],
            "memory_ids": ["memory-1"],
            "relationship_claim_ids": ["claim-1"],
            "common_ground_proposition_ids": ["common-1"],
            "second_order_belief_ids": ["second-1"],
        }
    )
    trace_1["expression_retrieval"]["speech_corpus_entry_ids"] = ["speech-1"]

    cognitive_2 = {
        "character_id": "character-2",
        "contract": {"purpose": "comprehension_and_private_judgment"},
        "resources": [{"id": "cog-2", "character_id": "character-2"}],
    }
    speech_2 = {
        "character_id": "character-2",
        "contract": {"purpose": "expression_retrieval_after_private_judgment"},
        "entries": [],
    }
    turn_2 = copy.deepcopy(turn_state["turns"][0])
    turn_2.update(
        {
            "turn": 2,
            "character_id": "character-2",
            "perceived_cue": "The first character keeps a hand on the folder.",
            "literal_read": "The folder remains between them.",
            "attribution": "A request to keep the negotiation open.",
            "judgment_or_question": "Pause before accepting the request.",
            "surface": {
                "action": "Leaves the folder on the table.",
                "spatial_relation": None,
                "gaze": "At the door.",
                "expression": None,
                "silence": True,
                "dialogue": None,
            },
            "consequence": ["The negotiation remains open without an answer."],
        }
    )
    trace_2 = copy.deepcopy(trace_1)
    trace_2.update(
        {
            "turn": 2,
            "character_id": "character-2",
            "private_interpretation": "The request leaves room to delay.",
            "pragmatic_attribution": "A request to keep the negotiation open.",
            "stance": "reserve",
            "social_objective": "Keep the option open without agreeing.",
        }
    )
    trace_2["comprehension_retrieval"].update(
        {
            "cognitive_resource_ids": ["cog-2"],
            "memory_ids": ["memory-2"],
            "relationship_claim_ids": ["claim-2"],
            "common_ground_proposition_ids": ["common-1"],
            "second_order_belief_ids": ["second-2"],
        }
    )
    trace_2["expression_retrieval"] = {
        "retrieval_status": "not_applicable_nonverbal",
        "speech_corpus_entry_ids": [],
        "relationship_register": "formal",
        "action_or_silence_options": ["leave the folder on the table"],
        "wording_options": [],
    }
    turn_state["turns"].append(turn_2)
    turn_state["decision_traces"].append(trace_2)

    memories = [
        {"character_id": "character-1", "memories": [{"id": "memory-1"}]},
        {"character_id": "character-2", "memories": [{"id": "memory-2"}]},
    ]
    relationships = {
        "relationship_claim_records": [
            {"id": "claim-1", "from_character": "character-1"},
            {"id": "claim-2", "from_character": "character-2"},
        ],
        "common_ground_propositions": [
            {"id": "common-1", "participants": ["character-1", "character-2"]}
        ],
        "second_order_beliefs": [
            {"id": "second-1", "holder_character_id": "character-1"},
            {"id": "second-2", "holder_character_id": "character-2"},
        ],
    }
    return turn_state, [cognitive_1, cognitive_2], [speech_1, speech_2], memories, relationships


class CharacterRuntimeAuditTests(unittest.TestCase):
    def test_valid_two_stage_turn_passes(self) -> None:
        turn_state, cognitive, speech = valid_documents()
        self.assertEqual(
            audit_runtime(turn_state, cognitive_resources=cognitive, speech_corpus=speech),
            [],
        )

    def test_unknown_or_unapproved_refs_fail(self) -> None:
        turn_state, cognitive, speech = valid_documents()
        turn_state["decision_traces"][0]["comprehension_retrieval"]["cognitive_resource_ids"] = ["missing"]
        speech["entries"][0]["approval_state"] = "pending"
        codes = {
            item.code
            for item in audit_runtime(
                turn_state,
                cognitive_resources=cognitive,
                speech_corpus=speech,
            )
        }
        self.assertTrue({"unknown-cognitive-resource", "unapproved-speech-corpus-entry"}.issubset(codes))

    def test_private_analysis_spill_is_a_warning(self) -> None:
        turn_state, cognitive, speech = valid_documents()
        private = turn_state["decision_traces"][0]["private_interpretation"]
        turn_state["turns"][0]["surface"]["dialogue"] = private
        findings = audit_runtime(turn_state, cognitive_resources=cognitive, speech_corpus=speech)
        spill = next(item for item in findings if item.code == "private-analysis-spill")
        self.assertEqual(spill.severity, "warning")

    def test_missing_consequence_is_an_error(self) -> None:
        turn_state, cognitive, speech = valid_documents()
        turn_state["turns"][0]["consequence"] = []
        findings = audit_runtime(turn_state, cognitive_resources=cognitive, speech_corpus=speech)
        self.assertIn("missing-turn-consequence", {item.code for item in findings})

    def test_empty_middle_records_do_not_count_as_explicit_no_change(self) -> None:
        turn_state, cognitive, speech = valid_documents()
        turn_state["decision_traces"][0]["inferences"] = []
        turn_state["decision_traces"][0]["belief_delta"] = []
        codes = {
            item.code
            for item in audit_runtime(
                turn_state,
                cognitive_resources=cognitive,
                speech_corpus=speech,
            )
        }
        self.assertTrue({"empty-inferences-record", "empty-belief-delta-record"}.issubset(codes))

    def test_cross_character_libraries_and_entries_fail_closed(self) -> None:
        turn_state, cognitive, speech = valid_documents()
        cognitive["character_id"] = "character-2"
        cognitive["resources"][0]["character_id"] = "character-2"
        speech["character_id"] = "character-2"
        speech["entries"][0]["character_id"] = "character-2"
        codes = {item.code for item in audit_runtime(turn_state, cognitive_resources=cognitive, speech_corpus=speech)}
        self.assertTrue(
            {
                "cognitive-character-mismatch",
                "cognitive-entry-character-mismatch",
                "speech-character-mismatch",
                "speech-entry-character-mismatch",
            }.issubset(codes)
        )

    def test_empty_retrievals_require_explicit_nonverbal_fallback(self) -> None:
        turn_state, cognitive, speech = valid_documents()
        trace = turn_state["decision_traces"][0]
        trace["comprehension_retrieval"]["cognitive_resource_ids"] = []
        trace["expression_retrieval"]["speech_corpus_entry_ids"] = []
        trace["expression_retrieval"]["retrieval_status"] = None
        codes = {item.code for item in audit_runtime(turn_state, cognitive_resources=cognitive, speech_corpus=speech)}
        self.assertTrue(
            {"empty-comprehension-retrieval", "dialogue-without-expression-evidence", "empty-expression-retrieval"}.issubset(codes)
        )

        turn_state["decision_traces"][0]["comprehension_retrieval"]["checked_unknown_or_excluded_resource_ids"] = ["unknown:cue"]
        turn_state["decision_traces"][0]["expression_retrieval"]["retrieval_status"] = "not_applicable_nonverbal"
        turn_state["turns"][0]["surface"]["dialogue"] = None
        self.assertEqual(audit_runtime(turn_state, cognitive_resources=cognitive, speech_corpus=speech), [])

    def test_full_multi_character_turn_state_uses_per_character_indexes(self) -> None:
        turn_state, cognitive, speech, memories, relationships = valid_multi_character_documents()
        self.assertEqual(
            audit_runtime(
                turn_state,
                cognitive_resources=cognitive,
                speech_corpus=speech,
                memories=memories,
                relationship_ledgers=relationships,
            ),
            [],
        )

    def test_wrong_character_refs_do_not_fall_back_to_another_library(self) -> None:
        turn_state, cognitive, speech, memories, relationships = valid_multi_character_documents()
        trace = turn_state["decision_traces"][0]
        trace["comprehension_retrieval"]["cognitive_resource_ids"] = ["cog-2"]
        trace["comprehension_retrieval"]["memory_ids"] = ["memory-2"]
        trace["comprehension_retrieval"]["relationship_claim_ids"] = ["claim-2"]
        speech[1]["entries"] = [
            {"id": "speech-2", "character_id": "character-2", "approval_state": "approved"}
        ]
        trace["expression_retrieval"]["speech_corpus_entry_ids"] = ["speech-2"]
        codes = {
            item.code
            for item in audit_runtime(
                turn_state,
                cognitive_resources=cognitive,
                speech_corpus=speech,
                memories=memories,
                relationship_ledgers=relationships,
            )
        }
        self.assertTrue(
            {
                "cognitive-entry-character-mismatch",
                "memory-entry-character-mismatch",
                "relationship-reference-character-mismatch",
                "speech-entry-character-mismatch",
            }.issubset(codes)
        )

    def test_claimed_refs_without_indexes_fail_closed(self) -> None:
        turn_state, _, _, _, _ = valid_multi_character_documents()
        codes = {item.code for item in audit_runtime(turn_state)}
        self.assertTrue(
            {
                "unverifiable-cognitive-resource-reference",
                "unverifiable-memory-reference",
                "unverifiable-relationship-reference",
                "unverifiable-speech-corpus-reference",
            }.issubset(codes)
        )

    def test_duplicate_ids_and_malformed_refs_are_errors_not_exceptions(self) -> None:
        turn_state, cognitive, speech = valid_documents()
        cognitive["resources"].append(copy.deepcopy(cognitive["resources"][0]))
        speech["entries"].append(copy.deepcopy(speech["entries"][0]))
        memories = {
            "character_id": "character-1",
            "memories": [{"id": "memory-1"}, {"id": "memory-1"}],
        }
        relationships = {
            "relationship_claim_records": [
                {"id": "claim-1", "from_character": "character-1"},
                {"id": "claim-1", "from_character": "character-1"},
            ]
        }
        trace = turn_state["decision_traces"][0]
        trace["comprehension_retrieval"]["cognitive_resource_ids"] = [["unhashable"], {"id": "x"}, ""]
        trace["comprehension_retrieval"]["memory_ids"] = ["memory-1"]
        trace["comprehension_retrieval"]["relationship_claim_ids"] = ["claim-1"]
        trace["expression_retrieval"]["speech_corpus_entry_ids"] = [{"id": "unhashable"}]
        codes = {
            item.code
            for item in audit_runtime(
                turn_state,
                cognitive_resources=cognitive,
                speech_corpus=speech,
                memories=memories,
                relationship_ledgers=relationships,
            )
        }
        self.assertTrue(
            {
                "duplicate-cognitive-resource-id",
                "duplicate-speech-corpus-entry-id",
                "duplicate-memory-id",
                "duplicate-relationship-reference-id",
                "invalid-comprehension-reference",
                "invalid-speech-reference",
            }.issubset(codes)
        )

    def test_legacy_and_detailed_trace_contradictions_fail(self) -> None:
        turn_state, cognitive, speech = valid_documents()
        turn = turn_state["turns"][0]
        trace = turn_state["decision_traces"][0]
        turn.update(
            {
                "stance": "agree",
                "social_objective": "End the negotiation.",
                "strategy": "withdraw",
                "impulse_modulation": "leave immediately",
            }
        )
        trace.update(
            {
                "strategy": "ask",
                "impulse_modulation": "stay",
                "output": {
                    "legacy_turn_surface_ref": 99,
                    "surface": {"dialogue": "不谈了。"},
                },
            }
        )
        codes = {
            item.code
            for item in audit_runtime(
                turn_state,
                cognitive_resources=cognitive,
                speech_corpus=speech,
            )
        }
        self.assertTrue(
            {
                "legacy-decision-trace-mismatch",
                "legacy-turn-surface-ref-mismatch",
                "legacy-decision-trace-surface-mismatch",
            }.issubset(codes)
        )

    def test_repeatable_cli_inputs_are_loaded_and_forwarded(self) -> None:
        args = argparse.Namespace(
            turn_state=Path("turn.yaml"),
            cognitive_resources=[Path("cog-a.yaml"), Path("cog-b.yaml")],
            speech_corpus=[Path("speech-a.yaml"), Path("speech-b.yaml")],
            memories=[Path("memory-a.yaml"), Path("memory-b.yaml")],
            relationship_ledger=[Path("relationships.yaml")],
            as_json=False,
        )
        with patch.object(runtime_audit, "parse_args", return_value=args):
            with patch.object(runtime_audit, "_load", side_effect=lambda path: {"loaded": str(path)}):
                with patch.object(runtime_audit, "audit_runtime", return_value=[]) as audited:
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(runtime_audit.main(), 0)
        forwarded = audited.call_args.kwargs
        self.assertEqual(len(forwarded["cognitive_resources"]), 2)
        self.assertEqual(len(forwarded["speech_corpus"]), 2)
        self.assertEqual(len(forwarded["memories"]), 2)
        self.assertEqual(len(forwarded["relationship_ledgers"]), 1)

    def test_parse_args_accumulates_repeatable_library_options(self) -> None:
        argv = [
            "audit_character_runtime.py",
            "turn.yaml",
            "--cognitive-resources",
            "cog-a.yaml",
            "--cognitive-resources",
            "cog-b.yaml",
            "--speech-corpus",
            "speech-a.yaml",
            "--speech-corpus",
            "speech-b.yaml",
            "--memories",
            "memory-a.yaml",
            "--relationship-ledger",
            "relationships.yaml",
        ]
        with patch("sys.argv", argv):
            args = parse_args()
        self.assertEqual(args.cognitive_resources, [Path("cog-a.yaml"), Path("cog-b.yaml")])
        self.assertEqual(args.speech_corpus, [Path("speech-a.yaml"), Path("speech-b.yaml")])
        self.assertEqual(args.memories, [Path("memory-a.yaml")])
        self.assertEqual(args.relationship_ledger, [Path("relationships.yaml")])


if __name__ == "__main__":
    unittest.main()
