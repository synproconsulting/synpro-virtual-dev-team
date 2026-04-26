import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { fetchSprintData } from '../api/sprintApi';
import JiraSprintView from './JiraSprintView';
import PullRequestView from './PullRequestView';
import CIPipelineView from './CIPipelineView';

const MetricCard = ({ title, value, sub }) => (
  <div style={{background:"var(--bg-card)",border:"1px solid var(--border)",borderRadius:10,padding:"1rem"}}>
    <div style={{fontSize:12,color:"var(--muted)",marginBottom:6}}>{title}</div>
    <div style={{fontSize:24,fontWeight:600}}>{value}</div>
    {sub && <div style={{fontSize:11,color:"var(--muted)",marginTop:4}}>{sub}</div>}
  </div>
);

const STATUS_ORDER = ["To Do", "In Progress", "In Review", "Done", "Blocked"];

const SprintDashboard = () => {
  const [sprintData, setSprintData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('jira');

  useEffect(() => {
    loadSprintData();
    const interval = setInterval(loadSprintData, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadSprintData = async () => {
    try {
      const data = await fetchSprintData();
      setSprintData(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load sprint data');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !sprintData) {
    return <div style={{padding:"2rem",color:"var(--muted)"}}>Loading sprint data...</div>;
  }

  if (error) {
    return <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>;
  }

  const issues    = sprintData?.jiraIssues || [];
  const prs       = sprintData?.prs || [];
  const runs      = sprintData?.runs || [];
  const metrics   = sprintData?.metrics || {};

  const doneCount   = issues.filter(i => i.status === "Done").length;
  const totalPoints = issues.reduce((s, i) => s + (i.points || 0), 0);
  const donePoints  = issues.filter(i => i.status === "Done").reduce((s, i) => s + (i.points || 0), 0);
  const successRuns = runs.filter(r => r.conclusion === "success").length;
  const ciRate      = runs.length ? Math.round((successRuns / runs.length) * 100) : 0;

  const TABS = [
    { id: "jira", label: `Jira Issues (${issues.length})` },
    { id: "prs",  label: `Pull Requests (${prs.length})` },
    { id: "ci",   label: `CI/CD (${runs.length})` },
  ];

  return (
    <div style={{display:"flex",flexDirection:"column",gap:"1.25rem"}}>
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:12}}>
        <MetricCard title="Sprint Velocity" value={doneCount} sub="tickets done" />
        <MetricCard title="Story Points" value={`${donePoints}/${totalPoints}`} sub="completed/total" />
        <MetricCard title="Pull Requests" value={`${prs.length} open`} sub={`${runs.filter(r=>r.conclusion==="success").length} CI passing`} />
        <MetricCard title="CI Success Rate" value={`${ciRate}%`} sub={`${runs.length} recent runs`} />
      </div>

      <div style={{display:"flex",gap:4,borderBottom:"1px solid var(--border)",paddingBottom:2}}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            background: activeTab === t.id ? "var(--accent)" : "transparent",
            color: activeTab === t.id ? "white" : "var(--muted)",
            border: "none", borderRadius:6, padding:"6px 14px",
            fontSize:13, cursor:"pointer", fontFamily:"inherit"
          }}>{t.label}</button>
        ))}
      </div>

      {activeTab === "jira" && <JiraSprintView issues={issues} />}
      {activeTab === "prs"  && <PullRequestView pullRequests={prs} />}
      {activeTab === "ci"   && <CIPipelineView pipelines={runs} />}
    </div>
  );
};

export default SprintDashboard;
