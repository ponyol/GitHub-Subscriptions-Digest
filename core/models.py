"""
Data models for GitHub Subscriptions Digest.

This module defines the Pydantic models that represent the structure
of our digest data, ensuring type safety and validation throughout the application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


class UpdateType(str, Enum):
    """Type of update from a repository."""

    RELEASE = "release"
    COMMIT_BATCH = "commit_batch"


class Update(BaseModel):
    """
    Represents a single update (release or commit batch) from a repository.

    Attributes:
        id: Unique identifier for the update (UUID).
        type: Type of update (release or commit_batch).
        date: ISO 8601 timestamp when the update occurred.
        title: Human-readable title of the update.
        summary_ru: AI-generated summary in Russian (null if not yet generated).
        source_content: Original content (release notes or commit messages).
        source_url: URL to the original source on GitHub.
    """

    id: str = Field(default_factory=lambda: f"update-{uuid4().hex}")
    type: UpdateType
    date: datetime
    title: str
    summary_ru: Optional[str] = None
    source_content: str
    source_url: HttpUrl


class Project(BaseModel):
    """
    Represents a GitHub repository being tracked.

    Attributes:
        name: Repository name in 'owner/repo' format.
        url: Full URL to the repository on GitHub.
        last_checked: ISO 8601 timestamp of last check for updates.
        updates: List of all updates for this project.
    """

    name: str
    url: HttpUrl
    last_checked: datetime
    updates: list[Update] = Field(default_factory=list)


class DigestData(BaseModel):
    """
    Root data structure representing the entire digest database.

    This is the structure that is serialized to/from digest_data.json.

    Attributes:
        last_run_timestamp: ISO 8601 timestamp of the last successful run.
        projects: List of all tracked projects with their updates.
    """

    last_run_timestamp: datetime
    projects: list[Project] = Field(default_factory=list)


class GitHubRelease(BaseModel):
    """
    Represents a GitHub release as returned by the GitHub API.

    Attributes:
        tag_name: Git tag for the release.
        name: Release name (title).
        body: Release notes (markdown).
        published_at: ISO 8601 timestamp when released.
        html_url: URL to the release page.
    """

    tag_name: str
    name: Optional[str] = None
    body: Optional[str] = ""
    published_at: datetime
    html_url: HttpUrl


class GitHubCommit(BaseModel):
    """
    Represents a single GitHub commit as returned by the GitHub API.

    Attributes:
        sha: Commit SHA hash.
        commit: Nested commit details.
        html_url: URL to the commit page.
    """

    sha: str
    commit: dict  # Contains 'message' and 'author' fields
    html_url: HttpUrl


class GitHubRepository(BaseModel):
    """
    Represents a GitHub repository from the subscriptions API.

    Attributes:
        full_name: Repository name in 'owner/repo' format.
        html_url: URL to the repository.
        default_branch: Name of the default branch (usually 'main' or 'master').
    """

    full_name: str
    html_url: HttpUrl
    default_branch: str = "main"
