"""
GitHub tools — fetch issues and PRs for improvement analysis, and create new ones.

For demo purposes, includes mock data for testing without real GitHub API.
"""
from typing import Tuple, Optional, Dict, Any
import config

try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


# Mock GitHub data for demo/testing
MOCK_ISSUES = {
    "test-issue-1": {
        "id": "test-issue-1",
        "title": "Add user authentication",
        "body": "We need to add authentication to the app.",
    },
    "test-issue-2": {
        "id": "test-issue-2",
        "title": "Fix bug",
        "body": "Something is broken and needs fixing.",
    },
}

MOCK_PRS = {
    "test-pr-1": {
        "id": "test-pr-1",
        "title": "Update dependencies",
        "body": "Updated some packages.",
        "branch": "feature/update-deps",
    },
}


def _get_github_client():
    """Get authenticated GitHub client."""
    if not GITHUB_AVAILABLE:
        raise RuntimeError("PyGitHub not installed. Run: pip install PyGitHub")

    if not config.GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not set in .env file")

    return Github(config.GITHUB_TOKEN)


def _get_repo():
    """Get the configured GitHub repository."""
    if not config.GITHUB_REPO:
        raise RuntimeError("GITHUB_REPO not set in .env file (format: owner/repo)")

    client = _get_github_client()
    return client.get_repo(config.GITHUB_REPO)


def fetch_github_issue(issue_id: str) -> Optional[dict]:
    """
    Fetch a GitHub issue by ID or URL.

    For demo: accepts "test-issue-1", "test-issue-2", etc.
    For real GitHub: would use GitHub API

    Args:
        issue_id: GitHub issue ID, URL, or test ID

    Returns:
        dict with id, title, body or None if not found
    """
    # Check mock data first
    if issue_id in MOCK_ISSUES:
        return MOCK_ISSUES[issue_id]

    # Try real GitHub API
    try:
        repo = _get_repo()
        issue = repo.get_issue(int(issue_id))
        return {
            "id": str(issue.number),
            "title": issue.title,
            "body": issue.body or "",
        }
    except Exception:
        return None


def fetch_github_pr(pr_id: str) -> Optional[dict]:
    """
    Fetch a GitHub PR by ID or URL.

    For demo: accepts "test-pr-1", etc.
    For real GitHub: would use GitHub API

    Args:
        pr_id: GitHub PR ID, URL, or test ID

    Returns:
        dict with id, title, body, branch or None if not found
    """
    # Check mock data first
    if pr_id in MOCK_PRS:
        return MOCK_PRS[pr_id]

    # Try real GitHub API
    try:
        repo = _get_repo()
        pr = repo.get_pull(int(pr_id))
        return {
            "id": str(pr.number),
            "title": pr.title,
            "body": pr.body or "",
            "branch": pr.head.ref
        }
    except Exception:
        return None


def create_github_issue(title: str, body: str, labels: list = None) -> Optional[Dict[str, Any]]:
    """
    Create a new GitHub issue.

    For demo/testing: creates mock issue if GITHUB_TOKEN not set
    For real GitHub: uses GitHub API

    Args:
        title: Issue title
        body: Issue body/description
        labels: Optional list of label names

    Returns:
        dict with issue details or None if failed
    """
    # For demo/testing when no GitHub token is configured
    if not config.GITHUB_TOKEN:
        import time
        mock_id = f"mock-issue-{int(time.time())}"
        MOCK_ISSUES[mock_id] = {
            "id": mock_id,
            "title": title,
            "body": body,
        }
        print(f"✓ Created mock issue (no GITHUB_TOKEN configured): {mock_id}")
        return {
            "id": mock_id,
            "title": title,
            "body": body,
            "url": f"https://github.com/mock/{mock_id}",
            "number": len(MOCK_ISSUES)
        }

    try:
        repo = _get_repo()
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels or []
        )
        return {
            "id": str(issue.number),
            "title": issue.title,
            "body": issue.body,
            "url": issue.html_url,
            "number": issue.number
        }
    except Exception as e:
        print(f"Failed to create GitHub issue: {e}")
        return None


def create_github_pr(title: str, body: str, head: str, base: str = "main", draft: bool = True) -> Optional[Dict[str, Any]]:
    """
    Create a new GitHub pull request.

    Args:
        title: PR title
        body: PR body/description
        head: Head branch name
        base: Base branch name (default: main)
        draft: Whether to create as draft PR

    Returns:
        dict with PR details or None if failed
    """
    try:
        repo = _get_repo()
        pr = repo.create_pull(
            title=title,
            body=body,
            head=head,
            base=base,
            draft=draft
        )
        return {
            "id": str(pr.number),
            "title": pr.title,
            "body": pr.body,
            "url": pr.html_url,
            "number": pr.number,
            "branch": pr.head.ref
        }
    except Exception as e:
        print(f"Failed to create GitHub PR: {e}")
        return None