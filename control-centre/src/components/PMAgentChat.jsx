import React, { useState, useRef, useEffect } from 'react';
import { generateSprintPlan } from '../api/pmAgentApi';
import SprintPlanApproval from './SprintPlanApproval';
import { useProduct } from '../contexts/ProductContext';
import './PMAgentChat.css';

const API_URL = import.meta.env.VITE_API_URL || '';

const sendChatWithProduct = async (message, history, productId) => {
  if (!API_URL) throw new Error('VITE_API_URL not configured');
  const r = await fetch(`${API_URL}/api/pm-agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, product_id: productId || null }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || `PM Agent error: ${r.status}`);
  }
  const data = await r.json();
  return {
    message:    data.reply || data.message || '',
    sprintPlan: data.plan  || data.sprintPlan || null,
    role:       data.role  || 'assistant',
  };
};

const PMAgentChat = () => {
  const { productCredentials, loadingCredentials, credentialsError } = useProduct();
  const productId = productCredentials?.id || null;

  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'agent',
      content: 'Hi! I\'m your PM Agent. I can help you plan sprints based on your project goals and team capacity. What would you like to work on?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sprintPlan, setSprintPlan] = useState(null);
  const [showApproval, setShowApproval] = useState(false);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const history = messages.map(m => ({
        role: m.type === 'user' ? 'user' : 'assistant',
        content: m.content,
      }));
      const response = await sendChatWithProduct(input.trim(), history, productId);

      const agentMessage = {
        id: Date.now() + 1,
        type: 'agent',
        content: response.message,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, agentMessage]);

      if (response.sprintPlan) {
        setSprintPlan(response.sprintPlan);
        setShowApproval(true);
      }
    } catch (err) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'agent',
        content: `Sorry, I encountered an error: ${err.message}. Please try again.`,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleGeneratePlan = async () => {
    setLoading(true);
    try {
      const brief = messages
        .filter(m => m.type === 'user')
        .map(m => m.content)
        .join('\n');
      const history = messages.map(m => ({
        role: m.type === 'user' ? 'user' : 'assistant',
        content: m.content
      }));
      const plan = await generateSprintPlan(brief, history);
      setSprintPlan(plan);
      setShowApproval(true);

      const confirmMessage = {
        id: Date.now(),
        type: 'agent',
        content: 'I\'ve generated a sprint plan based on our conversation. Please review and approve it below.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, confirmMessage]);
    } catch (err) {
      const errorMessage = {
        id: Date.now(),
        type: 'agent',
        content: `Failed to generate sprint plan: ${err.message}`,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanApproved = () => {
    setShowApproval(false);
    const successMessage = {
      id: Date.now(),
      type: 'agent',
      content: 'Great! The sprint has been created and tickets have been generated in Jira. You can view them in the Sprint Dashboard.',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, successMessage]);
    setSprintPlan(null);
  };

  const handlePlanRejected = (feedback) => {
    setShowApproval(false);
    const feedbackMessage = {
      id: Date.now(),
      type: 'agent',
      content: `I understand. Let me revise the plan based on your feedback: "${feedback}". What specific changes would you like?`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, feedbackMessage]);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  if (loadingCredentials) {
    return <div className="pm-agent-chat"><div style={{padding:'2rem',textAlign:'center'}}>Loading product credentials…</div></div>;
  }
  if (credentialsError) {
    return <div className="pm-agent-chat"><div style={{padding:'2rem',textAlign:'center'}}>Error loading credentials: {credentialsError}</div></div>;
  }
  if (!productCredentials) {
    return <div className="pm-agent-chat"><div style={{padding:'2rem',textAlign:'center'}}>Select a product to use PM Agent</div></div>;
  }

  return (
    <div className="pm-agent-chat">
      <div className="chat-header">
        <div className="agent-info">
          <div className="agent-avatar">🤖</div>
          <div>
            <h3>PM Agent</h3>
            <span className="status">Online</span>
          </div>
        </div>
        <button
          className="generate-plan-btn"
          onClick={handleGeneratePlan}
          disabled={loading || messages.length < 3}
        >
          📋 Generate Sprint Plan
        </button>
      </div>

      <div className="chat-messages" ref={chatContainerRef}>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.type} ${message.isError ? 'error' : ''}`}
          >
            <div className="message-content">
              {message.content}
            </div>
            <div className="message-time">
              {formatTime(message.timestamp)}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message agent loading">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {showApproval && sprintPlan && (
        <SprintPlanApproval
          plan={sprintPlan}
          onApprove={handlePlanApproved}
          onReject={handlePlanRejected}
        />
      )}

      <div className="chat-input-container">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Describe your sprint goals, team capacity, or ask questions..."
          rows="2"
          disabled={loading}
        />
        <button
          className="send-button"
          onClick={handleSendMessage}
          disabled={!input.trim() || loading}
        >
          ➤
        </button>
      </div>
    </div>
  );
};

export default PMAgentChat;
