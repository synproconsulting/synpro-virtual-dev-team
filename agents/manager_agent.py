"""
Manager Agent - Handles Jira workflow transitions with exponential backoff retry logic.

The Manager Agent is responsible for:
- Transitioning Jira issues through their workflow states
- Implementing exponential backoff for failed API calls
- Managing issue assignments and status updates
- Coordinating with other agents in the system
"""

import os
import time
import asyncio
from typing import Optional, Dict, Any, List
from enum import Enum
import base64
import httpx
from dataclasses import dataclass


# ── Configuration ─────────────────────────────────────────────────────────────────────

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY", "SDT1")

# Retry configuration
DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 60.0  # seconds
DEFAULT_EXPONENTIAL_BASE = 2


class TransitionStatus(Enum):
    """Status of a transition attempt."""
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"


@dataclass
class TransitionResult:
    """Result of a transition operation."""
    status: TransitionStatus
    issue_key: str
    transition_id: Optional[str] = None
    transition_name: Optional[str] = None
    attempts: int = 0
    total_time: float = 0.0
    error_message: Optional[str] = None
    final_status: Optional[str] = None


# ── Jira Client with Retry Logic ─────────────────────────────────────────────────────


class JiraRetryClient:
    """
    Jira client with exponential backoff retry logic.
    
    Implements exponential backoff with jitter for resilient API calls.
    """
    
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
        exponential_base: float = DEFAULT_EXPONENTIAL_BASE,
    ):
        """
        Initialize the Jira retry client.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.base_url = JIRA_BASE_URL
        self.auth_headers = self._create_auth_headers()
    
    def _create_auth_headers(self) -> Dict[str, str]:
        """Create authorization headers for Jira API."""
        if not JIRA_EMAIL or not JIRA_API_TOKEN:
            raise ValueError("JIRA_EMAIL and JIRA_API_TOKEN must be configured")
        
        creds = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
        encoded = base64.b64encode(creds.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with jitter.
        
        Args:
            attempt: Current retry attempt number (0-indexed)
        
        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # Cap at max_delay
        delay = min(delay, self.max_delay)
        
        # Add jitter (±25% randomness) to prevent thundering herd
        import random
        jitter = delay * 0.25 * (2 * random.random() - 1)
        delay_with_jitter = delay + jitter
        
        return max(0, delay_with_jitter)
    
    async def _execute_with_retry(
        self,
        operation: str,
        url: str,
        method: str = "GET",
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Execute HTTP request with exponential backoff retry logic.
        
        Args:
            operation: Description of the operation for logging
            url: Full URL to request
            method: HTTP method (GET, POST, PUT, etc.)
            json_data: JSON body for POST/PUT requests
            params: Query parameters
        
        Returns:
            httpx.Response object
        
        Raises:
            httpx.HTTPError: If all retries are exhausted
        """
        last_exception = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    # Execute the request
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.auth_headers,
                        json=json_data,
                        params=params,
                    )
                    
                    # Check for success status codes
                    if response.status_code < 400:
                        if attempt > 0:
                            print(f"✓ {operation} succeeded after {attempt} retries")
                        return response
                    
                    # Check if we should retry based on status code
                    # Retry on 5xx errors and 429 (rate limit)
                    if response.status_code in (429, 500, 502, 503, 504):
                        if attempt < self.max_retries:
                            delay = self._calculate_delay(attempt)
                            print(
                                f"⚠ {operation} failed with status {response.status_code}, "
                                f"retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries})"
                            )
                            await asyncio.sleep(delay)
                            continue
                    
                    # Non-retryable error, raise immediately
                    response.raise_for_status()
                    return response
                
                except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        delay = self._calculate_delay(attempt)
                        print(
                            f"⚠ {operation} failed with {type(e).__name__}, "
                            f"retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise
                
                except httpx.HTTPError as e:
                    # Non-retryable HTTP error
                    raise
        
        # If we get here, all retries were exhausted
        if last_exception:
            raise last_exception
        else:
            raise httpx.HTTPError(f"All {self.max_retries} retries exhausted for {operation}")
    
    async def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Get issue details with retry logic.
        
        Args:
            issue_key: Jira issue key (e.g., "SDT1-44")
        
        Returns:
            Issue data dictionary
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        response = await self._execute_with_retry(
            operation=f"Get issue {issue_key}",
            url=url,
            method="GET",
        )
        return response.json()
    
    async def get_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get available transitions for an issue with retry logic.
        
        Args:
            issue_key: Jira issue key
        
        Returns:
            List of available transitions
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        response = await self._execute_with_retry(
            operation=f"Get transitions for {issue_key}",
            url=url,
            method="GET",
        )
        data = response.json()
        return data.get("transitions", [])
    
    async def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        fields: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None,
    ) -> TransitionResult:
        """
        Transition an issue to a new status with retry logic.
        
        Args:
            issue_key: Jira issue key
            transition_id: ID of the transition to execute
            fields: Optional fields to update during transition
            comment: Optional comment to add
        
        Returns:
            TransitionResult with operation details
        """
        start_time = time.time()
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        
        body: Dict[str, Any] = {"transition": {"id": transition_id}}
        if fields:
            body["fields"] = fields
        if comment:
            body["update"] = {
                "comment": [{"add": {"body": comment}}]
            }
        
        try:
            response = await self._execute_with_retry(
                operation=f"Transition {issue_key}",
                url=url,
                method="POST",
                json_data=body,
            )
            
            total_time = time.time() - start_time
            
            # Get updated issue status
            issue_data = await self.get_issue(issue_key)
            final_status = issue_data.get("fields", {}).get("status", {}).get("name")
            
            return TransitionResult(
                status=TransitionStatus.SUCCESS,
                issue_key=issue_key,
                transition_id=transition_id,
                attempts=1,  # Will be updated by retry mechanism
                total_time=total_time,
                final_status=final_status,
            )
        
        except Exception as e:
            total_time = time.time() - start_time
            return TransitionResult(
                status=TransitionStatus.FAILED,
                issue_key=issue_key,
                transition_id=transition_id,
                attempts=self.max_retries + 1,
                total_time=total_time,
                error_message=str(e),
            )
    
    async def transition_issue_by_name(
        self,
        issue_key: str,
        target_status: str,
        fields: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None,
    ) -> TransitionResult:
        """
        Transition an issue to a target status by status name.
        
        This method finds the appropriate transition ID for the target status
        and executes the transition with retry logic.
        
        Args:
            issue_key: Jira issue key
            target_status: Target status name (e.g., "In Progress", "Done")
            fields: Optional fields to update during transition
            comment: Optional comment to add
        
        Returns:
            TransitionResult with operation details
        """
        try:
            # Get available transitions
            transitions = await self.get_transitions(issue_key)
            
            # Find transition that leads to target status
            transition_id = None
            transition_name = None
            for trans in transitions:
                to_status = trans.get("to", {}).get("name", "")
                if to_status.lower() == target_status.lower():
                    transition_id = trans["id"]
                    transition_name = trans["name"]
                    break
            
            if not transition_id:
                available = [t.get("to", {}).get("name", "") for t in transitions]
                return TransitionResult(
                    status=TransitionStatus.FAILED,
                    issue_key=issue_key,
                    attempts=1,
                    error_message=f"No transition found to '{target_status}'. Available: {available}",
                )
            
            # Execute the transition
            result = await self.transition_issue(
                issue_key=issue_key,
                transition_id=transition_id,
                fields=fields,
                comment=comment,
            )
            result.transition_name = transition_name
            return result
        
        except Exception as e:
            return TransitionResult(
                status=TransitionStatus.FAILED,
                issue_key=issue_key,
                attempts=1,
                error_message=str(e),
            )
    
    async def bulk_transition(
        self,
        transitions: List[Dict[str, Any]],
    ) -> List[TransitionResult]:
        """
        Execute multiple transitions with retry logic.
        
        Args:
            transitions: List of transition dictionaries with keys:
                - issue_key: str
                - target_status: str (optional if transition_id provided)
                - transition_id: str (optional if target_status provided)
                - fields: dict (optional)
                - comment: str (optional)
        
        Returns:
            List of TransitionResult objects
        """
        results = []
        
        for trans in transitions:
            issue_key = trans["issue_key"]
            
            if "transition_id" in trans:
                result = await self.transition_issue(
                    issue_key=issue_key,
                    transition_id=trans["transition_id"],
                    fields=trans.get("fields"),
                    comment=trans.get("comment"),
                )
            elif "target_status" in trans:
                result = await self.transition_issue_by_name(
                    issue_key=issue_key,
                    target_status=trans["target_status"],
                    fields=trans.get("fields"),
                    comment=trans.get("comment"),
                )
            else:
                result = TransitionResult(
                    status=TransitionStatus.FAILED,
                    issue_key=issue_key,
                    attempts=0,
                    error_message="Must provide either 'transition_id' or 'target_status'",
                )
            
            results.append(result)
        
        return results


