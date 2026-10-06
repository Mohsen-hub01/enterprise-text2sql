import contextlib
import io
import unittest
from unittest.mock import Mock, patch

import requests

from evaluation import run_api_benchmark as benchmark


class ApiBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.results_patch = patch.object(benchmark, "RESULTS_PATH")
        self.results_path = self.results_patch.start()
        self.addCleanup(self.results_patch.stop)

    example = {
        "id": "test",
        "question": "How many customers?",
        "reference_sql": "SELECT COUNT(*) FROM customers",
        "category": "aggregation",
    }

    def run_response(self, payload):
        response = Mock(status_code=200)
        response.json.return_value = payload
        with (
            patch.object(benchmark, "load_dataset", return_value=[self.example]),
            patch.object(benchmark.requests, "post", return_value=response),
            patch.object(benchmark, "compare_execution", return_value={"correct": True}) as compare,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = benchmark.run_benchmark()
        return result, compare

    def test_blocked_sql_is_never_executed(self):
        result, compare = self.run_response({
            "generated_sql": "DELETE FROM customers",
            "safe_sql": "SELECT COUNT(*) FROM customers",
            "validation": {"valid": False, "reason": "Blocked"},
        })
        compare.assert_not_called()
        self.assertEqual(result["correct"], 0)

    def test_failed_execution_is_never_retried_by_evaluator(self):
        result, compare = self.run_response({
            "safe_sql": "SELECT missing FROM customers",
            "validation": {"valid": True},
            "execution_error": "Unknown column",
        })
        compare.assert_not_called()
        self.assertEqual(result["correct"], 0)

    def test_generated_sql_without_executed_sql_is_not_compared(self):
        result, compare = self.run_response({
            "generated_sql": "SELECT COUNT(*) FROM customers",
            "validation": {"valid": True},
        })
        compare.assert_not_called()
        self.assertEqual(result["correct"], 0)

    def test_success_compares_safe_sql(self):
        sql = "SELECT COUNT(*) FROM customers LIMIT 100"
        result, compare = self.run_response({
            "safe_sql": sql, "validation": {"valid": True}, "retry_count": 1,
        })
        compare.assert_called_once_with(generated_sql=sql, reference_sql=self.example["reference_sql"])
        self.assertEqual(result["correct"], 1)
        self.assertEqual(result["average_retries"], 1)
        saved = benchmark.json.loads(self.results_path.write_text.call_args.args[0])
        self.assertEqual(saved["correct"], 1)

    def test_malformed_payloads_are_failures(self):
        for payload in ([], None, {"validation": None}, {"retry_count": "two"}):
            with self.subTest(payload=payload):
                result, compare = self.run_response(payload)
                compare.assert_not_called()
                self.assertEqual(len(result["evaluations"]), 1)
                self.assertIn("Invalid API response", result["evaluations"][0]["error"])

    def test_invalid_json_does_not_stop_next_example(self):
        invalid = Mock(status_code=200)
        invalid.json.side_effect = ValueError("Invalid JSON")
        valid = Mock(status_code=200)
        valid.json.return_value = {
            "safe_sql": "SELECT 1", "validation": {"valid": True},
        }
        with (
            patch.object(benchmark, "load_dataset", return_value=[self.example, self.example]),
            patch.object(benchmark.requests, "post", side_effect=[invalid, valid]),
            patch.object(benchmark, "compare_execution", return_value={"correct": True}),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = benchmark.run_benchmark()
        self.assertEqual(result["correct"], 1)
        self.assertEqual(len(result["evaluations"]), 2)

    def test_network_and_http_errors_are_recorded(self):
        http_error = Mock(status_code=500, text="Server error")
        with (
            patch.object(benchmark, "load_dataset", return_value=[self.example, self.example]),
            patch.object(benchmark.requests, "post", side_effect=[requests.Timeout("Timeout"), http_error]),
            patch.object(benchmark, "compare_execution") as compare,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = benchmark.run_benchmark()
        compare.assert_not_called()
        self.assertEqual(len(result["evaluations"]), 2)

    def test_windows_delegates_and_preserves_exit_code(self):
        with (
            patch.object(benchmark.sys, "platform", "win32"),
            patch.object(benchmark.subprocess, "run", return_value=Mock(returncode=7)) as run,
            patch.object(benchmark, "run_benchmark") as local,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(benchmark.main(), 7)
        local.assert_not_called()
        self.assertEqual(run.call_args.args[0], [
            "docker", "compose", "exec", "-T", "api", "python", "-m",
            "evaluation.run_api_benchmark",
        ])

    def test_dataset_loads_outside_project_directory(self):
        import os
        import tempfile

        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                self.assertTrue(benchmark.load_dataset())
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
