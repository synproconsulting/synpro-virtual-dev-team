from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import os
import requests
from functools import lru_cache

sprint_status_bp = Blueprint('sprint_status', __name__)

# Configuration from environment variables
JIRA_BASE_URL = os.getenv('JIRA_BASE_URL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_ORG = os.getenv('GITHUB_ORG')
CI_API_URL = os.getenv('CI_API_URL')
CI_API_TOKEN = os.getenv('CI_API_TOKEN')


class JiraClient:
    def __init__(self):
        self.base_url = JIRA_BASE_URL
        self.auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    def get_sprint_issues(self, sprint_id):
        endpoint = f'{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue'
        params = {'fields': 'summary,status,priority,assignee,customfield_10016'}
        response = requests.get(endpoint, auth=self.auth, params=params)
        response.raise_for_status()
        return response.json()

    def get_sprint_details(self, sprint_id):
        endpoint = f'{self.base_url}/rest/agile/1.0/sprint/{sprint_id}'
        response = requests.get(endpoint, auth=self.auth)
        response.raise_for_status()
        return response.json()


class GitHubClient:
    def __init__(self):
        self.token = GITHUB_TOKEN
        self.org = GITHUB_ORG
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def get_pull_requests(self, repo, sprint_start, sprint_end):
        endpoint = f'https://api.github.com/repos/{self.org}/{repo}/pulls'
        params = {'state': 'all', 'per_page': 100}
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_pr_reviews(self, repo, pr_number):
        endpoint = f'https://api.github.com/repos/{self.org}/{repo}/pulls/{pr_number}/reviews'
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()


class CIClient:
    def __init__(self):
        self.base_url = CI_API_URL
        self.headers = {'Authorization': f'Bearer {CI_API_TOKEN}'}

    def get_pipelines(self, branch=None):
        endpoint = f'{self.base_url}/pipelines'
        params = {'branch': branch} if branch else {}
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()


@sprint_status_bp.route('/api/sprint-status/<sprint_id>', methods=['GET'])
def get_sprint_status(sprint_id):
    try:
        jira_client = JiraClient()
        github_client = GitHubClient()
        ci_client = CIClient()

        # Fetch Jira data
        sprint_details = jira_client.get_sprint_details(sprint_id)
        sprint_issues = jira_client.get_sprint_issues(sprint_id)

        # Process Jira tickets
        jira_tickets = process_jira_tickets(sprint_issues)
        overview = calculate_sprint_overview(sprint_details, jira_tickets)

        # Fetch GitHub PRs
        repo = request.args.get('repo', 'main-repo')
        pull_requests = github_client.get_pull_requests(
            repo,
            sprint_details.get('startDate'),
            sprint_details.get('endDate')
        )
        processed_prs = process_pull_requests(pull_requests, github_client, repo)

        # Fetch CI pipelines
        pipelines = ci_client.get_pipelines()
        processed_pipelines = process_pipelines(pipelines)

        return jsonify({
            'overview': overview,
            'jiraTickets': jira_tickets,
            'pullRequests': processed_prs,
            'pipelines': processed_pipelines
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def process_jira_tickets(issues_data):
    tickets = []
    for issue in issues_data.get('issues', []):
        fields = issue['fields']
        tickets.append({
            'ticketId': issue['key'],
            'summary': fields['summary'],
            'status': fields['status']['name'],
            'priority': fields.get('priority', {}).get('name', 'None'),
            'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned'),
            'storyPoints': fields.get('customfield_10016', 0),
            'url': f"{JIRA_BASE_URL}/browse/{issue['key']}"
        })
    return tickets


def calculate_sprint_overview(sprint_details, tickets):
    total_tickets = len(tickets)
    completed = sum(1 for t in tickets if t['status'] == 'Done')
    in_progress = sum(1 for t in tickets if t['status'] == 'In Progress')
    blocked = sum(1 for t in tickets if t['status'] == 'Blocked')
    velocity = sum(t.get('storyPoints', 0) for t in tickets if t['status'] == 'Done')

    start_date = datetime.fromisoformat(sprint_details['startDate'].replace('Z', '+00:00'))
    end_date = datetime.fromisoformat(sprint_details['endDate'].replace('Z', '+00:00'))
    days_remaining = max(0, (end_date - datetime.now()).days)

    completion_percentage = int((completed / total_tickets * 100) if total_tickets > 0 else 0)

    return {
        'sprintName': sprint_details['name'],
        'startDate': sprint_details['startDate'],
        'endDate': sprint_details['endDate'],
        'totalTickets': total_tickets,
        'completedTickets': completed,
        'inProgressTickets': in_progress,
        'blockedTickets': blocked,
        'velocityPoints': velocity,
        'completionPercentage': completion_percentage,
        'daysRemaining': days_remaining
    }


def process_pull_requests(prs, github_client, repo):
    processed = []
    for pr in prs[:20]:  # Limit to recent 20 PRs
        reviews = github_client.get_pr_reviews(repo, pr['number'])
        approved = sum(1 for r in reviews if r['state'] == 'APPROVED')
        changes_requested = sum(1 for r in reviews if r['state'] == 'CHANGES_REQUESTED')

        processed.append({
            'prNumber': pr['number'],
            'title': pr['title'],
            'author': {
                'name': pr['user']['login'],
                'avatar': pr['user']['avatar_url']
            },
            'status': 'approved' if approved > 0 else 'pending',
            'reviews': {
                'approved': approved,
                'changesRequested': changes_requested
            },
            'commentCount': pr.get('comments', 0),
            'branch': pr['head']['ref'],
            'url': pr['html_url']
        })
    return processed


def process_pipelines(pipelines_data):
    processed = []
    for pipeline in pipelines_data.get('pipelines', [])[:15]:
        processed.append({
            'id': pipeline['id'],
            'name': pipeline['name'],
            'status': pipeline['status'],
            'branch': pipeline.get('branch', 'main'),
            'commit': {
                'sha': pipeline['commit']['sha'],
                'message': pipeline['commit']['message']
            },
            'duration': pipeline.get('duration'),
            'progress': pipeline.get('progress', 0),
            'startedAt': pipeline['started_at'],
            'url': pipeline['url'],
            'stages': pipeline.get('stages', [])
        })
    return processed