# ── Manager Agent ─────────────────────────────────────────────────────────────────────


class ManagerAgent:
    """
    Manager Agent for coordinating Jira workflow transitions.
    
    The Manager Agent orchestrates issue lifecycle management with robust
    retry logic and error handling.
    """
    
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
    ):
        """
        Initialize the Manager Agent.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds before first retry
        """
        self.client = JiraRetryClient(
            max_retries=max_retries,
            base_delay=base_delay,
        )
    
    async def start_work(
        self,
        issue_key: str,
        assignee: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> TransitionResult:
        """
        Transition an issue to 'In Progress' status.
        
        Args:
            issue_key: Jira issue key
            assignee: Optional assignee to set
            comment: Optional comment
        
        Returns:
            TransitionResult
        """
        fields = {}
        if assignee:
            fields["assignee"] = {"name": assignee}
        
        return await self.client.transition_issue_by_name(
            issue_key=issue_key,
            target_status="In Progress",
            fields=fields if fields else None,
            comment=comment or "Work started by Manager Agent",
        )
    
    async def complete_work(
        self,
        issue_key: str,
        comment: Optional[str] = None,
    ) -> TransitionResult:
        """
        Transition an issue to 'Done' status.
        
        Args:
            issue_key: Jira issue key
            comment: Optional comment
        
        Returns:
            TransitionResult
        """
        return await self.client.transition_issue_by_name(
            issue_key=issue_key,
            target_status="Done",
            comment=comment or "Work completed by Manager Agent",
        )
    
    async def move_to_code_review(
        self,
        issue_key: str,
        comment: Optional[str] = None,
    ) -> TransitionResult:
        """
        Transition an issue to 'Code Review' status.
        
        Args:
            issue_key: Jira issue key
            comment: Optional comment
        
        Returns:
            TransitionResult
        """
        return await self.client.transition_issue_by_name(
            issue_key=issue_key,
            target_status="Code Review",
            comment=comment or "Ready for code review",
        )
    
    async def move_to_testing(
        self,
        issue_key: str,
        comment: Optional[str] = None,
    ) -> TransitionResult:
        """
        Transition an issue to 'Testing' or 'QA' status.
        
        Args:
            issue_key: Jira issue key
            comment: Optional comment
        
        Returns:
            TransitionResult
        """
        # Try "Testing" first, fall back to "QA"
        result = await self.client.transition_issue_by_name(
            issue_key=issue_key,
            target_status="Testing",
            comment=comment or "Ready for testing",
        )
        
        if result.status == TransitionStatus.FAILED and "No transition found" in (result.error_message or ""):
            result = await self.client.transition_issue_by_name(
                issue_key=issue_key,
                target_status="QA",
                comment=comment or "Ready for QA",
            )
        
        return result
    
    async def get_issue_status(self, issue_key: str) -> Optional[str]:
        """
        Get current status of an issue.
        
        Args:
            issue_key: Jira issue key
        
        Returns:
            Current status name or None if error
        """
        try:
            issue = await self.client.get_issue(issue_key)
            return issue.get("fields", {}).get("status", {}).get("name")
        except Exception as e:
            print(f"Error getting status for {issue_key}: {e}")
            return None


# ── Factory Function ──────────────────────────────────────────────────────────────────


def create_manager_agent(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
) -> ManagerAgent:
    """
    Factory function to create a Manager Agent instance.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds before first retry
    
    Returns:
        ManagerAgent instance
    """
    return ManagerAgent(max_retries=max_retries, base_delay=base_delay)
