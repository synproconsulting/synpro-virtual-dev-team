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

// Jira-style issue type icons
const IssueTypeIcon = ({ type }) => {
  const types = {
    "Story": { bg: "#22c55e", symbol: "▶", title: "Story" },
    "Epic":  { bg: "#a855f7", symbol: "⚡", title: "Epic" },
    "Bug":   { bg: "#ef4444", symbol: "⬡", title: "Bug" },
    "Task":  { bg: "#3b82f6", symbol: "✓", title: "Task" },
    "Sub-task": { bg: "#60a5fa", symbol: "↳", title: "Sub-task" },
    "Subtask":  { bg: "#60a5fa", symbol: "↳", title: "Subtask" },
  };
  const t = types[type] || { bg: "#94a3b8", symbol: "◆", title: type || "Issue" };
  return (
    <span title={t.title} style={{
      display:"inline-flex", alignItems:"center", justifyContent:"center",
      width:16, height:16, borderRadius:3, background:t.bg,
      fontSize:9, color:"white", fontWeight:700, flexShrink:0,
    }}>{t.symbol}</span>
  );
};

const PriorityIcon = ({ priority }) => {
  const icons = {
    "Highest": "↑↑",
    "High":    "↑",
    "Medium":  "→",
    "Low":     "↓",
    "Lowest":  "↓↓",
  };
  const color = PRIORITY_COLORS[priority] || "#94a3b8";
  return (
    <span title={priority} style={{
      fontSize:10, color, fontWeight:700, minWidth:14, textAlign:"center"
    }}>{icons[priority] || "→"}</span>
  );
};

const IssueRow = ({ issue }) => {
  const sc  = STATUS_COLORS[issue.status] || { bg: "rgba(100,116,139,0.15)", color: "#94a3b8" };
  const url = `${JIRA_URL}/browse/${issue.key}`;

  return (
    <div style={{
      display:"flex", alignItems:"center", justifyContent:"space-between",
      padding:"8px 12px", background:"var(--bg)", borderRadius:8,
      border:"1px solid var(--border)", marginBottom:5,
      gap:10,
    }}>
      <div style={{display:"flex", alignItems:"center", gap:8, flex:1, minWidth:0}}>
        <IssueTypeIcon type={issue.type} />
        <PriorityIcon priority={issue.priority} />
        <a href={url} target="_blank" rel="noopener noreferrer"
          style={{color:"var(--accent)", fontWeight:600, fontSize:12,
            textDecoration:"none", flexShrink:0, display:"flex", alignItems:"center", gap:3}}>
          {issue.key}
          <ExternalLink size={10} />
        </a>
        <span style={{fontSize:13, color:"var(--text)", overflow:"hidden",
          textOverflow:"ellipsis", whiteSpace:"nowrap"}}>{issue.summary}</span>
        {issue.points > 0 && (
          <span style={{fontSize:11, color:"var(--muted)", background:"var(--bg-hover)",
            padding:"1px 6px", borderRadius:10, flexShrink:0}}>{issue.points}pts</span>
        )}
      </div>
      <span style={{
        fontSize:11, padding:"2px 8px", borderRadius:10, fontWeight:500,
        background:sc.bg, color:sc.color, whiteSpace:"nowrap", flexShrink:0
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

  // Legend
  const typeStats = issues.reduce((acc, i) => {
    acc[i.type] = (acc[i.type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div>
      <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12}}>
        <div style={{display:"flex", gap:6, flexWrap:"wrap"}}>
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
        <div style={{display:"flex", gap:8, alignItems:"center"}}>
          {Object.entries(typeStats).map(([type, count]) => (
            <div key={type} style={{display:"flex", alignItems:"center", gap:4, fontSize:11, color:"var(--muted)"}}>
              <IssueTypeIcon type={type} />
              <span>{count} {type}</span>
            </div>
          ))}
        </div>
      </div>

      {filter === "All" ? (
        Object.entries(grouped).map(([status, group]) => (
          <div key={status} style={{marginBottom:20}}>
            <div style={{fontSize:11, fontWeight:600, color:"var(--muted)",
              textTransform:"uppercase", letterSpacing:"0.05em", marginBottom:8,
              display:"flex", alignItems:"center", gap:6}}>
              <span style={{
                width:6, height:6, borderRadius:"50%",
                background:STATUS_COLORS[status]?.color || "#94a3b8",
                display:"inline-block"
              }}/>
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
