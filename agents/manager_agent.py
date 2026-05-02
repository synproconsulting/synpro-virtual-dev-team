"""
Manager Agent - Handles Jira workflow transitions with exponential backoff retry logic.

The Manager Agent is responsible for:
- Transitioning Jira issues through their workflow states
- Implementing exponential backoff for failed API calls
- Managing issue assignments and status updates
- Coordinating with other agents in the system
- Reviewing PRs with intelligent diff truncation
- Preventing infinite retrigger loops with configurable caps
"""

import os
import sys
import time
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import base64
import httpx
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Add tools to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.diff_handler import truncate_diff_smart, get_new_files_summary


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

# Retrigger loop protection configuration
DEFAULT_MAX_RETRIGGERS = 3  # Maximum number of times to retrigger the same operation
DEFAULT_RETRIGGER_WINDOW = 3600  # Time window in seconds (1 hour) to track retriggers
DEFAULT_COOLDOWN_PERIOD = 300  # Cooldown period in seconds (5 minutes) after hitting limit

# Diff review configuration
DEFAULT_DIFF_MAX_CHARS = 50000


class TransitionStatus(Enum):
    """Status of a transition attempt."""
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"
    MAX_RETRIGGERS_EXCEEDED = "max_retriggers_exceeded"


@dataclass
class TransitionResult:
    """Result of a transition operation."""
    status: TransitionStatus
    issue_key: str
    transition_id: Optional[str] = None
    transition_name: Optional[str] = None
    attempts: int = 0
    retrigger_count: int = 0
    total_time: float = 0.0
    error_message: Optional[str] = None
    final_status: Optional[str] = None


@dataclass
class DiffReviewResult:
    """Result of a diff review operation."""
    truncated_diff: str
    metadata: Dict[str, Any]
    new_files_summary: List[Dict[str, Any]]
    review_comments: List[str]
    
    @property
    def has_new_files(self) -> bool:
        """Check if the diff contains new files."""
        return len(self.new_files_summary) > 0
    
    @property
    def was_truncated(self) -> bool:
        """Check if the diff was truncated."""
        return self.metadata.get("truncated", False)


@dataclass
class RetriggerAttempt:
    """Record of a single retrigger attempt."""
    timestamp: datetime
    operation: str
    issue_key: str
    status: str


# ── Retrigger Tracker ─────────────────────────────────────────────────────────────────


