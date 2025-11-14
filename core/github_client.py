"""
GitHub API client for fetching subscriptions, releases, and commits.

This module provides async functions for interacting with the GitHub REST API
using httpx. All functions are pure and side-effect-free (except for network I/O).
"""

import logging
from datetime import datetime
from typing import Optional

import httpx

from .models import GitHubCommit, GitHubRelease, GitHubRepository

# Structured logging configuration
logger = logging.getLogger(__name__)

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"


class GitHubAPIError(Exception):
    """Raised when the GitHub API returns an error response."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"GitHub API error {status_code}: {message}")


async def fetch_subscriptions(token: str) -> list[GitHubRepository]:
    """
    Fetch all repositories the authenticated user is watching.

    NOTE: This function uses the /user/subscriptions endpoint which returns
    repositories the user is "watching". However, GitHub's watching mechanism
    has different levels (All Activity, Ignore, Custom), and this endpoint
    may not return all watched repositories in all cases.

    Args:
        token: GitHub Personal Access Token with 'repo' scope.

    Returns:
        List of GitHubRepository objects representing watched repositories.

    Raises:
        GitHubAPIError: If the API request fails.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    all_repos: list[dict] = []
    page = 1
    per_page = 100

    logger.info(
        "Fetching user subscriptions",
        extra={"context": "github_api", "operation": "fetch_subscriptions"},
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            url = f"{GITHUB_API_BASE}/user/subscriptions"
            params = {"page": page, "per_page": per_page}

            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(
                    "Failed to fetch subscriptions",
                    extra={
                        "context": "github_api",
                        "status_code": e.response.status_code,
                        "response_body": e.response.text,
                    },
                )
                raise GitHubAPIError(
                    e.response.status_code,
                    f"Failed to fetch subscriptions: {e.response.text}",
                ) from e

            repos_page = response.json()
            if not repos_page:
                break

            all_repos.extend(repos_page)
            logger.debug(
                "Fetched subscriptions page",
                extra={
                    "context": "github_api",
                    "page": page,
                    "repos_count": len(repos_page),
                },
            )

            page += 1

    logger.info(
        "Successfully fetched all subscriptions",
        extra={"context": "github_api", "total_repos": len(all_repos)},
    )

    # Log all repository names for debugging
    validated_repos = [GitHubRepository.model_validate(repo) for repo in all_repos]
    repo_names = [repo.full_name for repo in validated_repos]
    logger.info(
        "Fetched repositories list",
        extra={
            "context": "github_api",
            "repositories": repo_names,
            "total_count": len(repo_names),
        },
    )

    return validated_repos


async def fetch_latest_release(
    token: str, owner: str, repo: str
) -> Optional[GitHubRelease]:
    """
    Fetch the latest release for a repository.

    Args:
        token: GitHub Personal Access Token.
        owner: Repository owner.
        repo: Repository name.

    Returns:
        GitHubRelease object if a release exists, None otherwise.

    Raises:
        GitHubAPIError: If the API request fails (excluding 404).
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases/latest"

    logger.debug(
        "Fetching latest release",
        extra={"context": "github_api", "repo": f"{owner}/{repo}"},
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)

            # 404 is expected if no releases exist
            if response.status_code == 404:
                logger.debug(
                    "No releases found",
                    extra={"context": "github_api", "repo": f"{owner}/{repo}"},
                )
                return None

            response.raise_for_status()
            release_data = response.json()

            logger.debug(
                "Successfully fetched latest release",
                extra={
                    "context": "github_api",
                    "repo": f"{owner}/{repo}",
                    "tag": release_data.get("tag_name"),
                },
            )

            return GitHubRelease.model_validate(release_data)

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to fetch latest release",
                extra={
                    "context": "github_api",
                    "repo": f"{owner}/{repo}",
                    "status_code": e.response.status_code,
                    "response_body": e.response.text,
                },
            )
            raise GitHubAPIError(
                e.response.status_code,
                f"Failed to fetch release: {e.response.text}",
            ) from e


async def fetch_commits_since(
    token: str,
    owner: str,
    repo: str,
    branch: str,
    since: datetime,
) -> list[GitHubCommit]:
    """
    Fetch commits from a repository since a specific timestamp.

    Args:
        token: GitHub Personal Access Token.
        owner: Repository owner.
        repo: Repository name.
        branch: Branch name to fetch commits from.
        since: ISO 8601 timestamp to fetch commits after.

    Returns:
        List of GitHubCommit objects.

    Raises:
        GitHubAPIError: If the API request fails.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
    params = {
        "sha": branch,
        "since": since.isoformat(),
        "per_page": 100,
    }

    logger.debug(
        "Fetching commits since timestamp",
        extra={
            "context": "github_api",
            "repo": f"{owner}/{repo}",
            "branch": branch,
            "since": since.isoformat(),
        },
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            commits_data = response.json()

            logger.debug(
                "Successfully fetched commits",
                extra={
                    "context": "github_api",
                    "repo": f"{owner}/{repo}",
                    "commits_count": len(commits_data),
                },
            )

            return [GitHubCommit.model_validate(commit) for commit in commits_data]

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to fetch commits",
                extra={
                    "context": "github_api",
                    "repo": f"{owner}/{repo}",
                    "status_code": e.response.status_code,
                    "response_body": e.response.text,
                },
            )
            raise GitHubAPIError(
                e.response.status_code,
                f"Failed to fetch commits: {e.response.text}",
            ) from e
