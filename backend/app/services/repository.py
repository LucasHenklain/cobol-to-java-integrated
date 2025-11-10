"""Repository service for cloning and preparing source code."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional, Tuple

from git import GitCommandError, Repo

from app.core.config import settings

logger = logging.getLogger(__name__)


def _ensure_base_directory() -> Path:
    base_dir = Path(settings.REPOS_DIR)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _inject_token(repo_url: str) -> str:
    """Inject authentication token into HTTPS URLs when available."""
    if repo_url.startswith("http://") or repo_url.startswith("https://"):
        if "github.com" in repo_url and settings.GITHUB_TOKEN:
            return repo_url.replace("https://", f"https://{settings.GITHUB_TOKEN}@", 1)
        if "gitlab.com" in repo_url and settings.GITLAB_TOKEN:
            return repo_url.replace("https://", f"https://oauth2:{settings.GITLAB_TOKEN}@", 1)
    return repo_url


def _checkout_branch(repo: Repo, branch: Optional[str]) -> Optional[str]:
    if not branch:
        return None

    try:
        if branch in repo.heads:
            repo.git.checkout(branch)
            return branch

        remote_ref = f"origin/{branch}"
        remote_refs = {ref.name for ref in repo.refs}
        if remote_ref in remote_refs:
            repo.git.checkout("-B", branch, remote_ref)
            return branch
    except GitCommandError as exc:
        logger.debug("Failed to checkout branch %s: %s", branch, exc)

    return None


def _resolve_default_branch(repo: Repo) -> str:
    try:
        remote_head = repo.git.symbolic_ref("refs/remotes/origin/HEAD")
        return remote_head.split("/")[-1]
    except GitCommandError:
        pass

    candidates = []
    if repo.remotes:
        for ref in repo.remotes[0].refs:
            name = ref.name.split("/")[-1]
            candidates.append(name)

    for fallback in ("main", "master", "develop"):
        if fallback in candidates:
            return fallback

    if candidates:
        return candidates[0]

    if not repo.head.is_detached:
        return repo.active_branch.name

    return "main"


def _ensure_branch(repo: Repo, desired_branch: Optional[str]) -> str:
    selected_branch = _checkout_branch(repo, desired_branch)
    if selected_branch is None:
        if desired_branch:
            logger.warning(
                "Branch '%s' not found. Falling back to repository default.",
                desired_branch,
            )
        default_branch = _resolve_default_branch(repo)
        selected_branch = _checkout_branch(repo, default_branch)
        if selected_branch is None:
            selected_branch = default_branch
            try:
                repo.git.checkout(selected_branch)
            except GitCommandError as exc:
                logger.debug("Fallback checkout failed for %s: %s", selected_branch, exc)

    try:
        repo.git.pull("origin", selected_branch)
    except GitCommandError as exc:
        logger.debug("Pull skipped for %s: %s", selected_branch, exc)

    return selected_branch


def clone_or_update_repository(
    job_id: str,
    repo_url: str,
    branch: str = "main",
) -> Tuple[str, str, str]:
    """Clone or update a repository for the given job.

    Returns a tuple with the repository path, current commit hash, and resolved branch.
    """

    base_dir = _ensure_base_directory()
    job_repo_dir = base_dir / job_id

    auth_url = _inject_token(repo_url)

    repo: Repo
    resolved_branch: str

    try:
        if job_repo_dir.exists():
            repo = Repo(job_repo_dir)
            repo.remote().fetch("--prune")
        else:
            repo = Repo.clone_from(auth_url, job_repo_dir)
        resolved_branch = _ensure_branch(repo, branch)
    except GitCommandError as exc:
        logger.warning("Repository sync failed (%s). Re-cloning from origin.", exc)
        if job_repo_dir.exists():
            shutil.rmtree(job_repo_dir)
        repo = Repo.clone_from(auth_url, job_repo_dir)
        resolved_branch = _ensure_branch(repo, branch)

    commit_hash = repo.head.commit.hexsha if repo.head.is_valid() else ""
    return str(job_repo_dir), commit_hash, resolved_branch
