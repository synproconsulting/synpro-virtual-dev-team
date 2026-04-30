"""
tools/dev_tools.py
------------------
CrewAI tool wrappers for the Developer Agent.
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
from tools import github_client as gh


class NoInput(BaseModel):
    pass

class CreateBranchInput(BaseModel):
    branch_name: str = Field(...)
    from_branch: str = Field("main")

class CommitMultipleInput(BaseModel):
    files:   list[dict] = Field(...)
    message: str        = Field(...)
    branch:  str        = Field(...)

class ReadFileInput(BaseModel):
    path:   str = Field(...)
    branch: str = Field("main")

class CreatePRInput(BaseModel):
    title:       Optional[str] = Field(None)
    subject:     Optional[str] = Field(None)   # alias
    name:        Optional[str] = Field(None)   # alias
    body:        Optional[str] = Field(None)
    description: Optional[str] = Field(None)   # alias
    head_branch: Optional[str] = Field(None)
    head:        Optional[str] = Field(None)
    base_branch: Optional[str] = Field("main")
    base:        Optional[str] = Field(None)


class ReadFileTool(BaseTool):
    name:        str = "read_file"
    description: str = (
        "Read the current content of a file from the GitHub repository. "
        "Use this BEFORE committing any file that may already exist so you can merge "
        "your changes into the existing content rather than overwriting it. "
        "Returns the full file text, or an empty string if the file does not exist."
    )
    args_schema: type = ReadFileInput

    def _run(self, path: str, branch: str = "main") -> str:
        result = gh.get_file(path, branch)
        if result is None:
            return f"File '{path}' does not exist on branch '{branch}'."
        return result.get("content", "")


class EnsureRepoTool(BaseTool):
    name:        str = "ensure_repo_exists"
    description: str = "Create the GitHub repo if it does not exist. Always call this first."
    args_schema: type = NoInput

    def _run(self, **_) -> str:
        repo = gh.ensure_repo_exists()
        return f"Repo ready: {gh.get_repo_url()} (default branch: {repo.get('default_branch','main')})"


class ListBranchesTool(BaseTool):
    name:        str = "list_branches"
    description: str = "List all branches in the GitHub repository."
    args_schema: type = NoInput

    def _run(self, **_) -> str:
        branches = gh.list_branches()
        if not branches:
            return "No branches found."
        return "\n".join(b["name"] for b in branches)


class CreateBranchTool(BaseTool):
    name:        str = "create_branch"
    description: str = (
        "Create a fresh feature branch from main. "
        "Deletes any existing branch with the same name and recreates from latest main SHA. "
        "Name it: feature/<ticket-id>-<slug>"
    )
    args_schema: type = CreateBranchInput

    def _run(self, branch_name: str, from_branch: str = "main") -> str:
        gh.create_branch(branch_name, from_branch)
        return f"Branch '{branch_name}' created fresh from '{from_branch}'."


class CommitMultipleFilesTool(BaseTool):
    name:        str = "commit_multiple_files"
    description: str = (
        "Commit all implementation files in one clean commit. "
        "Call this ONCE after writing all files — do not call it per file. "
        "The files parameter must be a list of dicts, each with 'path' and 'content' keys. "
        "Example: [{"path": "src/auth/register.py", "content": "import os"}]"
    )
    args_schema: type = CommitMultipleInput

    def _run(self, files: list[dict], message: str, branch: str) -> str:
        normalised = []
        for f in files:
            if not isinstance(f, dict):
                continue
            path = (f.get("path") or f.get("filename") or
                    f.get("file_path") or f.get("name") or "")
            file_content = (f.get("content") or f.get("file_content") or
                            f.get("code") or f.get("text") or "")
            if path and file_content:
                normalised.append({"path": str(path), "content": str(file_content)})

        if not normalised:
            sample = str(files[:1])[:300] if files else "empty list"
            return (
                "ERROR: no valid files found. Each item needs path and content keys. "
                "Received: " + sample + ". "
                "Please retry with correct format."
            )

        result = gh.commit_multiple_files(normalised, message, branch)
        sha = result.get("commit_sha", "unknown")[:8]
        file_list = ", ".join(result.get("files", []))
        return f"Committed {len(normalised)} files to '{branch}' (sha: {sha}): {file_list}"


class CreatePRTool(BaseTool):
    name:        str = "create_pull_request"
    description: str = "Open a pull request from a feature branch to main."
    args_schema: type = CreatePRInput

    def _run(self, title: Optional[str] = None, subject: Optional[str] = None,
             name: Optional[str] = None, body: Optional[str] = None,
             description: Optional[str] = None,
             head_branch: Optional[str] = None, head: Optional[str] = None,
             base_branch: Optional[str] = None, base: Optional[str] = None) -> str:
        pr_title  = title or subject or name or "New Pull Request"
        pr_body   = body or description or ""
        branch    = head_branch or head or ""
        target    = base_branch or base or "main"
        if not branch:
            return "Error: head_branch is required. Please provide the feature branch name."
        result = gh.create_pull_request(pr_title, pr_body, branch, target)
        if result.get("existing"):
            return f"PR #{result['number']} already exists: {result['url']}"
        return f"PR #{result.get('number')} opened: {result.get('html_url')}"


class ListPRsTool(BaseTool):
    name:        str = "list_pull_requests"
    description: str = "List open pull requests in the repository."
    args_schema: type = NoInput

    def _run(self, **_) -> str:
        prs = gh.list_pull_requests()
        if not prs:
            return "No open pull requests."
        return "\n".join(
            f"PR #{p['number']}: {p['title']} ({p['branch']}) -- {p['url']}"
            for p in prs
        )


ALL_DEV_TOOLS = [
    EnsureRepoTool(),
    ReadFileTool(),
    ListBranchesTool(),
    CreateBranchTool(),
    CommitMultipleFilesTool(),
    CreatePRTool(),
    ListPRsTool(),
]
