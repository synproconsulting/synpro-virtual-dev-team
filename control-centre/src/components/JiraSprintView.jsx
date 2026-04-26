import React, { useState } from 'react';
import { ExternalLink } from 'lucide-react';

const JIRA_URL = import.meta.env.VITE_JIRA_URL || "https://synproconsulting.atlassian.net";

const STATUS_COLORS = {
  "To Do":       { bg: "rgba(100,116,139,0.15)", color: "#94a3b8" },
  "In Progress": { bg: "rgba(59,130,246,0.15)",  color: "#60a5fa" },
  "In Review":   { bg: "rgba(245,158,11,0.15)",  color: "#fbbf24" },
  "Done":        { bg: "rgba(34,197,94,0.15)",   color: "#4ade80" },
  "Blocked":     { bg: "rgba(239,68,68,0.15)",   color: "#f87171" },
};

const PRIORITY_COLORS = {
  "Highest": "#ef4444",
  "High":    "#f97316",
  "Medium":  "#eab308",
  "Low":     "#3b82f6",
  "Lowest":  "#94a3b8",
};

const STATUS_ORDER = ["To Do", "In Progress", "In Review", "Blocked", "Done"];

const IssueRow = ({ issue }) => {
  const sc = STATUS_COLORS[issue.status] || { bg: "rgba(100,116,139,0.15)", color: "#94a3b8" };
  const pc = PRIORITY_COLORS[issue.priority] || "#94a3b8";
  const url = `${JIRA_URL}/browse/${issue.key}`;

  return (
    <div style={{
      display:"flex", alignItems:"flex-start", justifyContent:"space-between",
      padding:"10px 12px", background:"var(--bg)", borderRadius:8,
      border:"1px solid var(--border)", marginBottom:6,
    }}>
      <div style={{flex:1, minWidth:0}}>
        <div style={{display:"flex", alignItems:"center", gap:8, marginBottom:4}}>
          <a href={url} target="_blank" rel="noopener noreferrer"
            style={{color:"var(--accent)", fontWeight:600, fontSize:13,
              textDecoration:"none", display:"flex", alignItems:"center", gap:4}}>
            {issue.key}
            <ExternalLink size={11} />
          </a>
          <span style={{fontSize:11, color:pc, fontWeight:500}}>{issue.priority}</span>
          {issue.points > 0 && (
            <span style={{fontSize:11, color:"var(--muted)",
              background:"var(--bg-hover)", padding:"1px 6px", borderRadius:10}}>
              {issue.points}pts
            </span>
          )}
        </div>
        <div style={{fontSize:13, color:"var(--text)", overflow:"hidden",
          textOverflow:"ellipsis", whiteSpace:"nowrap"}}>{issue.summary}</div>
      </div>
      <span style={{
        fontSize:11, padding:"2px 8px", borderRadius:10, fontWeight:500,
        background:sc.bg, color:sc.color, marginLeft:12, whiteSpace:"nowrap", flexShrink:0
      }}>{issue.status}</span>
    </div>
  );
};

const JiraSprintView = ({ issues = [] }) => {
  const [filter, setFilter] = useState("All");

  const statuses = ["All", ...STATUS_ORDER.filter(s => issues.some(i => i.status === s))];
  const filtered = filter === "All" ? issues : issues.filter(i => i.status === filter);

  const grouped = STATUS_ORDER.reduce((acc, status) => {
    const group = filtered.filter(i => i.status === status);
    if (group.length) acc[status] = group;
    return acc;
  }, {});

  return (
    <div>
      <div style={{display:"flex", gap:6, marginBottom:16, flexWrap:"wrap"}}>
        {statuses.map(s => {
          const count = s === "All" ? issues.length : issues.filter(i => i.status === s).length;
          const sc = s !== "All" ? STATUS_COLORS[s] : null;
          return (
            <button key={s} onClick={() => setFilter(s)} style={{
              background: filter === s ? (sc?.bg || "var(--accent)") : "transparent",
              color: filter === s ? (sc?.color || "white") : "var(--muted)",
              border: `1px solid ${filter === s ? (sc?.color || "var(--accent)") : "var(--border)"}`,
              borderRadius:20, padding:"3px 12px", fontSize:12,
              cursor:"pointer", fontFamily:"inherit"
            }}>{s} ({count})</button>
          );
        })}
      </div>

      {filter === "All" ? (
        Object.entries(grouped).map(([status, group]) => (
          <div key={status} style={{marginBottom:20}}>
            <div style={{fontSize:12, fontWeight:600, color:"var(--muted)",
              textTransform:"uppercase", letterSpacing:"0.05em", marginBottom:8}}>
              {status} ({group.length})
            </div>
            {group.map(issue => <IssueRow key={issue.key} issue={issue} />)}
          </div>
        ))
      ) : (
        filtered.map(issue => <IssueRow key={issue.key} issue={issue} />)
      )}

      {filtered.length === 0 && (
        <div style={{textAlign:"center", color:"var(--muted)", padding:"2rem"}}>
          No issues found
        </div>
      )}
    </div>
  );
};

export default JiraSprintView;
