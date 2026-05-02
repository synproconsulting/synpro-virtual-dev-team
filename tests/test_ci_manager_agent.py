"""
test_ci_manager_agent.py
─────────────────────────
Tests for Manager Agent retrigger loop prevention.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import ci_manager_agent as agent


class TestRetriggerLoopPrevention:
    """Test suite for retrigger cap and loop prevention."""
    
    def test_get_retrigger_count_no_prs(self):
        """Should return 0 when no PRs exist."""
        with patch('ci_manager_agent.requests.get') as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = []
            
            count = agent.get_retrigger_count("SDT1-60")
            assert count == 0
    
    def test_get_retrigger_count_with_retriggers(self):
        """Should count PRs with retrigger comments."""
        with patch('ci_manager_agent.requests.get') as mock_get:
            # First call: get PRs
            prs_response = Mock()
            prs_response.ok = True
            prs_response.json.return_value = [
                {
                    "head": {"ref": "feature/sdt1-60-test-1"},
                    "title": "[SDT1-60] Test",
                    "comments_url": "https://api.github.com/repos/test/test/issues/1/comments"
                },
                {
                    "head": {"ref": "feature/sdt1-60-test-2"},
                    "title": "[SDT1-60] Test",
                    "comments_url": "https://api.github.com/repos/test/test/issues/2/comments"
                }
            ]
            
            # Second call: comments for PR 1 (has retrigger)
            comments1_response = Mock()
            comments1_response.ok = True
            comments1_response.json.return_value = [
                {"body": "Merge conflict detected"},
                {"body": "Retriggering Auto Implement"}
            ]
            
            # Third call: comments for PR 2 (no retrigger)
            comments2_response = Mock()
            comments2_response.ok = True
            comments2_response.json.return_value = [
                {"body": "Looks good"}
            ]
            
            mock_get.side_effect = [prs_response, comments1_response, comments2_response]
            
            count = agent.get_retrigger_count("SDT1-60")
            assert count == 1
    
    def test_get_retrigger_count_handles_errors(self):
        """Should return 0 if API call fails."""
        with patch('ci_manager_agent.requests.get') as mock_get:
            mock_get.return_value.ok = False
            
            count = agent.get_retrigger_count("SDT1-60")
            assert count == 0
    
    def test_trigger_auto_implement_success(self):
        """Should trigger successfully when under cap."""
        with patch('ci_manager_agent.requests.get') as mock_get, \
             patch('ci_manager_agent.requests.post') as mock_post, \
             patch('ci_manager_agent.post_comment') as mock_comment:
            
            # Mock retrigger count = 0
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = []
            
            # Mock successful dispatch
            mock_post.return_value.status_code = 204
            
            result = agent.trigger_auto_implement(
                "SDT1-60",
                "Test summary",
                "Test feedback",
                pr_number=123
            )
            
            assert result is True
            mock_post.assert_called_once()
            # Should post a retrigger status comment
            assert mock_comment.call_count == 1
    
    def test_trigger_auto_implement_cap_reached(self):
        """Should block retrigger when cap is reached."""
        with patch('ci_manager_agent.requests.get') as mock_get, \
             patch('ci_manager_agent.requests.post') as mock_post, \
             patch('ci_manager_agent.post_comment') as mock_comment, \
             patch('ci_manager_agent.jira_comment') as mock_jira:
            
            # Mock retrigger count = MAX_RETRIGGER_ATTEMPTS
            prs_response = Mock()
            prs_response.ok = True
            prs_response.json.return_value = [
                {"head": {"ref": f"feature/sdt1-60-test-{i}"},
                 "title": "[SDT1-60] Test",
                 "comments_url": f"https://api.github.com/repos/test/test/issues/{i}/comments"}
                for i in range(3)
            ]
            
            comments_response = Mock()
            comments_response.ok = True
            comments_response.json.return_value = [
                {"body": "Merge conflict detected"}
            ]
            
            mock_get.side_effect = [prs_response] + [comments_response] * 3
            
            result = agent.trigger_auto_implement(
                "SDT1-60",
                "Test summary",
                "Test feedback",
                pr_number=123
            )
            
            assert result is False
            # Should NOT trigger workflow
            mock_post.assert_not_called()
            # Should post cap reached message
            assert mock_comment.call_count == 1
            assert "Retrigger cap reached" in mock_comment.call_args[0][1]
            # Should comment in Jira
            mock_jira.assert_called_once()
    
    def test_trigger_auto_implement_tracks_attempt_number(self):
        """Should track and display attempt number in comments."""
        with patch('ci_manager_agent.requests.get') as mock_get, \
             patch('ci_manager_agent.requests.post') as mock_post, \
             patch('ci_manager_agent.post_comment') as mock_comment:
            
            # Mock retrigger count = 1 (second attempt)
            prs_response = Mock()
            prs_response.ok = True
            prs_response.json.return_value = [
                {"head": {"ref": "feature/sdt1-60-test-1"},
                 "title": "[SDT1-60] Test",
                 "comments_url": "https://api.github.com/repos/test/test/issues/1/comments"}
            ]
            
            comments_response = Mock()
            comments_response.ok = True
            comments_response.json.return_value = [
                {"body": "retriggering Auto Implement"}
            ]
            
            mock_get.side_effect = [prs_response, comments_response]
            mock_post.return_value.status_code = 204
            
            result = agent.trigger_auto_implement(
                "SDT1-60",
                "Test summary",
                "Test feedback",
                pr_number=123
            )
            
            assert result is True
            # Check that attempt number is in the comment
            comment_text = mock_comment.call_args[0][1]
            assert "attempt 2/3" in comment_text
    
    def test_trigger_auto_implement_without_pr_number(self):
        """Should work without PR number (no comments posted)."""
        with patch('ci_manager_agent.requests.get') as mock_get, \
             patch('ci_manager_agent.requests.post') as mock_post, \
             patch('ci_manager_agent.post_comment') as mock_comment:
            
            # Mock retrigger count = 0
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = []
            
            # Mock successful dispatch
            mock_post.return_value.status_code = 204
            
            result = agent.trigger_auto_implement(
                "SDT1-60",
                "Test summary",
                "Test feedback",
                pr_number=None
            )
            
            assert result is True
            mock_post.assert_called_once()
            # Should not post comment when pr_number is None
            mock_comment.assert_not_called()
    
    def test_trigger_auto_implement_dispatch_failure(self):
        """Should handle workflow dispatch failures gracefully."""
        with patch('ci_manager_agent.requests.get') as mock_get, \
             patch('ci_manager_agent.requests.post') as mock_post, \
             patch('ci_manager_agent.post_comment') as mock_comment:
            
            # Mock retrigger count = 0
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = []
            
            # Mock failed dispatch
            mock_post.return_value.status_code = 403
            mock_post.return_value.text = "Forbidden"
            
            result = agent.trigger_auto_implement(
                "SDT1-60",
                "Test summary",
                "Test feedback",
                pr_number=123
            )
            
            assert result is False
            # Should post error message
            assert mock_comment.call_count == 1
            assert "retrigger failed" in mock_comment.call_args[0][1]


class TestConfigurationOptions:
    """Test configuration via environment variables."""
    
    def test_default_max_retrigger_attempts(self):
        """Should default to 3 attempts."""
        assert agent.MAX_RETRIGGER_ATTEMPTS >= 1
    
    @patch.dict('os.environ', {'MAX_RETRIGGER_ATTEMPTS': '5'})
    def test_custom_max_retrigger_attempts(self):
        """Should respect custom MAX_RETRIGGER_ATTEMPTS from env."""
        # Need to reimport to pick up env var
        import importlib
        importlib.reload(agent)
        assert agent.MAX_RETRIGGER_ATTEMPTS == 5


class TestMergeConflictHandling:
    """Test merge conflict detection and retrigger flow."""
    
    def test_review_pr_handles_immediate_conflict(self):
        """Should close and retrigger when PR has merge conflicts upfront."""
        with patch('ci_manager_agent.get_pr') as mock_get_pr, \
             patch('ci_manager_agent.post_comment') as mock_comment, \
             patch('ci_manager_agent.requests.patch') as mock_patch, \
             patch('ci_manager_agent.trigger_auto_implement') as mock_trigger, \
             patch('ci_manager_agent.jira_comment') as mock_jira:
            
            mock_get_pr.return_value = {
                "title": "[SDT1-60] Test PR",
                "head": {"ref": "feature/sdt1-60-test", "sha": "abc123"},
                "mergeable": False
            }
            
            agent.review_pr(123)
            
            # Should close PR
            mock_patch.assert_called_once()
            assert "closed" in str(mock_patch.call_args)
            
            # Should post comment
            assert mock_comment.call_count == 1
            assert "conflict" in mock_comment.call_args[0][1].lower()
            
            # Should trigger reimplement
            mock_trigger.assert_called_once()
            assert mock_trigger.call_args[0][0] == "SDT1-60"
    
    def test_review_pr_handles_conflict_during_merge(self):
        """Should handle conflicts detected during merge attempt."""
        with patch('ci_manager_agent.get_pr') as mock_get_pr, \
             patch('ci_manager_agent.get_ci_status') as mock_ci, \
             patch('ci_manager_agent.get_pr_diff') as mock_diff, \
             patch('ci_manager_agent.get_pr_files') as mock_files, \
             patch('ci_manager_agent.anthropic.Anthropic') as mock_anthropic, \
             patch('ci_manager_agent.merge_pr') as mock_merge, \
             patch('ci_manager_agent.post_comment') as mock_comment, \
             patch('ci_manager_agent.requests.patch') as mock_patch, \
             patch('ci_manager_agent.trigger_auto_implement') as mock_trigger, \
             patch('ci_manager_agent.jira_comment') as mock_jira:
            
            mock_get_pr.return_value = {
                "title": "[SDT1-60] Test PR",
                "head": {"ref": "feature/sdt1-60-test", "sha": "abc123"},
                "mergeable": True
            }
            
            mock_ci.return_value = [{
                "name": "Test",
                "status": "completed",
                "conclusion": "success"
            }]
            
            mock_diff.return_value = "diff content"
            mock_files.return_value = [{"filename": "test.py", "additions": 10, "deletions": 0}]
            
            # Mock Claude approval
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='{"decision":"APPROVE","summary":"Good","merge_message":"Test"}')]
            mock_client.messages.create.return_value = mock_response
            
            # Mock merge failure due to conflict
            mock_merge.return_value = (False, {"message": "merge conflict"})
            
            agent.review_pr(123)
            
            # Should attempt merge
            mock_merge.assert_called_once()
            
            # Should close and retrigger
            mock_patch.assert_called_once()
            mock_trigger.assert_called_once()


class TestJiraIntegration:
    """Test Jira updates when cap is reached."""
    
    def test_jira_notified_on_cap_reached(self):
        """Should post to Jira when retrigger cap is reached."""
        with patch('ci_manager_agent.requests.get') as mock_get, \
             patch('ci_manager_agent.post_comment') as mock_comment, \
             patch('ci_manager_agent.jira_comment') as mock_jira:
            
            # Mock retrigger count = MAX_RETRIGGER_ATTEMPTS
            prs_response = Mock()
            prs_response.ok = True
            prs_response.json.return_value = [
                {"head": {"ref": f"feature/sdt1-60-test-{i}"},
                 "title": "[SDT1-60] Test",
                 "comments_url": f"https://api.github.com/repos/test/test/issues/{i}/comments"}
                for i in range(3)
            ]
            
            comments_response = Mock()
            comments_response.ok = True
            comments_response.json.return_value = [
                {"body": "Merge conflict detected"}
            ]
            
            mock_get.side_effect = [prs_response] + [comments_response] * 3
            
            agent.trigger_auto_implement(
                "SDT1-60",
                "Test summary",
                "Test feedback",
                pr_number=123
            )
            
            # Should post to Jira
            mock_jira.assert_called_once()
            jira_text = mock_jira.call_args[0][1]
            assert "manual intervention" in jira_text.lower()
