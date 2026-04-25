"""Tests for PR auto-review functionality."""

import pytest
from unittest.mock import AsyncMock, patch
from src.auth.pr_auto_review import PRAutoReview, ReviewStatus
import httpx


@pytest.fixture
def pr_reviewer():
    """Create PRAutoReview instance for testing."""
    return PRAutoReview(
        repo_url="https://api.github.com/repos/test/repo",
        api_token="test-token-456",
    )


@pytest.mark.asyncio
async def test_analyze_pr_success(pr_reviewer):
    """Test successful PR analysis."""
    mock_pr_data = {"number": 42, "title": "Test PR", "state": "open"}
    mock_files = [
        {"filename": "test.py", "additions": 10, "deletions": 5},
        {"filename": "main.py", "additions": 20, "deletions": 3},
    ]

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.side_effect = [mock_pr_data, mock_files]
        mock_get.return_value.raise_for_status = lambda: None

        result = await pr_reviewer.analyze_pr(42)

        assert result["file_count"] == 2
        assert result["additions"] == 30
        assert result["deletions"] == 8
        assert result["pr_data"]["number"] == 42


@pytest.mark.asyncio
async def test_submit_review_approved(pr_reviewer):
    """Test submitting an approved review."""
    mock_response = {"id": "review-123", "state": "APPROVED"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        result = await pr_reviewer.submit_review(
            pr_number=42,
            status=ReviewStatus.APPROVED,
            comments=["Looks good!"],
        )

        assert result["state"] == "APPROVED"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_auto_approve_if_eligible_approved(pr_reviewer):
    """Test auto-approval for eligible PR."""
    mock_pr_data = {"number": 42}
    mock_files = [{"additions": 50, "deletions": 20}]
    mock_review = {"id": "review-123", "state": "APPROVED"}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_get.return_value.json.side_effect = [mock_pr_data, mock_files]
        mock_get.return_value.raise_for_status = lambda: None
        mock_post.return_value.json.return_value = mock_review
        mock_post.return_value.raise_for_status = lambda: None

        result = await pr_reviewer.auto_approve_if_eligible(42)

        assert result is not None
        assert result["state"] == "APPROVED"


@pytest.mark.asyncio
async def test_auto_approve_if_eligible_not_eligible(pr_reviewer):
    """Test auto-approval for ineligible PR."""
    mock_pr_data = {"number": 42}
    mock_files = [{"additions": 200, "deletions": 100}]  # Too large

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.side_effect = [mock_pr_data, mock_files]
        mock_get.return_value.raise_for_status = lambda: None

        result = await pr_reviewer.auto_approve_if_eligible(42)

        assert result is None


@pytest.mark.asyncio
async def test_analyze_pr_missing_credentials():
    """Test PR analysis with missing credentials."""
    reviewer = PRAutoReview(repo_url="", api_token="")

    with pytest.raises(ValueError, match="Repository API credentials not configured"):
        await reviewer.analyze_pr(42)


def test_generate_review_body(pr_reviewer):
    """Test review body generation."""
    comments = ["Issue 1", "Issue 2", "Issue 3"]
    body = pr_reviewer._generate_review_body(comments)

    assert "Automated Review" in body
    assert "3 items identified" in body
    assert "Issue 1" in body