class RetriggerTracker:
    """
    Tracks retrigger attempts to prevent infinite loops.
    
    This class maintains a history of retrigger attempts per issue/operation
    and enforces configurable limits to prevent infinite retrigger cycles.
    """
    
    def __init__(
        self,
        max_retriggers: int = DEFAULT_MAX_RETRIGGERS,
        window_seconds: int = DEFAULT_RETRIGGER_WINDOW,
        cooldown_seconds: int = DEFAULT_COOLDOWN_PERIOD,
    ):
        """
        Initialize the retrigger tracker.
        
        Args:
            max_retriggers: Maximum retriggers allowed within the time window
            window_seconds: Time window in seconds to track retriggers
            cooldown_seconds: Cooldown period after hitting limit
        """
        self.max_retriggers = max_retriggers
        self.window_seconds = window_seconds
        self.cooldown_seconds = cooldown_seconds
        
        # Track retrigger attempts: {(issue_key, operation): [RetriggerAttempt]}
        self._attempts: Dict[Tuple[str, str], List[RetriggerAttempt]] = {}
        
        # Track when an issue/operation combo was put in cooldown
        self._cooldown_until: Dict[Tuple[str, str], datetime] = {}
    
    def _get_key(self, issue_key: str, operation: str) -> Tuple[str, str]:
        """Generate tracking key for issue/operation combination."""
        return (issue_key, operation)
    
    def _cleanup_old_attempts(
        self,
        key: Tuple[str, str],
        current_time: datetime,
    ) -> None:
        """
        Remove attempts outside the tracking window.
        
        Args:
            key: Tracking key
            current_time: Current timestamp
        """
        if key not in self._attempts:
            return
        
        cutoff_time = current_time - timedelta(seconds=self.window_seconds)
        self._attempts[key] = [
            attempt for attempt in self._attempts[key]
            if attempt.timestamp > cutoff_time
        ]
        
        # Clean up empty lists
        if not self._attempts[key]:
            del self._attempts[key]
    
    def can_retrigger(
        self,
        issue_key: str,
        operation: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a retrigger is allowed for the given issue/operation.
        
        Args:
            issue_key: Jira issue key
            operation: Operation name (e.g., "transition_to_in_progress")
        
        Returns:
            Tuple of (can_retrigger: bool, reason: Optional[str])
            If can_retrigger is False, reason contains explanation
        """
        key = self._get_key(issue_key, operation)
        current_time = datetime.now()
        
        # Check if in cooldown period
        if key in self._cooldown_until:
            cooldown_end = self._cooldown_until[key]
            if current_time < cooldown_end:
                remaining = int((cooldown_end - current_time).total_seconds())
                return False, (
                    f"Operation '{operation}' for {issue_key} is in cooldown. "
                    f"Retry after {remaining} seconds."
                )
            else:
                # Cooldown expired, remove it
                del self._cooldown_until[key]
        
        # Clean up old attempts
        self._cleanup_old_attempts(key, current_time)
        
        # Check retrigger count within window
        if key in self._attempts:
            recent_attempts = len(self._attempts[key])
            if recent_attempts >= self.max_retriggers:
                # Put into cooldown
                self._cooldown_until[key] = current_time + timedelta(
                    seconds=self.cooldown_seconds
                )
                return False, (
                    f"Maximum retrigger limit ({self.max_retriggers}) exceeded for "
                    f"operation '{operation}' on {issue_key} within {self.window_seconds}s window. "
                    f"Entering cooldown period of {self.cooldown_seconds}s."
                )
        
        return True, None
    
    def record_retrigger(
        self,
        issue_key: str,
        operation: str,
        status: str,
    ) -> int:
        """
        Record a retrigger attempt.
        
        Args:
            issue_key: Jira issue key
            operation: Operation name
            status: Status of the attempt
        
        Returns:
            Current retrigger count within the window
        """
        key = self._get_key(issue_key, operation)
        current_time = datetime.now()
        
        # Clean up old attempts first
        self._cleanup_old_attempts(key, current_time)
        
        # Record new attempt
        attempt = RetriggerAttempt(
            timestamp=current_time,
            operation=operation,
            issue_key=issue_key,
            status=status,
        )
        
        if key not in self._attempts:
            self._attempts[key] = []
        
        self._attempts[key].append(attempt)
        
        return len(self._attempts[key])
    
    def get_retrigger_count(
        self,
        issue_key: str,
        operation: str,
    ) -> int:
        """
        Get current retrigger count for an issue/operation.
        
        Args:
            issue_key: Jira issue key
            operation: Operation name
        
        Returns:
            Number of retriggers within the tracking window
        """
        key = self._get_key(issue_key, operation)
        current_time = datetime.now()
        
        # Clean up old attempts
        self._cleanup_old_attempts(key, current_time)
        
        return len(self._attempts.get(key, []))
    
    def reset_retriggers(
        self,
        issue_key: str,
        operation: Optional[str] = None,
    ) -> None:
        """
        Reset retrigger tracking for an issue.
        
        Args:
            issue_key: Jira issue key
            operation: Optional specific operation. If None, resets all operations.
        """
        if operation:
            key = self._get_key(issue_key, operation)
            if key in self._attempts:
                del self._attempts[key]
            if key in self._cooldown_until:
                del self._cooldown_until[key]
        else:
            # Reset all operations for this issue
            keys_to_remove = [
                key for key in self._attempts.keys()
                if key[0] == issue_key
            ]
            for key in keys_to_remove:
                del self._attempts[key]
                if key in self._cooldown_until:
                    del self._cooldown_until[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about retrigger tracking.
        
        Returns:
            Dictionary with tracking statistics
        """
        current_time = datetime.now()
        
        # Clean up all old attempts
        for key in list(self._attempts.keys()):
            self._cleanup_old_attempts(key, current_time)
        
        # Count active cooldowns
        active_cooldowns = sum(
            1 for cooldown_end in self._cooldown_until.values()
            if current_time < cooldown_end
        )
        
        return {
            "tracked_operations": len(self._attempts),
            "total_attempts": sum(len(attempts) for attempts in self._attempts.values()),
            "active_cooldowns": active_cooldowns,
            "max_retriggers": self.max_retriggers,
            "window_seconds": self.window_seconds,
            "cooldown_seconds": self.cooldown_seconds,
        }


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
    retry logic and error handling. It also reviews PRs with intelligent
    diff truncation that prioritizes new files.
    
    The agent now includes retrigger loop protection to prevent infinite
    cycles when operations are repeatedly attempted.
    """
    
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        diff_max_chars: int = DEFAULT_DIFF_MAX_CHARS,
        max_retriggers: int = DEFAULT_MAX_RETRIGGERS,
        retrigger_window: int = DEFAULT_RETRIGGER_WINDOW,
        enable_retrigger_protection: bool = True,
    ):
        """
        Initialize the Manager Agent.
        
        Args:
            max_retries: Maximum number of retry attempts per API call
            base_delay: Base delay in seconds before first retry
            diff_max_chars: Maximum characters for diff reviews
            max_retriggers: Maximum retriggers allowed within window
            retrigger_window: Time window in seconds to track retriggers
            enable_retrigger_protection: Whether to enable retrigger loop protection
        """
        self.client = JiraRetryClient(
            max_retries=max_retries,
            base_delay=base_delay,
        )
        self.diff_max_chars = diff_max_chars
        self.enable_retrigger_protection = enable_retrigger_protection
        
        # Initialize retrigger tracker
        self.retrigger_tracker = RetriggerTracker(
            max_retriggers=max_retriggers,
            window_seconds=retrigger_window,
        )
    
    def _check_retrigger_allowed(
        self,
        issue_key: str,
        operation: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a retrigger is allowed for an operation.
        
        Args:
            issue_key: Jira issue key
            operation: Operation name
        
        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        if not self.enable_retrigger_protection:
            return True, None
        
        return self.retrigger_tracker.can_retrigger(issue_key, operation)
    
    def _record_retrigger(
        self,
        issue_key: str,
        operation: str,
        status: str,
    ) -> int:
        """
        Record a retrigger attempt.
        
        Args:
            issue_key: Jira issue key
            operation: Operation name
            status: Operation status
        
        Returns:
            Current retrigger count
        """
        if not self.enable_retrigger_protection:
            return 0
        
        return self.retrigger_tracker.record_retrigger(issue_key, operation, status)
    
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
        operation = "start_work"
        
        # Check retrigger limit
        can_retrigger, reason = self._check_retrigger_allowed(issue_key, operation)
        if not can_retrigger:
            print(f"🛑 Retrigger blocked: {reason}")
            return TransitionResult(
                status=TransitionStatus.MAX_RETRIGGERS_EXCEEDED,
                issue_key=issue_key,
                error_message=reason,
                retrigger_count=self.retrigger_tracker.get_retrigger_count(
                    issue_key, operation
                ),
            )
        
        # Record this retrigger
        retrigger_count = self._record_retrigger(issue_key, operation, "attempting")
        
        fields = {}
        if assignee:
            fields["assignee"] = {"name": assignee}
        
        result = await self.client.transition_issue_by_name(
            issue_key=issue_key,
            target_status="In Progress",
            fields=fields if fields else None,
            comment=comment or "Work started by Manager Agent",
        )
        
        result.retrigger_count = retrigger_count
        return result
    
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
        operation = "complete_work"
        
        # Check retrigger limit
        can_retrigger, reason = self._check_retrigger_allowed(issue_key, operation)
        if not can_retrigger:
            print(f"🛑 Retrigger blocked: {reason}")
            return TransitionResult(
                status=TransitionStatus.MAX_RETRIGGERS_EXCEEDED,
                issue_key=issue_key,
                error_message=reason,
                retrigger_count=self.retrigger_tracker.get_retrigger_count(
                    issue_key, operation
                ),
            )
        
        # Record this retrigger
        retrigger_count = self._record_retrigger(issue_key, operation, "attempting")
        
        result = await self.client.transition_issue_by_name(
            issue_key=issue_key,
            target_status="Done",
            comment=comment or "Work completed by Manager Agent",
        )
        
        result.retrigger_count = retrigger_count
        return result
    
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
        operation = "move_to_code_review"
        
        # Check retrigger limit
        can_retrigger, reason = self._check_retrigger_allowed(issue_key, operation)
        if not can_retrigger:
            print(f"🛑 Retrigger blocked: {reason}")
            return TransitionResult(
                status=TransitionStatus.MAX_RETRIGGERS_EXCEEDED,
                issue_key=issue_key,
                error_message=reason,
                retrigger_count=self.retrigger_tracker.get_retrigger_count(
                    issue_key, operation
                ),
            )
        
        # Record this retrigger
        retrigger_count = self._record_retrigger(issue_key, operation, "attempting")
        
        result = await self.client.transition_issue_by_name(
            issue_key=issue_key,
            target_status="Code Review",
            comment=comment or "Ready for code review",
        )
        
        result.retrigger_count = retrigger_count
        return result
    
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
        operation = "move_to_testing"
        
        # Check retrigger limit
        can_retrigger, reason = self._check_retrigger_allowed(issue_key, operation)
        if not can_retrigger:
            print(f"🛑 Retrigger blocked: {reason}")
            return TransitionResult(
                status=TransitionStatus.MAX_RETRIGGERS_EXCEEDED,
                issue_key=issue_key,
                error_message=reason,
                retrigger_count=self.retrigger_tracker.get_retrigger_count(
                    issue_key, operation
                ),
            )
        
        # Record this retrigger
        retrigger_count = self._record_retrigger(issue_key, operation, "attempting")
        
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
        
        result.retrigger_count = retrigger_count
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
    
    def reset_retriggers(
        self,
        issue_key: str,
        operation: Optional[str] = None,
    ) -> None:
        """
        Reset retrigger tracking for an issue.
        
        This can be called manually to allow an issue to retry operations
        after fixing underlying problems.
        
        Args:
            issue_key: Jira issue key
            operation: Optional specific operation. If None, resets all operations.
        """
        self.retrigger_tracker.reset_retriggers(issue_key, operation)
        print(f"✓ Reset retrigger tracking for {issue_key}" +
              (f" operation '{operation}'" if operation else " (all operations)"))
    
    def get_retrigger_stats(self) -> Dict[str, Any]:
        """
        Get retrigger tracker statistics.
        
        Returns:
            Dictionary with retrigger tracking statistics
        """
        return self.retrigger_tracker.get_stats()
    
    def review_diff(
        self,
        diff_text: str,
        generate_comments: bool = True,
    ) -> DiffReviewResult:
        """
        Review a PR diff with intelligent truncation.
        
        This method truncates large diffs while prioritizing new files.
        Optionally generates review comments highlighting important aspects.
        
        Args:
            diff_text: Raw git diff output
            generate_comments: Whether to generate review comments
        
        Returns:
            DiffReviewResult with truncated diff and metadata
        """
        # Truncate diff with smart prioritization
        truncated_diff, metadata = truncate_diff_smart(
            diff_text,
            max_chars=self.diff_max_chars,
        )
        
        # Get summary of new files
        new_files_summary = get_new_files_summary(diff_text)
        
        # Generate review comments if requested
        review_comments = []
        if generate_comments:
            review_comments = self._generate_review_comments(
                metadata,
                new_files_summary,
            )
        
        return DiffReviewResult(
            truncated_diff=truncated_diff,
            metadata=metadata,
            new_files_summary=new_files_summary,
            review_comments=review_comments,
        )
    
    def _generate_review_comments(
        self,
        metadata: Dict[str, Any],
        new_files_summary: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Generate review comments based on diff analysis.
        
        Args:
            metadata: Diff truncation metadata
            new_files_summary: List of new file summaries
        
        Returns:
            List of review comment strings
        """
        comments = []
        
        # Comment on new files
        if new_files_summary:
            new_file_count = len(new_files_summary)
            comments.append(
                f"✨ This PR introduces {new_file_count} new file(s). "
                f"Please ensure all new files have appropriate tests and documentation."
            )
            
            # List new files
            new_file_list = "\n".join([
                f"  - {f['path']} (+{f['additions']} lines)"
                for f in new_files_summary[:5]  # Show first 5
            ])
            if new_file_count > 5:
                new_file_list += f"\n  ... and {new_file_count - 5} more"
            
            comments.append(f"New files:\n{new_file_list}")
        
        # Comment on truncation if it occurred
        if metadata.get("truncated"):
            files_full = metadata.get("files_included_full", 0)
            files_summarized = metadata.get("files_summarized", 0)
            
            comments.append(
                f"⚠️ Note: This PR is large. Showing {files_full} file(s) in full "
                f"and {files_summarized} file(s) as summaries. "
                f"New files are prioritized in the review."
            )
        
        # Comment on size
        total_files = metadata.get("total_files", 0)
        if total_files > 10:
            comments.append(
                f"📊 This is a large PR with {total_files} files changed. "
                f"Consider breaking it into smaller PRs for easier review."
            )
        
        return comments
    
    async def review_and_comment_pr(
        self,
        issue_key: str,
        diff_text: str,
    ) -> Tuple[DiffReviewResult, TransitionResult]:
        """
        Review a PR diff and post review comments to Jira.
        
        Args:
            issue_key: Jira issue key
            diff_text: Raw git diff output
        
        Returns:
            Tuple of (DiffReviewResult, TransitionResult)
        """
        # Review the diff
        review_result = self.review_diff(diff_text, generate_comments=True)
        
        # Format comments for Jira
        jira_comment = self._format_review_for_jira(review_result)
        
        # Post comment and transition to code review (with retrigger protection)
        transition_result = await self.move_to_code_review(
            issue_key=issue_key,
            comment=jira_comment,
        )
        
        return review_result, transition_result
    
    def _format_review_for_jira(self, review_result: DiffReviewResult) -> str:
        """
        Format review result for Jira comment.
        
        Args:
            review_result: DiffReviewResult object
        
        Returns:
            Formatted Jira comment string
        """
        lines = ["=== Code Review (Manager Agent) ===", ""]
        
        # Add review comments
        if review_result.review_comments:
            lines.extend(review_result.review_comments)
            lines.append("")
        
        # Add statistics
        metadata = review_result.metadata
        lines.append("📈 PR Statistics:")
        lines.append(f"  - Total files: {metadata.get('total_files', 0)}")
        lines.append(f"  - New files: {metadata.get('new_files_count', 0)}")
        
        if metadata.get("truncated"):
            lines.append(
                f"  - Diff size: {metadata.get('truncated_size', 0):,} chars "
                f"(truncated from {metadata.get('original_size', 0):,})"
            )
        
        return "\n".join(lines)


# ── Factory Function ──────────────────────────────────────────────────────────────────


def create_manager_agent(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    diff_max_chars: int = DEFAULT_DIFF_MAX_CHARS,
    max_retriggers: int = DEFAULT_MAX_RETRIGGERS,
    retrigger_window: int = DEFAULT_RETRIGGER_WINDOW,
    enable_retrigger_protection: bool = True,
) -> ManagerAgent:
    """
    Factory function to create a Manager Agent instance.
    
    Args:
        max_retries: Maximum number of retry attempts per API call
        base_delay: Base delay in seconds before first retry
        diff_max_chars: Maximum characters for diff reviews
        max_retriggers: Maximum retriggers allowed within window
        retrigger_window: Time window in seconds to track retriggers
        enable_retrigger_protection: Whether to enable retrigger loop protection
    
    Returns:
        ManagerAgent instance
    """
    return ManagerAgent(
        max_retries=max_retries,
        base_delay=base_delay,
        diff_max_chars=diff_max_chars,
        max_retriggers=max_retriggers,
        retrigger_window=retrigger_window,
        enable_retrigger_protection=enable_retrigger_protection,
    )
