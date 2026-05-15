import React, { useState } from 'react';
import { ExternalLink, Download } from 'lucide-react';

const JIRA_URL = import.meta.env.VITE_JIRA_URL || "https://synproconsulting.atlassian.net";

// Local CSV download helpers (SDT1-93). Duplicated per file per spec to
// avoid adding a new module — keep changes in sync if edited.
const downloadCsv = (rows, filename) => {
  if (!rows.length) return;
  const cols = Object.keys(rows[0]);
  const esc  = (v) => {
    if (v == null) return "";
    const s = String(v);
    return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const header = cols.join(",");
  const body   = rows.map(r => cols.map(c => esc(r[c])).join(",")).join("\n");
  const blob   = new Blob([`${header}\n${body}`], { type: "text/csv;charset=utf-8;" });
  const url    = URL.createObjectURL(blob);
  const a      = document.createElement("a");
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
const csvFilename = (tabName, sprintName, productSlug) => {
  const date = new Date().toISOString().slice(0, 10);
  return `sprint-${sprintName || "unknown"}_${productSlug || "unknown"}_${tabName}_${date}.csv`;
};

const STATUS_COLORS = {
  "To Do":       { bg: "rgba(100,116,139,0.15)", color: "#94a3b8" },
  "In Progress": { bg: "rgba(59,130,246,0.15)",  color: "#60a5fa" },
  "In Review":   { bg: "rgba(245,158,11,0.15)",  color: "#fbbf24" },
  "Done":        { bg: "rgba(34,197,94,0.15)",   color: "#4ade80" },
  "Blocked":     { bg: "rgba(239,68,68,0.15)",   color: "#f87171" },
};
const getStatusColor = (s) => STATUS_COLORS[s] || { bg: "rgba(99,102,241,0.15)", color: "#818cf8" };

const PRIORITY_COLORS = { "Highest":"#ef4444","High":"#f97316","Medium":"#eab308","Low":"#3b82f6","Lowest":"#94a3b8" };
const PRIORITY_ICONS  = { "Highest":"↑↑","High":"↑","Medium":"→","Low":"↓","Lowest":"↓↓" };

const IssueTypeIcon = ({ type }) => {
  const T = { "Story":{bg:"#22c55e",s:"▶"},"Epic":{bg:"#a855f7",s:"⚡"},"Bug":{bg:"#ef4444",s:"⬡"},"Task":{bg:"#3b82f6",s:"✓"},"Sub-task":{bg:"#60a5fa",s:"↳"},"Subtask":{bg:"#60a5fa",s:"↳"} };
  const t = T[type] || { bg:"#94a3b8", s:"◆" };
  return <span title={type} style={{display:"inline-flex",alignItems:"center",justifyContent:"center",width:16,height:16,borderRadius:3,background:t.bg,fontSize:9,color:"white",fontWeight:700,flexShrink:0}}>{t.s}</span>;
};

const IssueRow = ({ issue, mergedPR }) => {
  const sc = getStatusColor(issue.status);
  return (
    <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"8px 12px",background:"var(--bg)",borderRadius:8,border:"1px solid var(--border)",marginBottom:5,gap:10}}>
      <div style={{display:"flex",alignItems:"center",gap:8,flex:1,minWidth:0}}>
        <IssueTypeIcon type={issue.type} />
        <span title={issue.priority} style={{fontSize:10,color:PRIORITY_COLORS[issue.priority]||"#94a3b8",fontWeight:700,minWidth:14,textAlign:"center"}}>{PRIORITY_ICONS[issue.priority]||"→"}</span>
        <a href={`${JIRA_URL}/browse/${issue.key}`} target="_blank" rel="noopener noreferrer"
          style={{color:"var(--accent)",fontWeight:600,fontSize:12,textDecoration:"none",flexShrink:0,display:"flex",alignItems:"center",gap:3}}>
          {issue.key}<ExternalLink size={10}/>
        </a>
        <span style={{fontSize:13,color:"var(--text)",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{issue.summary}</span>
        {issue.points > 0 && <span style={{fontSize:11,color:"var(--muted)",background:"var(--bg-hover)",padding:"1px 6px",borderRadius:10,flexShrink:0}}>{issue.points}pts</span>}
      {mergedPR && (
        <a href={mergedPR.url} target="_blank" rel="noopener noreferrer" style={{
          fontSize:11, color:"#4ade80", textDecoration:"none",
          background:"rgba(34,197,94,0.1)", padding:"1px 8px",
          borderRadius:10, flexShrink:0, display:"flex", alignItems:"center", gap:3,
        }}>
          ✓ PR #{mergedPR.number}
        </a>
      )}
      </div>
      <span style={{fontSize:11,padding:"2px 8px",borderRadius:10,fontWeight:500,background:sc.bg,color:sc.color,whiteSpace:"nowrap",flexShrink:0}}>{issue.status}</span>
    </div>
  );
};

const JiraSprintView = ({ issues = [], mergedPRs = [], sprintName, productSlug }) => {
  const [filter, setFilter] = useState("All");

  // Dynamic: derive unique statuses from actual data
  const uniqueStatuses = ["All", ...Array.from(new Set(issues.map(i => i.status)))];

  // Build a map of ticketKey -> merged PR for quick lookup
  const prByTicket = mergedPRs.reduce((acc, pr) => {
    if (pr.ticketKey) acc[pr.ticketKey] = pr;
    return acc;
  }, {});
  const filtered = filter === "All" ? issues : issues.filter(i => i.status === filter);

  // For "All" view group by status in order they appear
  const grouped = uniqueStatuses.slice(1).reduce((acc, s) => {
    const g = filtered.filter(i => i.status === s);
    if (g.length) acc[s] = g;
    return acc;
  }, {});

  // Type legend
  const typeStats = issues.reduce((acc, i) => { acc[i.type] = (acc[i.type]||0)+1; return acc; }, {});

  const handleDownloadCsv = () => {
    const rows = filtered.map(i => ({
      key:      i.key,
      summary:  i.summary,
      type:     i.type,
      status:   i.status,
      priority: i.priority,
      points:   i.points,
      order:    i.order,
      assignee: i.assignee || "",
    }));
    downloadCsv(rows, csvFilename("jira-issues", sprintName, productSlug));
  };

  return (
    <div>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12,flexWrap:"wrap",gap:8}}>
        <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
          {uniqueStatuses.map(s => {
            const count = s === "All" ? issues.length : issues.filter(i => i.status === s).length;
            const sc = s !== "All" ? getStatusColor(s) : null;
            return (
              <button key={s} onClick={() => setFilter(s)} style={{
                background: filter===s ? (sc?.bg||"var(--accent)") : "transparent",
                color: filter===s ? (sc?.color||"white") : "var(--muted)",
                border: `1px solid ${filter===s ? (sc?.color||"var(--accent)") : "var(--border)"}`,
                borderRadius:20, padding:"3px 12px", fontSize:12, cursor:"pointer", fontFamily:"inherit"
              }}>{s} ({count})</button>
            );
          })}
        </div>
        <div style={{display:"flex",gap:10,alignItems:"center"}}>
          {Object.entries(typeStats).map(([type,count]) => (
            <div key={type} style={{display:"flex",alignItems:"center",gap:4,fontSize:11,color:"var(--muted)"}}>
              <IssueTypeIcon type={type}/><span>{count}</span>
            </div>
          ))}
          <button onClick={handleDownloadCsv} disabled={!filtered.length} title="Download CSV" style={{
            background:"transparent", color:"var(--accent)",
            border:"1px solid var(--accent)", borderRadius:6,
            padding:"4px 10px", fontSize:12,
            cursor: filtered.length ? "pointer" : "not-allowed",
            opacity: filtered.length ? 1 : 0.5,
            fontFamily:"inherit", display:"flex", alignItems:"center", gap:4, flexShrink:0,
          }}>
            <Download size={12}/>CSV
          </button>
        </div>
      </div>

      {filter === "All"
        ? Object.entries(grouped).map(([status, group]) => {
            const sc = getStatusColor(status);
            return (
              <div key={status} style={{marginBottom:20}}>
                <div style={{fontSize:11,fontWeight:600,color:"var(--muted)",textTransform:"uppercase",letterSpacing:"0.05em",marginBottom:8,display:"flex",alignItems:"center",gap:6}}>
                  <span style={{width:6,height:6,borderRadius:"50%",background:sc.color,display:"inline-block"}}/>
                  {status} ({group.length})
                </div>
                {group.map(issue => <IssueRow key={issue.key} issue={issue} mergedPR={prByTicket[issue.key]}/>)}
              </div>
            );
          })
        : filtered.map(issue => <IssueRow key={issue.key} issue={issue} mergedPR={prByTicket[issue.key]}/>)
      }

      {filtered.length === 0 && (
        <div style={{textAlign:"center",color:"var(--muted)",padding:"2rem"}}>No issues found</div>
      )}
    </div>
  );
};

export default JiraSprintView;
