from __future__ import annotations

import unittest

from tracecontract.metrics import classification_metrics, summarize_trials


class MetricContractTests(unittest.TestCase):
    def test_trace_metrics_expose_raw_confusion_counts(self) -> None:
        result = classification_metrics(true_positive=8, false_positive=2, false_negative=4)
        self.assertEqual({"tp": 8, "fp": 2, "fn": 4}, result["counts"])
        self.assertAlmostEqual(0.8, result["precision"])
        self.assertAlmostEqual(2 / 3, result["recall"])
        self.assertAlmostEqual(8 / 11, result["f1"])

    def test_trial_summary_keeps_raw_costs_and_negative_results(self) -> None:
        result = summarize_trials([
            {"label": "X", "passed": 9, "total": 10, "costs": {"ingest": 3, "implementation": 7}, "failure_category": None},
            {"label": "Y", "passed": 5, "total": 10, "costs": {"ingest": 0, "implementation": 8}, "failure_category": "coding_error"},
        ])
        self.assertEqual(0.7, result["hidden_test_pass_rate"])
        self.assertEqual({"ingest": 3.0, "implementation": 15.0}, result["cost_components"])
        self.assertEqual({"coding_error": 1}, result["failure_categories"])
        self.assertEqual(2, len(result["observations"]))


if __name__ == "__main__":
    unittest.main()
