import React from 'react';
import SprintTrigger from './SprintTrigger';
import AutoReviewPanel from './AutoReviewPanel';
import './Dashboard.css';

const Dashboard = () => {
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Control Centre Dashboard</h1>
        <p className="subtitle">Manage sprints and automated PR reviews</p>
      </header>

      <main className="dashboard-content">
        <section className="dashboard-section">
          <SprintTrigger />
        </section>

        <section className="dashboard-section">
          <AutoReviewPanel />
        </section>
      </main>
    </div>
  );
};

export default Dashboard;
