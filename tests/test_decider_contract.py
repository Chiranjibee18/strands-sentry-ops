"""
Phase 5.2: Decider Contract Tests
---------------------------------
Validates typed question schema, response parsing, probability normalization,
and choice option recognition.
"""

import unittest
from decider_patterns import (
    StrandsDeciderClient,
    ChoiceQuestion,
    NoulQuestion,
    ScoreQuestion,
    DeciderAnswer,
)


class TestDeciderContract(unittest.TestCase):

    def setUp(self):
        self.client = StrandsDeciderClient(prefer_local_server=False)

    def test_choice_question_contract(self):
        q = ChoiceQuestion(
            type="choice",
            instructions="Select diagnostic tool",
            options=["inspect_dependencies", "inspect_docker", "inspect_tests"],
        )
        decision = self.client.ask(
            state="ModuleNotFoundError: No module named 'django'",
            questions={"tool": q},
        )
        self.assertIn("tool", decision.answers)
        ans: DeciderAnswer = decision.answers["tool"]
        self.assertEqual(ans.type, "choice")
        self.assertIn(ans.prediction, q.options)
        self.assertGreater(ans.confidence, 0.5)

        # Probabilities sum to 1.0
        prob_sum = sum(ans.probabilities.values())
        self.assertAlmostEqual(prob_sum, 1.0, delta=0.02)

    def test_noul_question_contract(self):
        q = NoulQuestion(
            type="noul",
            instructions="Is this tool call authorized?",
            criteria={"true": "Authorized", "false": "Drift"},
        )
        decision = self.client.ask(
            state="User Intent: Restart cache\nProposed Tool: flush_redis_cache\nArguments: {'db_index': 0}",
            questions={"safe": q},
        )
        ans = decision.answers["safe"]
        self.assertEqual(ans.type, "noul")
        self.assertIsInstance(ans.prediction, bool)
        self.assertGreaterEqual(ans.confidence, 0.0)
        self.assertLessEqual(ans.confidence, 1.0)

    def test_score_question_contract(self):
        q = ScoreQuestion(
            type="score",
            instructions="Rate relevance",
            options=["irrelevant", "low", "medium", "highly_relevant"],
        )
        decision = self.client.ask(
            state="active user query: EKS crashloop\ncontext candidate: EKS OOM runbook",
            questions={"relevance": q},
        )
        ans = decision.answers["relevance"]
        self.assertIn(ans.prediction, q.options)
        self.assertGreaterEqual(ans.score_value, 0.0)
        self.assertLessEqual(ans.score_value, 3.0)

    def test_unknown_option_rejection(self):
        q = ChoiceQuestion(
            type="choice",
            instructions="Select tool",
            options=["inspect_dependencies", "inspect_docker"],
        )
        decision = self.client.ask(
            state="Random text with no match",
            questions={"choice": q},
        )
        ans = decision.answers["choice"]
        self.assertIn(ans.prediction, q.options)


if __name__ == "__main__":
    unittest.main()
