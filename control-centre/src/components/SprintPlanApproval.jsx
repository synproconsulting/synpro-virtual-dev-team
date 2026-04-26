import React, { useState } from 'react';
import { approveSprint, rejectSprint } from '../api/pmAgentApi';
import './SprintPlanApproval.css';

const SprintPlanApproval = ({ plan, onApprove, onReject }) => {
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedTicket, setExpandedTicket] = useState(null);

  const handleApprove = async () => {
    setLoading(true);
    try {
      await approveSprint(plan.id);
      onApprove();
    } catch (err) {
      alert(`Failed to approve sprint: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!feedback.trim()) {
      alert('Please provide feedback for rejection');
      return;
    }
    
    setLoading(true);
    try {
      await rejectSprint(plan.id, feedback);
      onReject(feedback);
      setShowRejectModal(false);
      setFeedback('');
    } catch (err) {
      alert(`Failed to reject sprint: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleTicket = (ticketId) => {
    setExpandedTicket(expandedTicket === ticketId ? null : ticketId);
  };

  const getPriorityClass = (priority) => {
    return `priority-${priority.toLowerCase()}`;
  };

  const getStoryPoints = () => {
    return plan.tickets.reduce((sum, ticket) => sum + (ticket.storyPoints || 0), 0);
  };

  return (
    <div className="sprint-plan-approval">
      <div className="approval-overlay" onClick={() => !loading && setShowRejectModal(false)} />
      
      <div className="approval-panel">
        <div className="approval-header">
          <h3>🎯 Sprint Plan Review</h3>
          <p className="plan-summary">
            {plan.sprintNumber} • {plan.tickets.length} tickets • {getStoryPoints()} story points
          </p>
        </div>

        <div className="plan-details">
          <div className="detail-row">
            <span className="label">Sprint Duration:</span>
            <span className="value">{plan.startDate} → {plan.endDate}</span>
          </div>
          <div className="detail-row">
            <span className="label">Sprint Goal:</span>
            <span className="value">{plan.goal}</span>
          </div>
          <div className="detail-row">
            <span className="label">Team Capacity:</span>
            <span className="value">{plan.teamCapacity} points</span>
          </div>
        </div>

        <div className="tickets-section">
          <h4>Planned Tickets</h4>
          <div className="tickets-list">
            {plan.tickets.map((ticket) => (
              <div key={ticket.id} className="ticket-item">
                <div 
                  className="ticket-summary"
                  onClick={() => toggleTicket(ticket.id)}
                >
                  <div className="ticket-header">
                    <span className={`priority-badge ${getPriorityClass(ticket.priority)}`}>
                      {ticket.priority}
                    </span>
                    <span className="ticket-title">{ticket.title}</span>
                    <span className="story-points">{ticket.storyPoints} pts</span>
                  </div>
                  <span className="expand-icon">
                    {expandedTicket === ticket.id ? '▼' : '▶'}
                  </span>
                </div>
                
                {expandedTicket === ticket.id && (
                  <div className="ticket-details">
                    <p className="ticket-description">{ticket.description}</p>
                    {ticket.acceptanceCriteria && (
                      <div className="acceptance-criteria">
                        <strong>Acceptance Criteria:</strong>
                        <ul>
                          {ticket.acceptanceCriteria.map((criteria, idx) => (
                            <li key={idx}>{criteria}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <div className="ticket-meta">
                      <span>Type: {ticket.type}</span>
                      <span>Assignee: {ticket.assignee || 'Unassigned'}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="approval-actions">
          <button 
            className="reject-btn"
            onClick={() => setShowRejectModal(true)}
            disabled={loading}
          >
            ✕ Request Changes
          </button>
          <button 
            className="approve-btn"
            onClick={handleApprove}
            disabled={loading}
          >
            {loading ? 'Processing...' : '✓ Approve & Create Sprint'}
          </button>
        </div>
      </div>

      {showRejectModal && (
        <div className="reject-modal">
          <div className="modal-content">
            <h4>Request Changes</h4>
            <p>Please provide feedback on what needs to be changed:</p>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="E.g., 'Reduce story points', 'Add more frontend tasks', 'Change priorities'..."
              rows="4"
              disabled={loading}
            />
            <div className="modal-actions">
              <button 
                onClick={() => setShowRejectModal(false)}
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                className="submit-feedback-btn"
                onClick={handleReject}
                disabled={loading || !feedback.trim()}
              >
                Submit Feedback
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SprintPlanApproval;