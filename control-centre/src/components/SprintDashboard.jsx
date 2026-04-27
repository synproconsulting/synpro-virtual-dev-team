import React, { useState, useEffect, useCallback } from 'react';
import { fetchSprints, fetchSprintIssues, fetchSprintData, triggerSprint, triggerAutoReview, fetchMergedPRs } from '../api/sprintApi';
import JiraSprintView from './JiraSprintView';
import PullRequestView from './PullRequestView';
import CIPipelineView from './CIPipelineView';
import { Play, GitPullRequest } from 'lucide-react';

const MetricCard = ({ title, value, sub, color }) => (
  <div style={{background:"var(--bg-card)",border:"1px solid var(--border)",borderRadius:10,padding:"1rem",borderLeft:color?`3px solid ${color}`:undefined}}>
    <div style={{fontSize:12,color:"var(--muted)",marginBottom:6}}>{title}</div>
    <div style={{fontSize:22,fontWeight:600}}>{value}</div>
    {sub && <div style={{fontSize:11,color:"var(--muted)",marginTop:4}}>{sub}</div>}
  </div>
);

const SprintDashboard = () => {
  const [sprints, setSprints]       = useState([]);
  const [selected, setSelected]     = useState(null);
  const [issues, setIssues]         = useState([]);
  const [globalData, setGlobalData] = useState(null);
  const [loading, setLoading]       = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [msg, setMsg]               = useState(null);
  const [activeTab, setActiveTab]   = useState("jira");

  const loadGlobal = useCallback(async () => {
    setGlobalData(await fetchSprintData());
  }, []);

  useEffect(() => {
    const init = async () => {
      const [sprintList, global, merged] = await Promise.all([fetchSprints(), fetchSprintData(), fetchMergedPRs()]);
      setMergedPRs(merged);
      setSprints(sprintList);
      setGlobalData(global);
      if (sprintList.length) {
        const latest = sprintList[sprintList.length - 1];
        setSelected(latest);
        setIssues(await fetchSprintIssues(latest.id));
      }
      setLoading(false);
    };
    init();
    const iv = setInterval(loadGlobal, 60000);
    return () => clearInterval(iv);
  }, [loadGlobal]);

  const onSprintChange = async (sprint) => {
    setSelected(sprint); setLoading(true); setMsg(null);
    setIssues(await fetchSprintIssues(sprint.id));
    setLoading(false);
  };

  const handleRunSprint = async () => {
    const todo = issues.filter(i => i.status === "To Do");
    if (!todo.length) return;
    setTriggering(true); setMsg(null);
    const results = await triggerSprint(todo);
    const ok = results.filter(r => r.status === "triggered").length;
    setMsg({ success: ok > 0, text: `${ok > 0 ? "✓" : "✗"} Triggered ${ok}/${todo.length} tickets` });
    setTriggering(false);
  };

  const handleAutoReview = async (prNumber) => {
    await triggerAutoReview(prNumber);
    setMsg({ success: true, text: `✓ Auto Review triggered for PR #${prNumber}` });
  };

  const prs       = globalData?.prs  || [];
  const runs      = globalData?.runs || [];
  const done      = issues.filter(i => i.status === "Done");
  const todo      = issues.filter(i => i.status === "To Do");
  const inProg    = issues.filter(i => i.status === "In Progress");
  const totalPts  = issues.reduce((s, i) => s + (i.points||0), 0);
  const donePts   = done.reduce((s, i) => s + (i.points||0), 0);
  const pct       = issues.length ? Math.round((done.length / issues.length) * 100) : 0;
  const ciRate    = runs.length ? Math.round((runs.filter(r=>r.conclusion==="success").length/runs.length)*100) : 0;

  const TABS = [
    { id:"jira", label:`Jira Issues (${issues.length})` },
    { id:"prs",  label:`Pull Requests (${prs.length})` },
    { id:"ci",   label:`CI/CD (${runs.length})` },
  ];

  return (
    <div style={{display:"flex",flexDirection:"column",gap:"1rem"}}>

      {/* Sprint selector + Run button */}
      <div style={{background:"var(--bg-card)",border:"1px solid var(--border)",borderRadius:10,padding:"1rem"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:12}}>
          <div style={{position:"relative",flex:1,minWidth:0}}>
            <div style={{
              display:"flex", gap:6, overflowX:"auto", paddingBottom:2,
              scrollbarWidth:"none", msOverflowStyle:"none",
            }}>
              {sprints.map(sprint => (
                <button key={sprint.id} onClick={() => onSprintChange(sprint)} style={{
                  background: selected?.id===sprint.id ? "var(--accent)" : "var(--bg)",
                  color: selected?.id===sprint.id ? "white" : "var(--muted)",
                  border: `1px solid ${selected?.id===sprint.id ? "var(--accent)" : "var(--border)"}`,
                  borderRadius:20, padding:"4px 14px", fontSize:12,
                  cursor:"pointer", fontFamily:"inherit", fontWeight:500,
                  flexShrink:0,
                }}>{sprint.name.split(" - ")[0]}</button>
              ))}
            </div>
            <div style={{
              position:"absolute", right:0, top:0, bottom:0, width:32,
              background:"linear-gradient(to right, transparent, var(--bg-card))",
              pointerEvents:"none",
            }}/>
          </div>
          <button onClick={handleRunSprint} disabled={triggering||todo.length===0} style={{
            background: todo.length===0 ? "rgba(99,102,241,0.2)" : "var(--accent)",
            color:"white", border:"none", borderRadius:8, padding:"7px 14px",
            fontSize:12, cursor:todo.length===0?"not-allowed":"pointer",
            fontFamily:"inherit", fontWeight:500, display:"flex", alignItems:"center", gap:6,
            opacity:triggering?0.7:1, flexShrink:0,
          }}>
            <Play size={12}/>
            {triggering ? "Triggering..." : `Run Sprint (${todo.length})`}
          </button>
        </div>
        {msg && (
          <div style={{marginTop:8,padding:"6px 10px",borderRadius:6,fontSize:12,
            background:msg.success?"rgba(34,197,94,0.1)":"rgba(239,68,68,0.1)",
            color:msg.success?"#4ade80":"#f87171",
            border:`1px solid ${msg.success?"rgba(34,197,94,0.2)":"rgba(239,68,68,0.2)"}`}}>
            {msg.text}
          </div>
        )}
      </div>

      {/* Metrics — same style as before */}
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10}}>
        <MetricCard title="Completion" value={`${pct}%`} sub={`${done.length}/${issues.length} issues`} color={pct===100?"#4ade80":pct>50?"#60a5fa":"#fbbf24"}/>
        <MetricCard title="Story Points" value={`${donePts}/${totalPts}`} sub={`${totalPts-donePts} remaining`} color="#a855f7"/>
        <MetricCard title="In Progress" value={inProg.length} sub={`${todo.length} to do`} color="#60a5fa"/>
        <MetricCard title="CI Success Rate" value={`${ciRate}%`} sub={`${runs.length} recent runs`} color={ciRate>=80?"#4ade80":"#f87171"}/>
      </div>

      {/* Progress bar */}
      {issues.length > 0 && (
        <div style={{background:"var(--bg-card)",border:"1px solid var(--border)",borderRadius:10,padding:"1rem"}}>
          <div style={{display:"flex",justifyContent:"space-between",fontSize:12,color:"var(--muted)",marginBottom:8}}>
            <span style={{fontWeight:500}}>{selected?.name}</span>
            <span>{pct}% complete</span>
          </div>
          <div style={{height:8,background:"var(--bg)",borderRadius:4,overflow:"hidden"}}>
            <div style={{height:"100%",width:`${pct}%`,background:pct===100?"#4ade80":"var(--accent)",borderRadius:4,transition:"width 0.3s"}}/>
          </div>
          <div style={{display:"flex",gap:16,marginTop:8,fontSize:11,color:"var(--muted)"}}>
            <span style={{color:"#4ade80"}}>✓ Done: {done.length}</span>
            <span style={{color:"#60a5fa"}}>↻ In Progress: {inProg.length}</span>
            <span style={{color:"#94a3b8"}}>○ To Do: {todo.length}</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{display:"flex",gap:4,borderBottom:"1px solid var(--border)",paddingBottom:2}}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            background:activeTab===t.id?"var(--accent)":"transparent",
            color:activeTab===t.id?"white":"var(--muted)",
            border:"none", borderRadius:6, padding:"6px 14px",
            fontSize:13, cursor:"pointer", fontFamily:"inherit"
          }}>{t.label}</button>
        ))}
      </div>

      {loading ? (
        <div style={{textAlign:"center",color:"var(--muted)",padding:"2rem"}}>Loading...</div>
      ) : (
        <>
          {activeTab === "jira" && <JiraSprintView issues={issues} mergedPRs={mergedPRs}/>}
          {activeTab === "prs" && (
            <div>
              {prs.length === 0 ? (
                <div style={{textAlign:"center",color:"var(--muted)",padding:"2rem"}}>No open pull requests</div>
              ) : prs.map(pr => (
                <div key={pr.number} style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"10px 14px",background:"var(--bg)",border:"1px solid var(--border)",borderRadius:8,marginBottom:6,gap:10}}>
                  <div style={{flex:1,minWidth:0}}>
                    <div style={{fontSize:13,fontWeight:500,marginBottom:2,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                      <a href={pr.html_url} target="_blank" rel="noopener noreferrer" style={{color:"var(--accent)",textDecoration:"none",marginRight:6}}>#{pr.number}</a>
                      {pr.title}
                    </div>
                    <div style={{fontSize:11,color:"var(--muted)"}}>{pr.head?.ref} · {pr.user?.login}</div>
                  </div>
                  <button onClick={() => handleAutoReview(pr.number)} style={{
                    background:"var(--accent)",color:"white",border:"none",
                    borderRadius:6,padding:"5px 12px",fontSize:12,
                    cursor:"pointer",fontFamily:"inherit",
                    display:"flex",alignItems:"center",gap:4,flexShrink:0,
                  }}>
                    <GitPullRequest size={12}/>Auto Review
                  </button>
                </div>
              ))}
            </div>
          )}
          {activeTab === "ci" && <CIPipelineView pipelines={runs}/>}
        </>
      )}
    </div>
  );
};

export default SprintDashboard;
