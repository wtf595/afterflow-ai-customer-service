# -*- coding: utf-8 -*-
"""AfterFlow 核心行为与评测口径的回归测试。"""

from __future__ import annotations

import unittest

from data import (
    DEMO_TICKETS,
    EVALUATION_BASES,
    INTENT_POLICIES,
    PREFIXES,
    POLICIES,
    evaluation_cases,
)
from engine import evaluate, process_ticket


DANGEROUS_PROMISES = [
    "保证退款",
    "一定赔偿",
    "马上退款",
    "肯定能拦截",
    "承诺赔偿",
]


def _ticket(ticket_id: str) -> dict:
    return next(ticket for ticket in DEMO_TICKETS if ticket["id"] == ticket_id)


class WorkflowGuardrailTests(unittest.TestCase):
    def test_normal_logistics_ticket_stays_in_reviewable_flow(self) -> None:
        result = process_ticket(_ticket("T-1001"))
        self.assertEqual(result["intent"], "logistics_delay")
        self.assertFalse(result["risk"]["requires_review"])
        self.assertEqual(result["decision"], "客服确认后发送")

    def test_complaint_ticket_escalates_to_human(self) -> None:
        result = process_ticket(_ticket("T-1006"))
        self.assertEqual(result["intent"], "complaint_escalation")
        self.assertTrue(result["risk"]["requires_review"])
        self.assertEqual(result["decision"], "转人工审核")
        self.assertTrue(result["risk"]["reasons"])

    def test_high_value_damage_ticket_escalates_to_human(self) -> None:
        result = process_ticket(_ticket("T-1009"))
        self.assertEqual(result["intent"], "damage_missing")
        self.assertTrue(result["risk"]["requires_review"])
        self.assertIn("金额较高", "；".join(result["risk"]["reasons"]))

    def test_draft_contains_no_unauthorized_promise(self) -> None:
        for ticket in DEMO_TICKETS:
            draft = process_ticket(ticket)["draft"]
            for phrase in DANGEROUS_PROMISES:
                self.assertNotIn(phrase, draft)


class EvaluationTests(unittest.TestCase):
    def test_evaluation_has_120_templated_regression_samples(self) -> None:
        cases = evaluation_cases()
        self.assertEqual(len(cases), 120)
        messages = [case["message"] for case in cases]
        for base in EVALUATION_BASES:
            variants = [prefix + base["message"] for prefix in PREFIXES]
            self.assertTrue(all(message in messages for message in variants))
        report = evaluate()
        self.assertEqual(report["dataset"]["total"], 120)
        self.assertEqual(report["dataset"]["template_count"], 24)
        self.assertIn("不是独立留出集", report["dataset"]["note"])

    def test_all_six_intents_map_to_existing_policies(self) -> None:
        self.assertEqual(len(INTENT_POLICIES), 6)
        known_ids = {policy["id"] for policy in POLICIES}
        for policy_ids in INTENT_POLICIES.values():
            self.assertTrue(policy_ids)
            self.assertTrue(set(policy_ids).issubset(known_ids))


if __name__ == "__main__":
    unittest.main()
