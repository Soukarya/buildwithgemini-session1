"""Read-only GitHub Actions & Repository Tools for the ReleaseOps AI Assistant.

Provides safe, read-only tools for inspecting repositories, workflow runs, jobs,
failed step logs, pull requests, and commit metadata using the GitHub REST API.

Credentials:
- Reads GITHUB_TOKEN or GH_TOKEN from environment if available.
- Functions operate in read-only mode (HTTP GET only).
- Credentials and tokens are NEVER printed, logged, or hardcoded.
"""

import os
import re
import requests
from typing import Optional, Dict, Any


def _get_github_headers() -> Dict[str, str]:
    """Helper to construct GitHub REST API headers with optional token from environment."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ReleaseOps-AI-Assistant/1.0",
    }
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def sanitize_sensitive_data(text: str) -> str:
    """Redacts tokens, API keys, passwords, and secrets from string output."""
    if not text:
        return text
    patterns = [
        r"(?i)(token|password|secret|api[_-]?key|bearer|credential|auth)[=:\s]+[^\s]+",
        r"ghp_[A-Za-z0-9]{20,}",
        r"gho_[A-Za-z0-9]{20,}",
        r"ghu_[A-Za-z0-9]{20,}",
        r"ghs_[A-Za-z0-9]{20,}",
        r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    ]
    sanitized = text
    for p in patterns:
        sanitized = re.sub(p, "[REDACTED_SENSITIVE_DATA]", sanitized)
    return sanitized


def get_github_repository(owner: str, repo: str) -> str:
    """Fetch read-only metadata for a GitHub repository.

    Args:
        owner: GitHub repository owner or organization (e.g. 'ctssddevopsengineer').
        repo: Repository name (e.g. 'wedding-invitation-site').

    Returns:
        Formatted summary of repository metadata.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        r = requests.get(url, headers=_get_github_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            res = (
                f"Repository: {data.get('full_name')}\n"
                f"Description: {data.get('description', 'N/A')}\n"
                f"Default Branch: {data.get('default_branch')}\n"
                f"Visibility: {data.get('visibility', 'public')}\n"
                f"Open Issues: {data.get('open_issues_count')}\n"
                f"Language: {data.get('language')}\n"
                f"Updated At: {data.get('updated_at')}"
            )
            return sanitize_sensitive_data(res)
        return f"GitHub API returned HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Error fetching GitHub repository {owner}/{repo}: {str(e)}"


def get_github_workflow_runs(
    owner: str, repo: str, status: Optional[str] = None, limit: int = 5
) -> str:
    """List recent GitHub Actions workflow runs for a repository.

    Args:
        owner: GitHub owner/org.
        repo: GitHub repository name.
        status: Optional status filter (e.g., 'completed', 'failure', 'in_progress').
        limit: Max number of runs to return (default: 5).

    Returns:
        Formatted string listing recent workflow runs.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    params = {"per_page": limit}
    if status:
        params["status"] = status

    try:
        r = requests.get(url, headers=_get_github_headers(), params=params, timeout=10)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            if not runs:
                return f"No workflow runs found for {owner}/{repo}."
            lines = [f"Recent Workflow Runs for {owner}/{repo}:"]
            for run in runs[:limit]:
                lines.append(
                    f"- Run ID: {run.get('id')} | Name: '{run.get('name')}' | "
                    f"Status: {run.get('status')} | Conclusion: {run.get('conclusion')} | "
                    f"Event: {run.get('event')} | Head Branch: {run.get('head_branch')}"
                )
            return sanitize_sensitive_data("\n".join(lines))
        return f"GitHub API returned HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Error listing workflow runs for {owner}/{repo}: {str(e)}"


def get_github_workflow_run_details(owner: str, repo: str, run_id: int) -> str:
    """Fetch detailed metadata for a specific GitHub Actions workflow run.

    Args:
        owner: GitHub repository owner.
        repo: GitHub repository name.
        run_id: Integer ID of the GitHub Actions workflow run.

    Returns:
        Formatted summary of workflow run metadata.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}"
    try:
        r = requests.get(url, headers=_get_github_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            res = (
                f"Workflow Run ID: {data.get('id')}\n"
                f"Workflow Name: {data.get('name')}\n"
                f"Status: {data.get('status')}\n"
                f"Conclusion: {data.get('conclusion')}\n"
                f"Event: {data.get('event')}\n"
                f"Head Branch: {data.get('head_branch')}\n"
                f"Head Commit SHA: {data.get('head_sha')}\n"
                f"Head Commit Message: {data.get('head_commit', {}).get('message', 'N/A')}\n"
                f"Actor: {data.get('actor', {}).get('login')}\n"
                f"Created At: {data.get('created_at')}\n"
                f"Updated At: {data.get('updated_at')}\n"
                f"HTML URL: {data.get('html_url')}"
            )
            return sanitize_sensitive_data(res)
        return f"GitHub API returned HTTP {r.status_code} for run {run_id}: {r.text[:200]}"
    except Exception as e:
        return f"Error fetching workflow run details for run_id {run_id}: {str(e)}"


def get_github_workflow_jobs(owner: str, repo: str, run_id: int) -> str:
    """List all jobs associated with a GitHub Actions workflow run.

    Args:
        owner: GitHub repository owner.
        repo: GitHub repository name.
        run_id: Workflow run ID.

    Returns:
        Formatted summary of all jobs in the workflow run.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    try:
        r = requests.get(url, headers=_get_github_headers(), timeout=10)
        if r.status_code == 200:
            jobs = r.json().get("jobs", [])
            if not jobs:
                return f"No jobs found for workflow run {run_id}."
            lines = [f"Jobs for Workflow Run {run_id} in {owner}/{repo}:"]
            for job in jobs:
                lines.append(
                    f"- Job ID: {job.get('id')} | Name: '{job.get('name')}' | "
                    f"Status: {job.get('status')} | Conclusion: {job.get('conclusion')} | "
                    f"Steps Count: {len(job.get('steps', []))}"
                )
            return sanitize_sensitive_data("\n".join(lines))
        return f"GitHub API returned HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Error listing jobs for workflow run {run_id}: {str(e)}"


def get_github_failed_job_steps(owner: str, repo: str, run_id: int) -> str:
    """Inspect and extract failed or cancelled jobs and their specific failed steps.

    Args:
        owner: GitHub repository owner.
        repo: GitHub repository name.
        run_id: Workflow run ID.

    Returns:
        Formatted summary of failed jobs and failed/skipped steps with line-item detail.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    try:
        r = requests.get(url, headers=_get_github_headers(), timeout=10)
        if r.status_code == 200:
            jobs = r.json().get("jobs", [])
            failed_jobs = [
                j for j in jobs if j.get("conclusion") in ["failure", "cancelled", "timed_out"]
            ]
            if not failed_jobs:
                return f"All jobs in workflow run {run_id} completed successfully (or no failures found)."

            lines = [f"Failed / Cancelled Jobs in Workflow Run {run_id}:"]
            for job in failed_jobs:
                lines.append(
                    f"\nJob ID: {job.get('id')} | Name: '{job.get('name')}' | Conclusion: {job.get('conclusion')}"
                )
                steps = job.get("steps", [])
                for step in steps:
                    conclusion = step.get("conclusion")
                    if conclusion != "success":
                        lines.append(
                            f"   ↳ Step #{step.get('number')} '{step.get('name')}': {conclusion}"
                        )
            return sanitize_sensitive_data("\n".join(lines))
        return f"GitHub API returned HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Error extracting failed job steps for run_id {run_id}: {str(e)}"


def get_github_job_logs(owner: str, repo: str, job_id: int, max_lines: int = 100) -> str:
    """Fetch execution log lines for a specific GitHub Actions job.

    Args:
        owner: GitHub repository owner.
        repo: GitHub repository name.
        job_id: Integer job ID.
        max_lines: Maximum error/relevant log lines to return (default: 100).

    Returns:
        Relevant execution log text or authentication guidance.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
    try:
        r = requests.get(url, headers=_get_github_headers(), allow_redirects=True, timeout=15)
        if r.status_code == 200:
            log_text = r.text
            lines = log_text.split("\n")
            # Extract lines with failure / error signals
            filtered_lines = [
                l for l in lines if any(w in l.lower() for w in ["error", "fail", "fatal", "mismatch", "exception", "failed"])
            ]
            sample = filtered_lines[:max_lines] if filtered_lines else lines[:max_lines]
            res = (
                f"Log snippet for Job ID {job_id} ({len(lines)} total lines, returning {len(sample)} relevant lines):\n"
                + "\n".join(sample)
            )
            return sanitize_sensitive_data(res)
        elif r.status_code == 403:
            return (
                f"Log download for Job ID {job_id} returned HTTP 403 Forbidden. "
                f"Downloading raw logs requires a valid GITHUB_TOKEN in environment variables. "
                f"Job step metadata remains fully accessible via get_github_failed_job_steps."
            )
        return f"GitHub API returned HTTP {r.status_code} for job {job_id}: {r.text[:200]}"
    except Exception as e:
        return f"Error fetching job logs for job_id {job_id}: {str(e)}"


def get_github_pull_request(owner: str, repo: str, pr_number: int) -> str:
    """Fetch read-only pull request metadata for a repository.

    Args:
        owner: GitHub repository owner.
        repo: GitHub repository name.
        pr_number: Integer PR number.

    Returns:
        Formatted summary of pull request metadata.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    try:
        r = requests.get(url, headers=_get_github_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            res = (
                f"Pull Request #{data.get('number')}: {data.get('title')}\n"
                f"State: {data.get('state')}\n"
                f"Author: {data.get('user', {}).get('login')}\n"
                f"Head Branch: {data.get('head', {}).get('ref')} ({data.get('head', {}).get('sha')[:7]})\n"
                f"Base Branch: {data.get('base', {}).get('ref')}\n"
                f"Mergeable: {data.get('mergeable')}\n"
                f"Draft: {data.get('draft')}\n"
                f"Created At: {data.get('created_at')}\n"
                f"Updated At: {data.get('updated_at')}"
            )
            return sanitize_sensitive_data(res)
        return f"GitHub API returned HTTP {r.status_code} for PR #{pr_number}: {r.text[:200]}"
    except Exception as e:
        return f"Error fetching pull request #{pr_number}: {str(e)}"


def get_github_commit_details(owner: str, repo: str, commit_sha: str) -> str:
    """Fetch read-only commit details for a repository.

    Args:
        owner: GitHub repository owner.
        repo: GitHub repository name.
        commit_sha: Full or short commit SHA string.

    Returns:
        Formatted summary of commit details.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
    try:
        r = requests.get(url, headers=_get_github_headers(), timeout=10)
        if r.status_code == 200:
            data = r.json()
            commit_info = data.get("commit", {})
            author_info = commit_info.get("author", {})
            files = data.get("files", [])
            file_names = [f.get("filename") for f in files[:10]]
            res = (
                f"Commit SHA: {data.get('sha')}\n"
                f"Author: {author_info.get('name')} <{author_info.get('email')}>\n"
                f"Date: {author_info.get('date')}\n"
                f"Message: {commit_info.get('message')}\n"
                f"Changed Files Count: {len(files)}\n"
                f"Sample Changed Files: {', '.join(file_names)}"
            )
            return sanitize_sensitive_data(res)
        return f"GitHub API returned HTTP {r.status_code} for commit {commit_sha}: {r.text[:200]}"
    except Exception as e:
        return f"Error fetching commit {commit_sha}: {str(e)}"
