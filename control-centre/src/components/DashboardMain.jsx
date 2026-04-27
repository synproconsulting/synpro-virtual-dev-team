import React from "react";

const LINKS = [
  { label: "Sprint Status",  desc: "View sprint progress, run sprints, review PRs",     tab: "sprint" },
  { label: "Workflows",      desc: "Monitor GitHub Actions runs in real-time",           tab: "workflows" },
  { label: "UAT Deploy",     desc: "Deploy services to UAT environment",                tab: "deploy" },
  { label: "SonarCloud",     desc: "Trigger on-demand code quality analysis",           tab: "sonarcloud" },
  { label: "PM Agent",       desc: "Chat with the PM Agent to plan sprints",            tab: "pm-agent" },
];

const DashboardMain = () => (
  <div style={{display:"flex",flexDirection:"column",gap:"1.5rem"}}>
    <div style={{borderBottom:"1px solid var(--border)",paddingBottom:"1rem"}}>
      <div style={{fontSize:22,fontWeight:700,marginBottom:6}}>SynPro Control Centre</div>
      <div style={{fontSize:13,color:"var(--muted)"}}>
        Manage sprints, deployments, code quality and AI-assisted planning from one place.
      </div>
    </div>

    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(280px,1fr))",gap:12}}>
      {LINKS.map(link => (
        <div key={link.tab} style={{
          background:"var(--bg-card)", border:"1px solid var(--border)",
          borderRadius:10, padding:"1.25rem", cursor:"pointer",
          transition:"border-color 0.15s",
        }}
          onMouseEnter={e => e.currentTarget.style.borderColor="var(--accent)"}
          onMouseLeave={e => e.currentTarget.style.borderColor="var(--border)"}
        >
          <div style={{fontSize:15,fontWeight:600,marginBottom:6}}>{link.label}</div>
          <div style={{fontSize:13,color:"var(--muted)"}}>{link.desc}</div>
        </div>
      ))}
    </div>

    <div style={{
      background:"rgba(99,102,241,0.08)", border:"1px solid rgba(99,102,241,0.2)",
      borderRadius:10, padding:"1rem", fontSize:13, color:"var(--muted)"
    }}>
      💡 <strong style={{color:"var(--text)"}}>Tip:</strong> Start with{" "}
      <strong style={{color:"var(--accent)"}}>Sprint Status</strong> to see your current sprint progress,
      or use <strong style={{color:"var(--accent)"}}>PM Agent</strong> to plan a new sprint.
    </div>
  </div>
);

export default DashboardMain;
