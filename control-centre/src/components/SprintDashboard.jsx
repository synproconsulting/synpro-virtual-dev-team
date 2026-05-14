import React, { useState, useEffect, useCallback } from 'react';
import { fetchSprints, fetchSprintIssues, fetchSprintData, triggerSprint, triggerAutoReview, fetchMergedPRs, completeSprint } from '../api/sprintApi';
import JiraSprintView from './JiraSprintView';
import PullRequestView from './PullRequestView';
import CIPipelineView from './CIPipelineView';
import { useProduct } from '../contexts/ProductContext';
import { Play, GitPullRequest } from 'lucide-react';

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return dateStr;
  }
};

const STATE_STYLE = {
  active:  { bg: '#4ade80', text: '#052e16' },
  closed:  { bg: 'rgba(148,163,184,0.2)', text: '#94a3b8' },
  future:  { bg: 'rgba(96,165,250,0.2)', text: '#60a5fa' },
};

const MetricCard = ({ title, value, sub, color }) => (
  <div style={{background:"var(--bg-card)",border:"1px solid var(--border)",borderRadius:10,padding:"1rem",borderLeft:color?`3px solid ${color}`:undefined}}>
    <div style={{fontSize:12,color:"var(--muted)",marginBottom:6}}>{title}</div>
    <div style={{fontSize:22,fontWeight:600}}>{value}</div>
    {sub && <div style={{fontSize:11,color:"var(--muted)",marginTop:4}}>{sub}</div>}
  </div>
);

const EmptyState = ({ message }) => (
  <div style={{textAlign:"center",color:"var(--muted)",padding:"3rem 1rem",
               background:"var(--bg-card)",border:"1px solid var(--border)",borderRadius:10}}>
    {message}
  </div>
);

