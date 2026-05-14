import React, { useState, useEffect, useCallback } from 'react';
import { fetchGitHubWorkflows } from '../api/githubApi';
import { useProduct } from '../contexts/ProductContext';
import { ExternalLink, RefreshCw } from 'lucide-react';

const STATUS_STYLE = {
  success:     { bg: "rgba(34,197,94,0.15)",   color: "#4ade80",  label: "✓ Success",   dot: "#4ade80" },
  failure:     { bg: "rgba(239,68,68,0.15)",   color: "#f87171",  label: "✗ Failed",    dot: "#f87171" },
  cancelled:   { bg: "rgba(100,116,139,0.15)", color: "#94a3b8",  label: "⊘ Cancelled", dot: "#94a3b8" },
  skipped:     { bg: "rgba(100,116,139,0.15)", color: "#94a3b8",  label: "— Skipped",   dot: "#94a3b8" },
  in_progress: { bg: "rgba(59,130,246,0.15)",  color: "#60a5fa",  label: "↻ Running",   dot: "#60a5fa" },
  queued:      { bg: "rgba(245,158,11,0.15)",  color: "#fbbf24",  label: "⏳ Queued",    dot: "#fbbf24" },
};

const timeAgo = (dateStr) => {
  if (!dateStr) return "";
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
  if (diff < 60)    return `${diff}s ago`;
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
};

const WORKFLOW_FILTERS = ["All", "Auto Review and Merge", "Auto Implement", "CI Pipeline", "Deploy to UAT"];

