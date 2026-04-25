import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.sprint_status import (
    process_jira_tickets,
    calculate_sprint_overview,
    process_pull_requests,
    process_pipelines
)


class TestSprintStatus(unittest.TestCase):

    def test_process_jira_tickets(self):
        mock_data = {
            'issues': [
                {
                    'key': 'SDT1-31',
                    'fields': {
                        'summary': 'Test ticket',
                        'status': {'name': 'Done'},
                        'priority': {'name': 'High'},
                        'assignee': {'displayName': 'John Doe'},
                        'customfield_10016': 5
                    }
                }
            ]
        }

        result = process_jira_tickets(mock_data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['ticketId'], 'SDT1-31')
        self.assertEqual(result[0]['status'], 'Done')
        self.assertEqual(result[0]['storyPoints'], 5)

    def test_calculate_sprint_overview(self):
        sprint_details = {
            'name': 'Sprint 1',
            'startDate': '2024-01-01T00:00:00.000Z',
            'endDate': '2024-01-15T00:00:00.000Z'
        }

        tickets = [
            {'status': 'Done', 'storyPoints': 5},
            {'status': 'In Progress', 'storyPoints': 3},
            {'status': 'To Do', 'storyPoints': 2}
        ]

        result = calculate_sprint_overview(sprint_details, tickets)
        self.assertEqual(result['totalTickets'], 3)
        self.assertEqual(result['completedTickets'], 1)
        self.assertEqual(result['inProgressTickets'], 1)
        self.assertEqual(result['velocityPoints'], 5)

    def test_process_pull_requests(self):
        mock_prs = [
            {
                'number': 123,
                'title': 'Test PR',
                'user': {'login': 'testuser', 'avatar_url': 'http://avatar.url'},
                'comments': 5,
                'head': {'ref': 'feature-branch'},
                'html_url': 'http://github.com/pr/123'
            }
        ]

        mock_client = MagicMock()
        mock_client.get_pr_reviews.return_value = [
            {'state': 'APPROVED'},
            {'state': 'APPROVED'}
        ]

        result = process_pull_requests(mock_prs, mock_client, 'test-repo')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['prNumber'], 123)
        self.assertEqual(result[0]['reviews']['approved'], 2)

    def test_process_pipelines(self):
        mock_data = {
            'pipelines': [
                {
                    'id': 'pipe-1',
                    'name': 'CI Pipeline',
                    'status': 'success',
                    'branch': 'main',
                    'commit': {
                        'sha': 'abc123def456',
                        'message': 'Test commit'
                    },
                    'duration': 120,
                    'started_at': '2024-01-10T10:00:00Z',
                    'url': 'http://ci.example.com/pipe-1',
                    'stages': []
                }
            ]
        }

        result = process_pipelines(mock_data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'CI Pipeline')
        self.assertEqual(result[0]['status'], 'success')


if __name__ == '__main__':
    unittest.main()
