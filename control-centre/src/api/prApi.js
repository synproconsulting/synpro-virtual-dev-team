const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const GITHUB_TOKEN = process.env.REACT_APP_GITHUB_TOKEN;

export const fetchOpenPRs = async () => {
  const response = await fetch(`${API_BASE_URL}/api/prs/open`, {
    headers: {
      'Authorization': `Bearer ${process.env.REACT_APP_API_TOKEN || ''}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to fetch open PRs');
  }

  return response.json();
};

export const triggerAutoReview = async (prNumber, repository) => {
  const response = await fetch(`${API_BASE_URL}/api/prs/auto-review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.REACT_APP_API_TOKEN || ''}`,
    },
    body: JSON.stringify({
      prNumber,
      repository,
      githubToken: GITHUB_TOKEN,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to trigger auto-review');
  }

  return response.json();
};

export const getReviewStatus = async (prNumber, repository) => {
  const response = await fetch(
    `${API_BASE_URL}/api/prs/review-status?prNumber=${prNumber}&repository=${repository}`,
    {
      headers: {
        'Authorization': `Bearer ${process.env.REACT_APP_API_TOKEN || ''}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to fetch review status');
  }

  return response.json();
};

export const getPRDetails = async (prNumber, repository) => {
  const response = await fetch(
    `${API_BASE_URL}/api/prs/details?prNumber=${prNumber}&repository=${repository}`,
    {
      headers: {
        'Authorization': `Bearer ${process.env.REACT_APP_API_TOKEN || ''}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to fetch PR details');
  }

  return response.json();
};
