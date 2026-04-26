import React from 'react';
import { ExternalLink } from 'lucide-react';

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

const CIPipelineView = ({ pipelines = [] }) => {
  if (!pipelines.length) {
    return (
      <div style={{textAlign:"center", color:"var(--muted)", padding:"2rem"}}>
        No CI/CD runs found
      </div>
    );
  }

  return (
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
  );
};

export default CIPipelineView;
