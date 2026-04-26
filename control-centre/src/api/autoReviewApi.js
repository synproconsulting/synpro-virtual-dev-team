const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

export const enableAutoReview = async (reviewData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auto-review/enable`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify(reviewData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to enable auto-review');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

export const disableAutoReview = async (prId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auto-review/${prId}/disable`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to disable auto-review');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

export const getAutoReviewStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/auto-review/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch auto-review status');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

export const getReviewHistory = async (prId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auto-review/${prId}/history`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch review history');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};