const SprintDashboard = () => {
  const { productCredentials, loadingCredentials, credentialsError } = useProduct();
  const productId = productCredentials?.id || null;
  const jiraProjectKey = productCredentials?.jira_project_key || null;

  const [sprints, setSprints]       = useState([]);
  const [selected, setSelected]     = useState(null);
  const [issues, setIssues]         = useState([]);
  const [globalData, setGlobalData] = useState(null);
  const [loading, setLoading]       = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [msg, setMsg]               = useState(null);
  const [activeTab, setActiveTab]   = useState("jira");
  const [mergedPRs, setMergedPRs]   = useState([]);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [completeDestination, setCompleteDestination] = useState("backlog");
  const [nextSprintTarget, setNextSprintTarget] = useState("");
  const [completing, setCompleting]         = useState(false);

  const loadGlobal = useCallback(async () => {
    if (!productCredentials) return;
    setGlobalData(await fetchSprintData(productCredentials));
  }, [productCredentials]);

  useEffect(() => {
    if (!productCredentials) {
      setSprints([]); setSelected(null); setIssues([]);
      setGlobalData(null); setMergedPRs([]); setLoading(false);
      return;
    }
    let cancelled = false;
    const init = async () => {
      setLoading(true);
      const [sprintList, global, merged] = await Promise.all([
        fetchSprints(productId),
        fetchSprintData(productCredentials),
        fetchMergedPRs(productCredentials),
      ]);
      if (cancelled) return;
      setMergedPRs(merged);
      setSprints(sprintList);
      setGlobalData(global);
      if (sprintList.length) {
        const activeSprint  = sprintList.find(s => s.state === 'active');
        const defaultSprint = activeSprint || sprintList[sprintList.length - 1];
        setSelected(defaultSprint);
        const sprintIssues = await fetchSprintIssues(defaultSprint, productId);
        if (!cancelled) setIssues(sprintIssues);
      } else {
        setSelected(null);
        setIssues([]);
      }
      if (!cancelled) setLoading(false);
    };
    init();
    const iv = setInterval(loadGlobal, 60000);
    return () => { cancelled = true; clearInterval(iv); };
  }, [productCredentials, productId, loadGlobal]);

  const onSprintChange = async (sprint) => {
    setSelected(sprint); setLoading(true); setMsg(null);
    setIssues(await fetchSprintIssues(sprint, productId));
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

  const openCompleteDialog = () => {
    const nextSprints = sprints.filter(s => s.id !== selected?.id && s.state !== "closed");
    setNextSprintTarget(nextSprints.length > 0 ? (nextSprints[0].nativeId || "") : "");
    setCompleteDestination("backlog");
    setShowCompleteDialog(true);
  };

  const handleCompleteSprint = async () => {
    if (!selected?.nativeId) return;
    setCompleting(true);
    const nextId = completeDestination === "nextSprint" ? nextSprintTarget : null;
    const result = await completeSprint(selected.nativeId, completeDestination, nextId);
    setCompleting(false);
    setShowCompleteDialog(false);
    if (result.success) {
      setSprints(prev => prev.map(s => s.id === selected.id ? { ...s, state: "closed" } : s));
      setSelected(prev => ({ ...prev, state: "closed" }));
      setMsg({ success: true, text: "✓ Sprint completed successfully" });
    } else {
      setMsg({ success: false, text: `✗ Failed to complete sprint: ${result.error || "Unknown error"}` });
    }
  };

  if (loadingCredentials) {
    return <EmptyState message="Loading product credentials…" />;
  }
  if (credentialsError) {
    return <EmptyState message={`Error loading credentials: ${credentialsError}`} />;
  }
  if (!productCredentials) {
    return <EmptyState message="Select a product to view sprint data" />;
  }

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
      {jiraProjectKey && (
        <div style={{fontSize:11,color:"var(--muted)",marginBottom:-4}}>
          Jira project: <strong style={{color:"var(--fg)"}}>{jiraProjectKey}</strong>
        </div>
      )}

      {/* Sprint selector + buttons */}
      <div style={{background:"var(--bg-card)",border:"1px solid var(--border)",borderRadius:10,padding:"1rem"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:12}}>
          <div style={{position:"relative",flex:1,minWidth:0}}>
            <div style={{
              display:"flex", gap:6, overflowX:"auto", paddingBottom:2,
              scrollbarWidth:"none", msOverflowStyle:"none",
            }}>
              {sprints.map(sprint => {
                const isActive   = sprint.state === 'active';
                const isSelected = selected?.id === sprint.id;
                const stStyle    = STATE_STYLE[sprint.state] || STATE_STYLE.closed;
                return (
                  <button key={sprint.id} onClick={() => onSprintChange(sprint)} style={{
                    background: isSelected ? (isActive ? '#16a34a' : 'var(--accent)') : 'var(--bg)',
                    color:      isSelected ? 'white' : isActive ? '#4ade80' : 'var(--muted)',
                    border:     `1px solid ${isSelected ? (isActive ? '#16a34a' : 'var(--accent)') : isActive ? '#4ade80' : 'var(--border)'}`,
                    borderRadius: 20, padding: '4px 10px 4px 12px', fontSize: 12,
                    cursor: 'pointer', fontFamily: 'inherit', fontWeight: 500,
                    flexShrink: 0, display: 'flex', alignItems: 'center', gap: 5,
                  }}>
                    <span>{sprint.name.split(' - ')[0]}</span>
                    <span style={{
                      background:    isSelected ? 'rgba(255,255,255,0.25)' : stStyle.bg,
                      color:         isSelected ? 'white' : stStyle.text,
                      fontSize:      9, fontWeight: 700, padding: '1px 5px',
                      borderRadius:  8, letterSpacing: '0.05em', textTransform: 'uppercase',
                    }}>{sprint.state || '?'}</span>
                  </button>
                );
              })}
            </div>
            <div style={{
              position:"absolute", right:0, top:0, bottom:0, width:32,
              background:"linear-gradient(to right, transparent, var(--bg-card))",
              pointerEvents:"none",
            }}/>
          </div>
          <div style={{display:"flex",gap:8,alignItems:"center"}}>
            {selected?.state === "active" && selected?.nativeId && (
              <button onClick={openCompleteDialog} disabled={completing} style={{
                background:"#ef4444",color:"white",border:"none",borderRadius:8,
                padding:"7px 14px",fontSize:12,fontFamily:"inherit",fontWeight:500,
                cursor:completing?"not-allowed":"pointer",opacity:completing?0.7:1,flexShrink:0,
              }}>
                {completing ? "Completing..." : "Complete Sprint"}
              </button>
            )}
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

      {/* Metrics */}
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10}}>
        <MetricCard title="Completion" value={`${pct}%`} sub={`${done.length}/${issues.length} issues`} color={pct===100?"#4ade80":pct>50?"#60a5fa":"#fbbf24"}/>
        <MetricCard title="Story Points" value={`${donePts}/${totalPts}`} sub={`${totalPts-donePts} remaining`} color="#a855f7"/>
        <MetricCard title="In Progress" value={inProg.length} sub={`${todo.length} to do`} color="#60a5fa"/>
        <MetricCard title="CI Success Rate" value={`${ciRate}%`} sub={`${runs.length} recent runs`} color={ciRate>=80?"#4ade80":"#f87171"}/>
      </div>

      {/* Progress bar + sprint info */}
      {issues.length > 0 && (
        <div style={{background:"var(--bg-card)",border:"1px solid var(--border)",borderRadius:10,padding:"1rem"}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",fontSize:12,color:"var(--muted)",marginBottom:8}}>
            <div>
              <span style={{fontWeight:500,color:"var(--fg)"}}>{selected?.name}</span>
              {selected?.startDate && (
                <span style={{marginLeft:8,fontSize:11}}>
                  {formatDate(selected.startDate)}{selected.endDate ? ` – ${formatDate(selected.endDate)}` : ''}
                </span>
              )}
            </div>
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

      {/* Complete Sprint confirmation dialog */}
      {showCompleteDialog && (
        <div style={{
          position:"fixed",top:0,left:0,right:0,bottom:0,
          background:"rgba(0,0,0,0.6)",zIndex:1000,
          display:"flex",alignItems:"center",justifyContent:"center",
        }}>
          <div style={{
            background:"var(--bg-card)",border:"1px solid var(--border)",
            borderRadius:12,padding:"1.5rem",width:440,maxWidth:"90vw",
          }}>
            <h3 style={{margin:"0 0 1rem",fontSize:16,fontWeight:600}}>Complete Sprint</h3>
            <p style={{fontSize:13,color:"var(--muted)",margin:"0 0 1rem"}}>
              <strong style={{color:"var(--fg)"}}>{selected?.name}</strong>{" "}has{" "}
              <strong style={{color:"#4ade80"}}>{done.length} completed</strong> and{" "}
              <strong style={{color:"#fbbf24"}}>{todo.length + inProg.length} incomplete</strong>
              {" "}ticket{todo.length + inProg.length !== 1 ? "s" : ""}.
            </p>
            {(todo.length + inProg.length) > 0 && (
              <div style={{marginBottom:"1rem"}}>
                <label style={{fontSize:12,color:"var(--muted)",display:"block",marginBottom:6}}>
                  Move incomplete tickets to:
                </label>
                <select
                  value={completeDestination}
                  onChange={e => setCompleteDestination(e.target.value)}
                  style={{
                    background:"var(--bg)",border:"1px solid var(--border)",
                    borderRadius:6,padding:"6px 10px",fontSize:13,
                    color:"var(--fg)",width:"100%",fontFamily:"inherit",
                  }}
                >
                  <option value="backlog">Backlog</option>
                  <option value="nextSprint">Next Sprint</option>
                </select>
                {completeDestination === "nextSprint" && (
                  <select
                    value={nextSprintTarget}
                    onChange={e => setNextSprintTarget(e.target.value)}
                    style={{
                      background:"var(--bg)",border:"1px solid var(--border)",
                      borderRadius:6,padding:"6px 10px",fontSize:13,
                      color:"var(--fg)",width:"100%",fontFamily:"inherit",marginTop:8,
                    }}
                  >
                    {sprints
                      .filter(s => s.id !== selected?.id && s.state !== "closed")
                      .map(s => <option key={s.id} value={s.nativeId || s.id}>{s.name}</option>)
                    }
                  </select>
                )}
              </div>
            )}
            <div style={{display:"flex",gap:8,justifyContent:"flex-end",marginTop:4}}>
              <button
                onClick={() => setShowCompleteDialog(false)}
                style={{
                  background:"transparent",border:"1px solid var(--border)",
                  borderRadius:6,padding:"7px 16px",fontSize:12,
                  color:"var(--muted)",cursor:"pointer",fontFamily:"inherit",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleCompleteSprint}
                disabled={completing}
                style={{
                  background:"#ef4444",color:"white",border:"none",
                  borderRadius:6,padding:"7px 16px",fontSize:12,
                  cursor:completing?"not-allowed":"pointer",
                  fontFamily:"inherit",fontWeight:500,opacity:completing?0.7:1,
                }}
              >
                {completing ? "Completing..." : "Complete Sprint"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SprintDashboard;
