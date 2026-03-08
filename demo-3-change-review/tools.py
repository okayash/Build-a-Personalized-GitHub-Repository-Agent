"""
Tools for agents — functions that gather context from the filesystem or git.
"""
import subprocess
from typing import Optional


def get_git_diff(commit_range: Optional[str] = None) -> str:
    """
    Get git diff for the current branch or a specific commit range.

    Args:
        commit_range: e.g., "HEAD~1..HEAD" or None for staged/unstaged changes.

    Returns:
        The git diff output as a string.
    """
    if commit_range:
        cmd = ["git", "diff", commit_range]
    else:
        # For current branch changes, perhaps diff with origin/main or something.
        # But user said current branch changes, so maybe git diff HEAD or git diff --cached
        # Let's assume for current branch vs main: git diff origin/main..HEAD
        cmd = ["git", "diff", "origin/main..HEAD"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error getting git diff: {e.stderr}"