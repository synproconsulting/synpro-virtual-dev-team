"""Tests for PR auto review functionality."""

import pytest
from src.auth.pr_auto_review import (
    PRAutoReview,
    PRData,
    ReviewRule,
    ReviewStatus
)


@pytest.fixture
def pr_reviewer():
    """Create a PR auto reviewer instance."""
    return PRAutoReview()


@pytest.fixture
def valid_pr_data():
    """Create valid PR data for testing."""
    return PRData(
        pr_number=123,
        title="[SDT1-29] Add auto review feature",
        description="This PR adds auto review functionality",
        files_changed=["src/auth/pr_auto_review.py", "tests/test_pr_auto_review.py"],
        lines_added=200,
        lines_removed=50,
        author="developer",
        branch="feature/auto-review"
    )


@pytest.mark.asyncio
async def test_review_pr_success(pr_reviewer, valid_pr_data):
    """Test successful PR review with no violations."""
    result = await pr_reviewer.review_pr(valid_pr_data)
    
    assert result["pr_number"] == 123
    assert result["status"] == ReviewStatus.APPROVED.value
    assert len(result["violations"]) == 0


@pytest.mark.asyncio
async def test_review_pr_invalid_title(pr_reviewer, valid_pr_data):
    """Test PR review with invalid title."""
    valid_pr_data.title = "Add feature without ticket"
    result = await pr_reviewer.review_pr(valid_pr_data)
    
    assert result["status"] == ReviewStatus.COMMENTED.value
    assert "pr_title" in result["violations"]
    assert any(c["rule"] == "pr_title" for c in result["comments"])


@pytest.mark.asyncio
async def test_review_pr_too_large(pr_reviewer, valid_pr_data):
    """Test PR review with excessive size."""
    valid_pr_data.lines_added = 600
    result = await pr_reviewer.review_pr(valid_pr_data)
    
    assert "pr_size" in result["violations"]
    assert any(c["rule"] == "pr_size" for c in result["comments"])


@pytest.mark.asyncio
async def test_review_pr_no_tests(pr_reviewer, valid_pr_data):
    """Test PR review without test files."""
    valid_pr_data.files_changed = ["src/auth/feature.py"]
    result = await pr_reviewer.review_pr(valid_pr_data)
    
    assert "test_coverage" in result["violations"]
    assert any(c["rule"] == "test_coverage" for c in result["comments"])


@pytest.mark.asyncio
async def test_review_pr_with_secrets(pr_reviewer, valid_pr_data):
    """Test PR review detecting potential secrets."""
    valid_pr_data.description = "Added API_KEY = 'secret123' for authentication"
    result = await pr_reviewer.review_pr(valid_pr_data)
    
    assert result["status"] == ReviewStatus.CHANGES_REQUESTED.value
    assert "no_secrets" in result["violations"]
    assert any(c["severity"] == "error" for c in result["comments"])


def test_default_rules(pr_reviewer):
    """Test that default rules are properly initialized."""
    assert len(pr_reviewer.rules) == 4
    rule_names = [r.name for r in pr_reviewer.rules]
    
    assert "pr_title" in rule_names
    assert "pr_size" in rule_names
    assert "test_coverage" in rule_names
    assert "no_secrets" in rule_names


def test_custom_rules():
    """Test PR reviewer with custom rules."""
    custom_rules = [
        ReviewRule("custom_rule", "Custom validation", severity="error")
    ]
    reviewer = PRAutoReview(rules=custom_rules)
    
    assert len(reviewer.rules) == 1
    assert reviewer.rules[0].name == "custom_rule"


@pytest.mark.asyncio
async def test_multiple_violations(pr_reviewer, valid_pr_data):
    """Test PR with multiple rule violations."""
    valid_pr_data.title = "Bad title"
    valid_pr_data.files_changed = ["src/feature.py"]
    valid_pr_data.lines_added = 600
    
    result = await pr_reviewer.review_pr(valid_pr_data)
    
    assert len(result["violations"]) >= 2
    assert len(result["comments"]) >= 2
