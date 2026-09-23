"""Unit and integration tests for GitHub read-only tools."""

import unittest
from unittest.mock import patch, MagicMock
from app.github_tools import (
    get_github_repository,
    get_github_workflow_runs,
    get_github_workflow_run_details,
    get_github_workflow_jobs,
    get_github_failed_job_steps,
    get_github_job_logs,
    get_github_pull_request,
    get_github_commit_details,
    sanitize_sensitive_data,
)


class TestGitHubToolsMocked(unittest.TestCase):
    """Offline unit tests using mocked HTTP responses."""

    @patch("requests.get")
    def test_get_github_repository_mocked(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "full_name": "mock-org/mock-repo",
            "description": "Mock DevOps Repo",
            "default_branch": "main",
            "visibility": "public",
            "open_issues_count": 2,
            "language": "Python",
            "updated_at": "2026-09-23T10:00:00Z",
        }
        mock_get.return_value = mock_resp

        res = get_github_repository("mock-org", "mock-repo")
        self.assertIn("Repository: mock-org/mock-repo", res)
        self.assertIn("Default Branch: main", res)

    @patch("requests.get")
    def test_get_github_failed_job_steps_mocked(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "jobs": [
                {
                    "id": 101,
                    "name": "Build & Lint",
                    "conclusion": "success",
                    "steps": [{"number": 1, "name": "Checkout", "conclusion": "success"}],
                },
                {
                    "id": 102,
                    "name": "Pixel Regression",
                    "conclusion": "failure",
                    "steps": [
                        {"number": 1, "name": "Checkout", "conclusion": "success"},
                        {"number": 8, "name": "Compare Baseline", "conclusion": "failure"},
                    ],
                },
            ]
        }
        mock_get.return_value = mock_resp

        res = get_github_failed_job_steps("mock-org", "mock-repo", 12345)
        self.assertIn("Job ID: 102 | Name: 'Pixel Regression' | Conclusion: failure", res)
        self.assertIn("Step #8 'Compare Baseline': failure", res)

    def test_sanitize_sensitive_data(self):
        text = "My secret token is ghp_1234567890abcdefghijklmnopqrst and password: SecretPass123"
        sanitized = sanitize_sensitive_data(text)
        self.assertNotIn("ghp_1234567890abcdefghijklmnopqrst", sanitized)
        self.assertIn("[REDACTED_SENSITIVE_DATA]", sanitized)


class TestGitHubToolsLiveAPI(unittest.TestCase):
    """Integration test against public GitHub repository ctssddevopsengineer/wedding-invitation-site."""

    def test_live_workflow_run_35428930729(self):
        owner = "ctssddevopsengineer"
        repo = "wedding-invitation-site"
        run_id = 35428930729

        run_details = get_github_workflow_run_details(owner, repo, run_id)
        self.assertIn("35428930729", run_details)
        self.assertIn("New CI", run_details)

        failed_steps = get_github_failed_job_steps(owner, repo, run_id)
        self.assertIn("Pixel Visual Regression", failed_steps)
        self.assertIn("Compare against approved pixel baselines", failed_steps)


if __name__ == "__main__":
    unittest.main()
