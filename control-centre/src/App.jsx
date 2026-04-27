import React, { useState } from "react";
import DashboardMain from "./components/DashboardMain";
import SprintDashboard from "./components/SprintDashboard";
import GitHubWorkflowMonitor from "./components/GitHubWorkflowMonitor";
import SprintTrigger from "./components/SprintTrigger";
import UATDeployment from "./components/UATDeployment";
import SonarCloudTrigger from "./components/SonarCloudTrigger";
import PMAgentChat from "./components/PMAgentChat";
import ProfilePage from "./components/ProfilePage";

const TABS = [
  { id: "overview",   label: "Overview",       component: DashboardMain },
  { id: "sprint",     label: "Sprint Status",  component: SprintDashboard },
  { id: "workflows",  label: "Workflows",      component: GitHubWorkflowMonitor },
  { id: "trigger",    label: "Sprint Trigger", component: SprintTrigger },
  { id: "deploy",     label: "UAT Deploy",     component: UATDeployment },
  { id: "sonarcloud", label: "SonarCloud",     component: SonarCloudTrigger },
  { id: "pm-agent",   label: "PM Agent",       component: PMAgentChat },
  { id: "profile",    label: "Profile",        component: ProfilePage },
];

function App() {
  const [activeTab, setActiveTab] = useState("overview");

  const ActiveComponent = TABS.find(tab => tab.id === activeTab)?.component || DashboardMain;

  return (
    <div className="app">
      <nav className="nav-tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
      <main className="main-content">
        <ActiveComponent />
      </main>
    </div>
  );
}

export default App;