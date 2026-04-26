import React, { useState, useEffect } from 'react';
import { fetchSprints, fetchSprintIssues, fetchSprintData } from '../api/sprintApi';
import JiraSprintView from './JiraSprintView';
import PullRequestView from './PullRequestView';
import CIPipelineView from './CIPipelineView';

const MetricCard = ({ title, value, sub, color }) => (
  <div style={{
    background:"var(--bg-card)", border:"1px solid var(--border)",
    borderRadius:10, padding:"1rem",
    borderLeft: color ? `3px solid ${color}` : undefined,
  }}>
    <div style={{fontSize:12,color:"var(--muted)",marginBottom:6}}>{title}</div>
    <div style={{fontSize:22,fontWeight:600}}>{value}</div>
    {sub && <div style={{fontSize:11,color:"var(--muted)",marginTop:4}}>{sub}</div>}
  </div>
);

const SprintDashboard = () => {
  const [sprints, setSprints]         = useState([]);
  const [selectedSprint, setSelected] = useState(null);
  const [issues, setIssues]           = useState([]);
  const [globalData, setGlobalData]   = useState(null);
  const [loading, setLoading]         = useState(true);
  const [activeTab, setActiveTab]     = useState("jira");

  useEffect(() => {
    const init = async () => {
      const [sprintList, global] = await Promise.all([
        fetchSprints(),
        fetchSprintData(),
      ]);
      setSprints(sprintList);
      setGlobalData(global);
      if (sprintList.length > 0) {
        const latest = sprintList[sprintList.length - 1];
        setSelected(latest);
        const sprintIssues = await fetchSprintIssues(latest.id);
        setIssues(sprintIssues);
      }
      setLoading(false);
    };
    init();
  }, []);

  const onSprintChange = async (sprint) => {
    setSelected(sprint);
    setLoading(true);
    const sprintIssues = await fetchSprintIssues(sprint.id);
    setIssues(sprintIssues);
    setLoading(false);
  };

  const prs  = globalData?.prs  || [];
  const runs = globalData?.runs || [];

  // Sprint metrics
  const doneIssues   = issues.filter(i => i.status === "Done");
  const todoIssues   = issues.filter(i => i.status === "To Do");
  const inProgress   = issues.filter(i => i.status === "In Progress");
  const totalPoints  = issues.reduce((s, i) => s + (i.points || 0), 0);
  const donePoints   = doneIssues.reduce((s, i) => s + (i.points || 0), 0);
  const completion   = issues.length ? Math.round((doneIssues.length / issues.length) * 100) : 0;
  const successRuns  = runs.filter(r => r.conclusion === "success").length;
  const ciRate       = runs.length ? Math.round((successRuns / runs.length) * 100) : 0;

  const TABS = [
    { id:"jira", label:`Issues (${issues.length})` },
    { id:"prs",  label:`PRs (${prs.length})` },
    { id:"ci",   label:`CI/CD (${runs.length})` },
  ];

  return (
    <div style={{display:"flex",flexDirection:"column",gap:"1.25rem"}}>

      {/* Sprint Selector */}
      <div style={{
        background:"var(--bg-card)", border:"1px solid var(--border)",
        borderRadius:10, padding:"1rem",
        display:"flex", alignItems:"center", gap:12, flexWrap:"wrap"
      }}>
        <span style={{fontSize:13, color:"var(--muted)", flexShrink:0}}>Sprint:</span>
        <div style={{display:"flex", gap:6, flexWrap:"wrap", flex:1}}>
          {sprints.map(sprint => (
            <button key={sprint.id} onClick={() => onSprintChange(sprint)} style={{
              background: selectedSprint?.id === sprint.id ? "var(--accent)" : "var(--bg)",
              color: selectedSprint?.id === sprint.id ? "white" : "var(--muted)",
              border: `1px solid ${selectedSprint?.id === sprint.id ? "var(--accent)" : "var(--border)"}`,
              borderRadius:20, padding:"4px 14px", fontSize:12,
              cursor:"pointer", fontFamily:"inherit", fontWeight:500,
            }}>{sprint.name}</button>
          ))}
        </div>
        {selectedSprint && (
          <span style={{fontSize:11, color:"var(--muted)"}}>
            {issues.length} issues
          </span>
        )}
      </div>

      {/* Metrics */}
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10}}>
        <MetricCard
          title="Completion"
          value={`${completion}%`}
          sub={`${doneIssues.length}/${issues.length} issues done`}
          color={completion === 100 ? "#4ade80" : completion > 50 ? "#60a5fa" : "#fbbf24"}
        />
        <MetricCard
          title="Story Points"
          value={`${donePoints}/${totalPoints}`}
          sub={`${totalPoints - donePoints} remaining`}
          color="#a855f7"
        />
        <MetricCard
          title="In Progress"
          value={inProgress.length}
          sub={`${todoIssues.length} to do`}
          color="#60a5fa"
        />
        <MetricCard
          title="CI Success Rate"
          value={`${ciRate}%`}
          sub={`${runs.length} recent runs`}
          color={ciRate >= 80 ? "#4ade80" : "#f87171"}
        />
      </div>

      {/* Progress Bar */}
      {issues.length > 0 && (
        <div style={{background:"var(--bg-card)",border:"1px solid var(--border)",borderRadius:10,padding:"1rem"}}>
          <div style={{display:"flex",justifyContent:"space-between",fontSize:12,color:"var(--muted)",marginBottom:8}}>
            <span>Sprint Progress</span>
            <span>{completion}% complete</span>
          </div>
          <div style={{height:8,background:"var(--bg)",borderRadius:4,overflow:"hidden"}}>
            <div style={{
              height:"100%",
              width:`${completion}%`,
              background: completion === 100 ? "#4ade80" : "var(--accent)",
              borderRadius:4, transition:"width 0.3s ease"
            }}/>
          </div>
          <div style={{display:"flex",gap:16,marginTop:8,fontSize:11,color:"var(--muted)"}}>
            <span style={{color:"#4ade80"}}>✓ Done: {doneIssues.length}</span>
            <span style={{color:"#60a5fa"}}>↻ In Progress: {inProgress.length}</span>
            <span style={{color:"#94a3b8"}}>○ To Do: {todoIssues.length}</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{display:"flex",gap:4,borderBottom:"1px solid var(--border)",paddingBottom:2}}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            background: activeTab === t.id ? "var(--accent)" : "transparent",
            color: activeTab === t.id ? "white" : "var(--muted)",
            border:"none", borderRadius:6, padding:"6px 14px",
            fontSize:13, cursor:"pointer", fontFamily:"inherit"
          }}>{t.label}</button>
        ))}
      </div>

      {loading ? (
        <div style={{textAlign:"center",color:"var(--muted)",padding:"2rem"}}>Loading...</div>
      ) : (
        <>
          {activeTab === "jira" && <JiraSprintView issues={issues} />}
          {activeTab === "prs"  && <PullRequestView pullRequests={prs} />}
          {activeTab === "ci"   && <CIPipelineView pipelines={runs} />}
        </>
      )}
    </div>
  );
};

export default SprintDashboard;
