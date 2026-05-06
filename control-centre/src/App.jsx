import React, { useState } from "react";
import DashboardMain from "./components/DashboardMain";
import SprintDashboard from "./components/SprintDashboard";
import GitHubWorkflowMonitor from "./components/GitHubWorkflowMonitor";
import UATDeployment from "./components/UATDeployment";
import SonarCloudTrigger from "./components/SonarCloudTrigger";
import PMAgentChat from "./components/PMAgentChat";
import OrchestratorStateView from "./components/OrchestratorStateView";

const TABS = [
  { id: "overview",      label: "Overview",      component: DashboardMain },
  { id: "sprint",        label: "Sprint Status", component: SprintDashboard },
  { id: "orchestrator",  label: "Orchestrator",  component: OrchestratorStateView },
  { id: "workflows",     label: "Workflows",     component: GitHubWorkflowMonitor },
  { id: "deploy",        label: "UAT Deploy",    component: UATDeployment },
  { id: "sonarcloud",    label: "SonarCloud",    component: SonarCloudTrigger },
  { id: "pm-agent",      label: "PM Agent",      component: PMAgentChat },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("sprint");
  const ActiveComponent = TABS.find(t => t.id === activeTab)?.component || SprintDashboard;

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
