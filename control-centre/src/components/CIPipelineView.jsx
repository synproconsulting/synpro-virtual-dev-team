import React from 'react';
import { ExternalLink, Download } from 'lucide-react';

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

const STATUS_STYLE = {
  success:    { bg: "rgba(34,197,94,0.15)",   color: "#4ade80",  label: "✓ Success" },
  failure:    { bg: "rgba(239,68,68,0.15)",   color: "#f87171",  label: "✗ Failed" },
  cancelled:  { bg: "rgba(100,116,139,0.15)", color: "#94a3b8",  label: "⊘ Cancelled" },
  skipped:    { bg: "rgba(100,116,139,0.15)", color: "#94a3b8",  label: "— Skipped" },
  in_progress:{ bg: "rgba(59,130,246,0.15)",  color: "#60a5fa",  label: "↻ Running" },
  queued:     { bg: "rgba(245,158,11,0.15)",  color: "#fbbf24",  label: "⏳ Queued" },
};

const timeAgo = (dateStr) => {
  if (!dateStr) return "";
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
  if (diff < 60)   return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
};

const CIPipelineView = ({ pipelines = [], sprintName, productSlug }) => {
  const handleDownloadCsv = () => {
    const rows = pipelines.map(r => ({
      id:            r.id,
      name:          r.name,
      status:        r.status,
      conclusion:    r.conclusion || "",
      head_branch:   r.head_branch || "",
      display_title: r.display_title || "",
      created_at:    r.created_at || "",
      updated_at:    r.updated_at || "",
      url:           r.html_url || "",
    }));
    downloadCsv(rows, csvFilename("ci-cd", sprintName, productSlug));
  };

  return (
    <div>
      <div style={{display:"flex", justifyContent:"flex-end", marginBottom:10}}>
        <button onClick={handleDownloadCsv} disabled={!pipelines.length} title="Download CSV" style={{
          background:"transparent", color:"var(--accent)",
          border:"1px solid var(--accent)", borderRadius:6,
          padding:"4px 10px", fontSize:12,
          cursor: pipelines.length ? "pointer" : "not-allowed",
          opacity: pipelines.length ? 1 : 0.5,
          fontFamily:"inherit", display:"flex", alignItems:"center", gap:4,
        }}>
          <Download size={12}/>CSV
        </button>
      </div>
      {!pipelines.length ? (
        <div style={{textAlign:"center", color:"var(--muted)", padding:"2rem"}}>
          No CI/CD runs found
        </div>
      ) : (
    <div style={{display:"flex",flexDirection:"column",gap:8}}>
      {pipelines.map((run) => {
        const status = run.status === "completed" ? run.conclusion : run.status;
        const style  = STATUS_STYLE[status] || STATUS_STYLE.queued;
        const duration = run.updated_at && run.created_at
          ? Math.round((new Date(run.updated_at) - new Date(run.created_at)) / 1000)
          : null;

        return (
          <div key={run.id} style={{
            display:"flex", alignItems:"center", justifyContent:"space-between",
            padding:"10px 14px", background:"var(--bg)", border:"1px solid var(--border)",
            borderRadius:8,
          }}>
            <div style={{flex:1, minWidth:0}}>
              <div style={{display:"flex", alignItems:"center", gap:8, marginBottom:3}}>
                <a href={run.html_url} target="_blank" rel="noopener noreferrer"
                  style={{color:"var(--text)", fontWeight:500, fontSize:13,
                    textDecoration:"none", display:"flex", alignItems:"center", gap:4,
                    overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap"}}>
                  {typeof run.name === "string" ? run.name : "Workflow Run"}
                  <ExternalLink size={11} style={{flexShrink:0}} />
                </a>
              </div>
              <div style={{fontSize:11, color:"var(--muted)", display:"flex", gap:12}}>
                <span>{typeof run.head_commit?.message === "string"
                  ? run.head_commit.message.split("\n")[0].slice(0, 60)
                  : run.display_title || ""}</span>
                <span>{timeAgo(run.created_at)}</span>
                {duration && <span>{duration}s</span>}
              </div>
            </div>
            <span style={{
              fontSize:11, padding:"2px 10px", borderRadius:10, fontWeight:500,
              background:style.bg, color:style.color, marginLeft:12, whiteSpace:"nowrap", flexShrink:0
            }}>{style.label}</span>
          </div>
        );
      })}
    </div>
      )}
    </div>
  );
};

export default CIPipelineView;
