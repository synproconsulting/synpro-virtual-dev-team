import React, { useState, useEffect } from "react";
import DashboardMain from "./components/DashboardMain";
import SprintDashboard from "./components/SprintDashboard";
import GitHubWorkflowMonitor from "./components/GitHubWorkflowMonitor";
import UATDeployment from "./components/UATDeployment";
import SonarCloudTrigger from "./components/SonarCloudTrigger";
import PMAgentChat from "./components/PMAgentChat";

const TABS = [
  { id: "overview",   label: "Overview",      component: DashboardMain },
  { id: "sprint",     label: "Sprint Status", component: SprintDashboard },
  { id: "workflows",  label: "Workflows",     component: GitHubWorkflowMonitor },
  { id: "deploy",     label: "UAT Deploy",    component: UATDeployment },
  { id: "sonarcloud", label: "SonarCloud",    component: SonarCloudTrigger },
  { id: "pm-agent",   label: "PM Agent",      component: PMAgentChat },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  
  // Listen for navigation events from child components
  useEffect(() => {
    const handleNavigate = (event) => {
      if (event.detail && typeof event.detail === 'string') {
        setActiveTab(event.detail);
      }
    };
    
    window.addEventListener('cc-navigate', handleNavigate);
    return () => window.removeEventListener('cc-navigate', handleNavigate);
  }, []);
  
  const ActiveComponent = TABS.find(t => t.id === activeTab)?.component || DashboardMain;

  return (
    <div className="cc-app">
      <header className="cc-header">
        <div className="cc-header-inner">
          <div className="cc-logo">
            <span className="cc-logo-icon">⚡</span>
            <span className="cc-logo-text">SynPro Control Centre</span>
          </div>
          <nav className="cc-nav">
            {TABS.map(tab => (
              <button
                key={tab.id}
                className={`cc-nav-btn ${activeTab === tab.id ? "active" : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>
      <main className="cc-main">
        <ActiveComponent />
      </main>
    </div>
  );
}
