import React, { useState, useRef, useEffect } from 'react';
import { Send, CheckCircle, XCircle, Clock, Sparkles } from 'lucide-react';
import './PMAgentChat.css';

const PMAgentChat = ({ projectId, onSprintCreated }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingApproval, setPendingApproval] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initial greeting
    setMessages([{
      id: 'init',
      role: 'assistant',
      content: 'Hi! I\'m your PM Agent. I can help you plan sprints by analyzing your backlog, estimating story points, and creating sprint plans. What would you like to work on?',
      timestamp: new Date()
    }]);
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/pm-agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          message: input,
          conversation_history: messages.slice(-10)
        })
      });

      const data = await response.json();

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        sprintPlan: data.sprint_plan
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (data.sprint_plan && data.requires_approval) {
        setPendingApproval(data.sprint_plan);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (approved) => {
    if (!pendingApproval) return;

    setLoading(true);
    try {
      const response = await fetch('/api/pm-agent/approve-sprint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          sprint_plan: pendingApproval,
          approved
        })
      });

      const data = await response.json();

      const resultMessage = {
        id: `result-${Date.now()}`,
        role: 'assistant',
        content: approved 
          ? `Great! Sprint "${pendingApproval.name}" has been created with ${pendingApproval.stories.length} stories.`
          : 'No problem. Let me know if you\'d like to adjust the sprint plan.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, resultMessage]);
      setPendingApproval(null);

      if (approved && onSprintCreated) {
        onSprintCreated(data.sprint);
      }
    } catch (error) {
      console.error('Approval error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="pm-agent-chat">
      <div className="chat-header">
        <Sparkles className="header-icon" />
        <h3>PM Agent</h3>
      </div>

      <div className="chat-messages">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content}
              {msg.sprintPlan && (
                <SprintPlanCard plan={msg.sprintPlan} />
              )}
            </div>
            <div className="message-timestamp">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {pendingApproval && (
        <div className="approval-panel">
          <Clock className="approval-icon" />
          <span>Sprint plan ready for approval</span>
          <div className="approval-actions">
            <button 
              onClick={() => handleApproval(true)}
              className="approve-btn"
              disabled={loading}
            >
              <CheckCircle size={16} /> Approve
            </button>
            <button 
              onClick={() => handleApproval(false)}
              className="reject-btn"
              disabled={loading}
            >
              <XCircle size={16} /> Reject
            </button>
          </div>
        </div>
      )}

      <div className="chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me to plan a sprint, estimate stories, or analyze your backlog..."
          disabled={loading}
          rows={2}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

const SprintPlanCard = ({ plan }) => (
  <div className="sprint-plan-card">
    <h4>{plan.name}</h4>
    <div className="plan-details">
      <span>Duration: {plan.duration} days</span>
      <span>Stories: {plan.stories.length}</span>
      <span>Total Points: {plan.total_points}</span>
    </div>
    <ul className="story-list">
      {plan.stories.map((story, idx) => (
        <li key={idx}>
          {story.title} <span className="story-points">({story.points}pt)</span>
        </li>
      ))}
    </ul>
  </div>
);

export default PMAgentChat;