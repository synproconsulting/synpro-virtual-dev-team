"""Tests for PR auto review functionality."""

import pytest
from src.auth.pr_auto_review import PRAutoReview, PRMetadata, ReviewStatus


@pytest.fixture
def pr_auto_review():
    """Fixture for PR auto review."""
    return PRAutoReview(team_id="team-alpha")


@pytest.fixture
def valid_pr_metadata():
    """Fixture for valid PR metadata."""
    return PRMetadata(
        pr_id="PR-123",
        title="Add new feature",
        author="developer1",
        branch="feature/new-feature",
        target_branch="main",
        files_changed=5,
        lines_added=100,
        lines_removed=20
    )


@pytest.fixture
def large_pr_metadata():
    """Fixture for large PR metadata."""
    return PRMetadata(
        pr_id="PR-456",
        title="Large refactor",
        author="developer2",
        branch="feature/refactor",
        target_branch="main",
        files_changed=100,
        lines_added=5000,
        lines_removed=3000
    )


def test_pr_auto_review_initialization(pr_auto_review):
    """Test PR auto review initialization."""
    assert pr_auto_review.team_id == "team-alpha"
    assert pr_auto_review.review_rules is not None
    assert len(pr_auto_review._review_history) == 0


def test_review_valid_pr(pr_auto_review, valid_pr_metadata):
    """Test reviewing a valid PR."""
    result = pr_auto_review.review_pr(valid_pr_metadata)
    
    assert result["pr_id"] == "PR-123"
    assert result["status"] == ReviewStatus.APPROVED.value
    assert all(result["checks"].values())
    assert len(result["comments"]) == 0


def test_review_large_pr(pr_auto_review, large_pr_metadata):
    """Test reviewing a large PR."""
    result = pr_auto_review.review_pr(large_pr_metadata)
    
    assert result["pr_id"] == "PR-456"
    assert result["status"] == ReviewStatus.CHANGES_REQUESTED.value
    assert not result["checks"]["size_check"]
    assert not result["checks"]["lines_check"]
    assert len(result["comments"]) > 0


def test_invalid_branch_name(pr_auto_review):
    """Test PR with invalid branch name."""
    pr_metadata = PRMetadata(
        pr_id="PR-789",
        title="Test PR",
        author="developer3",
        branch="invalid-branch",
        target_branch="main",
        files_changed=5,
        lines_added=50,
        lines_removed=10
    )
    
    result = pr_auto_review.review_pr(pr_metadata)
    
    assert not result["checks"]["branch_name_check"]
    assert any("naming conventions" in comment for comment in result["comments"])


def test_invalid_target_branch(pr_auto_review, valid_pr_metadata):
    """Test PR with invalid target branch."""
    valid_pr_metadata.target_branch = "random-branch"
    result = pr_auto_review.review_pr(valid_pr_metadata)
    
    assert not result["checks"]["target_branch_check"]
    assert any("Target branch" in comment for comment in result["comments"])


def test_review_history(pr_auto_review, valid_pr_metadata):
    """Test review history tracking."""
    pr_auto_review.review_pr(valid_pr_metadata)
    pr_auto_review.review_pr(valid_pr_metadata)
    
    history = pr_auto_review.get_review_history()
    assert len(history) == 2
    assert all("pr_id" in review for review in history)


def test_custom_review_rules():
    """Test custom review rules."""
    custom_rules = {
        "max_files_changed": 10,
        "max_lines_changed": 200
    }
    reviewer = PRAutoReview(team_id="team-beta", review_rules=custom_rules)
    
    assert reviewer.review_rules["max_files_changed"] == 10
    assert reviewer.review_rules["max_lines_changed"] == 200
