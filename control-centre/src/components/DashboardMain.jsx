import React, { useState } from 'react';
import SprintTrigger from './SprintTrigger';
import AutoReviewPR from './AutoReviewPR';
import './DashboardMain.css';

const DashboardMain = () => {
  const [activeTab, setActiveTab] = useState('sprint');

  return (
    <div className="dashboard-main">
      <div className="dashboard-header">
        <h1>Control Centre Dashboard</h1>
        <p className="subtitle">Sprint Management & PR Auto-Review</p>
      </div>

      <div className="dashboard-tabs">
        <button
          className={`tab-button ${activeTab === 'sprint' ? 'active' : ''}`}
          onClick={() => setActiveTab('sprint')}
        >
          Sprint Trigger
        </button>
        <button
          className={`tab-button ${activeTab === 'pr' ? 'active' : ''}`}
          onClick={() => setActiveTab('pr')}
        >
          Auto Review PRs
        </button>
      </div>

      <div className="dashboard-content">
        {activeTab === 'sprint' && <SprintTrigger />}
        {activeTab === 'pr' && <AutoReviewPR />}
      </div>
    </div>
  );
};

export default DashboardMain;
