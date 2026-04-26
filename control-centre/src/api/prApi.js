const GITHUB_API = "https://api.github.com";
const GH_REPO   = import.meta.env.VITE_GITHUB_REPO || "synproconsulting/synpro-virtual-dev-team";
const GH_TOKEN  = import.meta.env.VITE_GITHUB_TOKEN || "";

const ghHeaders = () => ({
  "Accept": "application/vnd.github+json",
  "Content-Type": "application/json",
  ...(GH_TOKEN ? { "Authorization": `Bearer ${GH_TOKEN}` } : {}),
});

export const fetchOpenPRs = async () => {
  const r = await fetch(`${GITHUB_API}/repos/${GH_REPO}/pulls?state=open&per_page=20`, { headers: ghHeaders() });
  return r.ok ? r.json() : [];
};

export const fetchPullRequests = fetchOpenPRs;

export const getReviewStatus = async (prNumber) => {
  const [owner, repo] = GH_REPO.split("/");
  const r = await fetch(`${GITHUB_API}/repos/${owner}/${repo}/pulls/${prNumber}/reviews`, { headers: ghHeaders() });
  return r.ok ? r.json() : [];
};

export const triggerAutoReview = async (prNumber) => {
  const [owner, repo] = GH_REPO.split("/");
  const r = await fetch(
    `${GITHUB_API}/repos/${owner}/${repo}/actions/workflows/auto-review.yml/dispatches`,
    { method: "POST", headers: ghHeaders(),
      body: JSON.stringify({ ref: "main", inputs: { pr_number: String(prNumber) } }) }
  );
  return { success: r.status === 204 };
};

export const mergePR = async (prNumber) => {
  const [owner, repo] = GH_REPO.split("/");
  const r = await fetch(
    `${GITHUB_API}/repos/${owner}/${repo}/pulls/${prNumber}/merge`,
    { method: "PUT", headers: ghHeaders(),
      body: JSON.stringify({ merge_method: "squash" }) }
  );
  return { success: r.ok, data: await r.json() };
};

export const closePR = async (prNumber) => {
  const [owner, repo] = GH_REPO.split("/");
  const r = await fetch(
    `${GITHUB_API}/repos/${owner}/${repo}/pulls/${prNumber}`,
    { method: "PATCH", headers: ghHeaders(),
      body: JSON.stringify({ state: "closed" }) }
  );
  return { success: r.ok };
};

export const getPRDetails = async (prNumber) => {
  const [owner, repo] = GH_REPO.split("/");
  const r = await fetch(`${GITHUB_API}/repos/${owner}/${repo}/pulls/${prNumber}`, { headers: ghHeaders() });
  return r.ok ? r.json() : null;
};

export const getPRCIStatus = async (prNumber) => {
  const [owner, repo] = GH_REPO.split("/");
  const pr = await getPRDetails(prNumber);
  if (!pr) return [];
  const sha = pr.head?.sha;
  if (!sha) return [];
  const r = await fetch(`${GITHUB_API}/repos/${owner}/${repo}/commits/${sha}/check-runs`, { headers: ghHeaders() });
  return r.ok ? (await r.json()).check_runs || [] : [];
};
