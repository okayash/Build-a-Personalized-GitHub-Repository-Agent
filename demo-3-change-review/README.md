# Change Review

> **Personalized GitHub Repository Agent** — AI-Augmented Software Engineering
> Missouri S&T

A multi-agent AI system that reviews code changes, drafts GitHub issues/PRs with human approval, and improves existing GitHub content.

## Features

- **Review Changes**: Analyze git diffs and assess risks
- **Draft Issues/PRs**: Create structured drafts from code analysis or explicit instructions
- **Human Approval**: Review drafts before creating GitHub items
- **Improve Content**: Critique and improve existing GitHub issues/PRs
- **Multi-Agent Architecture**: Planning, Tool Use, Reflection patterns

## Pipeline

```
Review: Analyzer → Categorizer → RiskAssessor → DecisionMaker
Draft: Planner → Writer → Gatekeeper → Approval
Improve: Reviewer → Planner → Improver → Gatekeeper → Approval
```

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set up Ollama: `ollama pull llama3.2:3b`
3. Configure GitHub: Copy `.env.example` to `.env` and add your GitHub token and repository

## Usage

### CLI

```bash
# Review current branch changes
python cli.py review

# Review specific commit range
python cli.py review --range HEAD~3..HEAD

# Draft an issue from analysis
python cli.py review --draft issue

# Draft a PR from explicit instruction
python cli.py draft pr --instruction "Add rate limiting to login endpoint"

# List pending drafts
python cli.py approve --list

# Review a draft
python cli.py approve abc12345

# Approve and create GitHub item
python cli.py approve abc12345 --yes

# Reject a draft
python cli.py approve abc12345 --no

# Improve existing issue
python cli.py improve --issue 42

# Improve existing PR
python cli.py improve --pr 17
```

### Web UI

```bash
uvicorn web.main:app --reload --port 8003
```

## Configuration

Create a `.env` file with:

```
OLLAMA_HOST=http://localhost:11434
AGENT_MODEL=llama3.2:3b
MAX_TOKENS=2048
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=owner/repository
```

## Agent Patterns

- **Planning**: Structured planning before drafting
- **Tool Use**: Real git/GitHub API calls, no fabricated data
- **Reflection**: Critic agent validates output quality
- **Multi-Agent**: Specialized roles with clear responsibilities