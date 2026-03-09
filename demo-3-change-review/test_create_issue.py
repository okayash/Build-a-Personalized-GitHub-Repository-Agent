#!/usr/bin/env python3
"""
Test script to create a sample GitHub issue
"""
import sys
sys.path.append('/Users/ashleyfong/Documents/Build-a-Personalized-GitHub-Repository-Agent/demo-3-change-review')

from tools.gh_tools import create_github_issue

def main():
    print("Creating test sample issue...")

    result = create_github_issue(
        title='Test Sample Issue - User Notifications Feature',
        body='''This is a test issue created to demonstrate the GitHub Repository Agent functionality.

## Description
Add a new feature for user notifications to improve user experience.

## Requirements
- Email notifications
- In-app notifications
- Notification preferences

## Acceptance Criteria
- Users can opt-in/opt-out of notifications
- Notifications are delivered reliably
- Settings are persisted''',
        labels=['enhancement', 'test']
    )

    if result:
        print("✓ Issue created successfully!")
        print(f"ID: {result['id']}")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
    else:
        print("✗ Failed to create issue")

if __name__ == "__main__":
    main()