"""
Core module for GitHub Subscriptions Digest.

This module serves as the public API for the digest system, exposing only
the necessary functions and classes for external use.

Following functional programming principles, all exported functions are
pure (except for I/O operations) and side-effect-free.
"""

# Data models
from .models import (
    DigestData,
    GitHubCommit,
    GitHubRelease,
    GitHubRepository,
    Project,
    Update,
    UpdateType,
)

# GitHub API client
from .github_client import (
    GitHubAPIError,
    fetch_commits_since,
    fetch_latest_release,
    fetch_subscriptions,
)

# AI summarization
from .ai_summarizer import (
    GeminiAPIError,
    configure_gemini,
    summarize_commits,
    summarize_release,
    summarize_text,
)

# Data management
from .data_manager import (
    DataManagerError,
    add_or_update_project,
    add_update_to_project,
    find_project,
    load_digest_data,
    save_digest_data,
    update_last_run_timestamp,
)

# Site generation
from .site_generator import (
    SiteGeneratorError,
    generate_site,
)

# Explicit public API definition
__all__ = [
    # Models
    "DigestData",
    "GitHubCommit",
    "GitHubRelease",
    "GitHubRepository",
    "Project",
    "Update",
    "UpdateType",
    # GitHub API
    "GitHubAPIError",
    "fetch_commits_since",
    "fetch_latest_release",
    "fetch_subscriptions",
    # AI Summarization
    "GeminiAPIError",
    "configure_gemini",
    "summarize_commits",
    "summarize_release",
    "summarize_text",
    # Data Management
    "DataManagerError",
    "add_or_update_project",
    "add_update_to_project",
    "find_project",
    "load_digest_data",
    "save_digest_data",
    "update_last_run_timestamp",
    # Site Generation
    "SiteGeneratorError",
    "generate_site",
]
