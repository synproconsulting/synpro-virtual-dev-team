import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const notificationApi = axios.create({
  baseURL: `${API_BASE_URL}/api/notifications`,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Get all notifications with optional filters
 * @param {Object} params - Query parameters (limit, offset, type, status)
 * @returns {Promise<Array>} List of notifications
 */
export const getNotifications = async (params = {}) => {
  try {
    const response = await notificationApi.get('/', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching notifications:', error);
    throw error;
  }
};

/**
 * Get a single notification by ID
 * @param {string} id - Notification ID
 * @returns {Promise<Object>} Notification details
 */
export const getNotification = async (id) => {
  try {
    const response = await notificationApi.get(`/${id}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching notification:', error);
    throw error;
  }
};

/**
 * Mark a notification as read
 * @param {string} id - Notification ID
 * @returns {Promise<Object>} Updated notification
 */
export const markAsRead = async (id) => {
  try {
    const response = await notificationApi.patch(`/${id}/read`);
    return response.data;
  } catch (error) {
    console.error('Error marking notification as read:', error);
    throw error;
  }
};

/**
 * Mark all notifications as read
 * @returns {Promise<Object>} Result
 */
export const markAllAsRead = async () => {
  try {
    const response = await notificationApi.post('/mark-all-read');
    return response.data;
  } catch (error) {
    console.error('Error marking all notifications as read:', error);
    throw error;
  }
};

/**
 * Delete a notification
 * @param {string} id - Notification ID
 * @returns {Promise<void>}
 */
export const deleteNotification = async (id) => {
  try {
    await notificationApi.delete(`/${id}`);
  } catch (error) {
    console.error('Error deleting notification:', error);
    throw error;
  }
};

/**
 * Clear all notifications
 * @returns {Promise<void>}
 */
export const clearNotifications = async () => {
  try {
    await notificationApi.delete('/clear');
  } catch (error) {
    console.error('Error clearing notifications:', error);
    throw error;
  }
};

/**
 * Get unread notification count
 * @returns {Promise<number>} Unread count
 */
export const getUnreadCount = async () => {
  try {
    const response = await notificationApi.get('/unread/count');
    return response.data.count;
  } catch (error) {
    console.error('Error fetching unread count:', error);
    throw error;
  }
};

export default notificationApi;