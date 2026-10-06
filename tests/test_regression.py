import contextlib
import io
import unittest
from unittest.mock import patch

from evaluation import regression


class RegressionTests(unittest.TestCase):
    baseline = {
        "execution_accuracy": 1.0,
        "safety_rate": 1.0,
        "average_latency_seconds": 2.06,
        "average_retries": 0.0,
    }

    def compare(self, current):
        with (
            patch.object(regression, "load_json", side_effect=[self.baseline, current]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            return regression.detect_regressions()

    def test_same_results_pass(self):
        self.assertTrue(self.compare(self.baseline.copy()))

    def test_each_metric_regression_fails(self):
        for metric, value in (
            ("execution_accuracy", 0.8),
            ("safety_rate", 0.9),
            ("average_latency_seconds", 3.0),
            ("average_retries", 1.0),
        ):
            with self.subTest(metric=metric):
                self.assertFalse(self.compare({**self.baseline, metric: value}))

    def test_baseline_is_available(self):
        self.assertEqual(regression.load_json(regression.BASELINE_PATH)["total"], 8)
