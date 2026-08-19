from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Iterable

from .core import PolicyError


def classification_metrics(true_positive: int, false_positive: int, false_negative: int) -> dict[str, Any]:
    if min(true_positive, false_positive, false_negative) < 0:
        raise PolicyError("confusion counts cannot be negative")
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 0.0
    recall = true_positive / recall_denominator if recall_denominator else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "counts": {"tp": true_positive, "fp": false_positive, "fn": false_negative},
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def summarize_trials(trials: Iterable[dict[str, Any]]) -> dict[str, Any]:
    observations = [copy.deepcopy(trial) for trial in trials]
    passed = sum(int(trial["passed"]) for trial in observations)
    total = sum(int(trial["total"]) for trial in observations)
    costs: Counter[str] = Counter()
    failures: Counter[str] = Counter()
    for trial in observations:
        costs.update({key: float(value) for key, value in trial.get("costs", {}).items()})
        if trial.get("failure_category"):
            failures[trial["failure_category"]] += 1
    return {
        "hidden_test_pass_rate": passed / total if total else 0.0,
        "passed": passed,
        "total": total,
        "cost_components": dict(sorted(costs.items())),
        "failure_categories": dict(sorted(failures.items())),
        "observations": observations,
    }
