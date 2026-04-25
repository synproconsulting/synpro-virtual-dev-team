"""Automatic PR review functionality."""

import os
from typing import Optional, List, Dict
import httpx
from enum import Enum


class ReviewStatus(Enum):
    """PR review status options."""
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"


class PRAutoReview:
    """Handles automatic PR review and commenting."""

    def __init__(self, repo_url: Optional[str] = None, api_token: Optional[str] = None):
        """
        Initialize PR auto-review.

        Args:
            repo_url: Repository API base URL
            api_token: Authentication token for repo access
        """
        self.repo_url = repo_url or os.getenv("REPO_API_URL", "")
        self.api_token = api_token or os.getenv("REPO_API_TOKEN", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def analyze_pr(self, pr_number: int) -> Dict[str, any]:
        """
        Analyze PR for automatic review.

        Args:
            pr_number: Pull request number

        Returns:
            Dictionary containing analysis results
        """
        if not self.repo_url or not self.api_token:
            raise ValueError("Repository API credentials not configured")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.repo_url}/pulls/{pr_number}",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            pr_data = response.json()

            # Fetch PR files
            files_response = await client.get(
                f"{self.repo_url}/pulls/{pr_number}/files",
                headers=self.headers,
                timeout=30.0,
            )
            files_response.raise_for_status()
            files = files_response.json()

            return {
                "pr_data": pr_data,
                "files": files,
                "file_count": len(files),
                "additions": sum(f.get("additions", 0) for f in files),
                "deletions": sum(f.get("deletions", 0) for f in files),
            }

    async def submit_review(
        self,
        pr_number: int,
        status: ReviewStatus,
        comments: List[str],
        body: Optional[str] = None,
    ) -> dict:
        """
        Submit an automatic review for a PR.

        Args:
            pr_number: Pull request number
            status: Review status (approved, changes requested, etc.)
            comments: List of review comments
            body: Optional review body text

        Returns:
            Dictionary containing review submission result
        """
        if not self.repo_url or not self.api_token:
            raise ValueError("Repository API credentials not configured")

        review_body = body or self._generate_review_body(comments)

        payload = {
            "event": status.value,
            "body": review_body,
            "comments": [{"body": comment} for comment in comments],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.repo_url}/pulls/{pr_number}/reviews",
                json=payload,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    def _generate_review_body(self, comments: List[str]) -> str:
        """
        Generate review body from comments.

        Args:
            comments: List of review comments

        Returns:
            Formatted review body text
        """
        if not comments:
            return "Automated review completed."

        return f"## Automated Review\n\n{len(comments)} items identified:\n\n" + "\n".join(
            f"- {comment}" for comment in comments[:5]
        )

    async def auto_approve_if_eligible(self, pr_number: int) -> Optional[dict]:
        """
        Automatically approve PR if it meets criteria.

        Args:
            pr_number: Pull request number

        Returns:
            Review result if approved, None otherwise
        """
        analysis = await self.analyze_pr(pr_number)

        # Simple eligibility criteria
        if (
            analysis["file_count"] <= 5
            and analysis["additions"] <= 100
            and analysis["deletions"] <= 50
        ):
            return await self.submit_review(
                pr_number,
                ReviewStatus.APPROVED,
                ["Automated approval: PR meets size and complexity criteria."],
            )

        return None
