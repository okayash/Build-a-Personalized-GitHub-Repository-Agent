"""
GitHub tools — fetch issues and PRs for improvement analysis.

For demo purposes, includes mock data for testing without real GitHub API.
"""
from typing import Optional


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

    # In production, would call GitHub API:
    # client = GitHub(auth=PAT)
    # repo = client.get_repo(owner/repo)
    # issue = repo.get_issue(int(issue_id))
    # return {"id": issue_id, "title": issue.title, "body": issue.body}

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

    # In production, would call GitHub API:
    # client = GitHub(auth=PAT)
    # repo = client.get_repo(owner/repo)
    # pr = repo.get_pull(int(pr_id))
    # return {
    #     "id": pr_id,
    #     "title": pr.title,
    #     "body": pr.body,
    #     "branch": pr.head.ref
    # }

    return None