const GitHubWorkflowMonitor = () => {
  const { productCredentials, loadingCredentials, credentialsError } = useProduct();
  const githubOrg = productCredentials?.github_org || "";
  const githubRepo = productCredentials?.github_repo || "";
  const ghRepoSlug = githubOrg && githubRepo ? `${githubOrg}/${githubRepo}` : null;

  const [runs, setRuns]       = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const [filter, setFilter]   = useState("All");
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadWorkflows = useCallback(async () => {
    if (!ghRepoSlug) return;
    setLoading(true);
    try {
      const data = await fetchGitHubWorkflows(ghRepoSlug);
      setRuns(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [ghRepoSlug]);

  useEffect(() => {
    if (!ghRepoSlug) {
      setRuns([]); setLastUpdated(null); setError(null);
      return;
    }
    loadWorkflows();
    const interval = setInterval(loadWorkflows, 30000);
    return () => clearInterval(interval);
  }, [ghRepoSlug, loadWorkflows]);

  if (loadingCredentials) {
    return <div style={{textAlign:"center",color:"var(--muted)",padding:"3rem 1rem"}}>Loading product credentials…</div>;
  }
  if (credentialsError) {
    return <div style={{textAlign:"center",color:"var(--muted)",padding:"3rem 1rem"}}>Error loading credentials: {credentialsError}</div>;
  }
  if (!productCredentials) {
    return <div style={{textAlign:"center",color:"var(--muted)",padding:"3rem 1rem"}}>Select a product to view workflows</div>;
  }
  if (!ghRepoSlug) {
    return <div style={{textAlign:"center",color:"var(--muted)",padding:"3rem 1rem"}}>
      Product is missing GitHub org/repo configuration.
    </div>;
  }

  const filtered = filter === "All"
    ? runs
    : runs.filter(r => (r.name || "").includes(filter));

  return (
    <div>
      <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16}}>
        <div>
          <div style={{fontSize:16, fontWeight:600, marginBottom:4}}>GitHub Actions Monitor</div>
          <div style={{fontSize:12, color:"var(--muted)"}}>
            {ghRepoSlug} · Auto-refreshes every 30s
            {lastUpdated && ` · Updated ${timeAgo(lastUpdated.toISOString())}`}
          </div>
        </div>
        <button onClick={loadWorkflows} disabled={loading} style={{
          background:"transparent", border:"1px solid var(--border)",
          borderRadius:8, padding:"6px 12px", cursor:"pointer",
          color:"var(--text)", display:"flex", alignItems:"center", gap:6, fontSize:13
        }}>
          <RefreshCw size={13} style={{animation: loading ? "spin 1s linear infinite" : "none"}} />
          Refresh
        </button>
      </div>

      <div style={{display:"flex", gap:6, marginBottom:16, flexWrap:"wrap"}}>
        {WORKFLOW_FILTERS.map(f => {
          const count = f === "All" ? runs.length : runs.filter(r => (r.name||"").includes(f)).length;
          return (
            <button key={f} onClick={() => setFilter(f)} style={{
              background: filter === f ? "var(--accent)" : "transparent",
              color: filter === f ? "white" : "var(--muted)",
              border: `1px solid ${filter === f ? "var(--accent)" : "var(--border)"}`,
              borderRadius:20, padding:"3px 12px", fontSize:12,
              cursor:"pointer", fontFamily:"inherit"
            }}>{f} ({count})</button>
          );
        })}
      </div>

      {error && (
        <div style={{background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)",
          borderRadius:8, padding:"10px 14px", color:"#f87171", fontSize:13, marginBottom:12}}>
          Error loading workflows: {error}
        </div>
      )}

      {loading && runs.length === 0 ? (
        <div style={{textAlign:"center", color:"var(--muted)", padding:"2rem"}}>
          Loading workflow runs...
        </div>
      ) : filtered.length === 0 ? (
        <div style={{textAlign:"center", color:"var(--muted)", padding:"2rem"}}>
          No workflow runs found
        </div>
      ) : (
        <div style={{display:"flex", flexDirection:"column", gap:6}}>
          {filtered.map(run => {
            const status = run.status === "completed" ? run.conclusion : run.status;
            const style  = STATUS_STYLE[status] || STATUS_STYLE.queued;
            const duration = run.updated_at && run.created_at
              ? Math.round((new Date(run.updated_at) - new Date(run.created_at)) / 1000)
              : null;

            return (
              <div key={run.id} style={{
                display:"flex", alignItems:"center", justifyContent:"space-between",
                padding:"10px 14px", background:"var(--bg)",
                border:"1px solid var(--border)", borderRadius:8,
              }}>
                <div style={{display:"flex", alignItems:"center", gap:10, flex:1, minWidth:0}}>
                  <div style={{width:8, height:8, borderRadius:"50%",
                    background:style.dot, flexShrink:0}} />
                  <div style={{flex:1, minWidth:0}}>
                    <div style={{display:"flex", alignItems:"center", gap:6, marginBottom:2}}>
                      <span style={{fontSize:13, fontWeight:500, color:"var(--text)"}}>
                        {typeof run.name === "string" ? run.name : "Workflow Run"}
                      </span>
                      <a href={run.html_url} target="_blank" rel="noopener noreferrer"
                        style={{color:"var(--muted)"}}>
                        <ExternalLink size={11} />
                      </a>
                    </div>
                    <div style={{fontSize:11, color:"var(--muted)", display:"flex", gap:10}}>
                      <span style={{overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap", maxWidth:300}}>
                        {typeof run.display_title === "string" ? run.display_title :
                         typeof run.head_commit?.message === "string"
                           ? run.head_commit.message.split("\n")[0].slice(0, 60) : ""}
                      </span>
                      <span style={{flexShrink:0}}>{timeAgo(run.created_at)}</span>
                      {duration && <span style={{flexShrink:0}}>{duration < 60 ? `${duration}s` : `${Math.floor(duration/60)}m ${duration%60}s`}</span>}
                    </div>
                  </div>
                </div>
                <span style={{
                  fontSize:11, padding:"2px 10px", borderRadius:10, fontWeight:500,
                  background:style.bg, color:style.color, marginLeft:12,
                  whiteSpace:"nowrap", flexShrink:0
                }}>{style.label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default GitHubWorkflowMonitor;
