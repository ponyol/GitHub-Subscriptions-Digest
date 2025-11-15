#!/usr/bin/env python3
"""
Main script for the daily GitHub Subscriptions Digest workflow.

This script is designed to run in GitHub Actions and performs the following:
1. Loads existing digest data from gh-pages branch
2. Fetches all user subscriptions from GitHub
3. Checks for new releases and commits
4. Generates AI summaries for new content
5. Updates the digest data
6. Generates the static site
7. Saves everything back to disk for deployment

Environment variables required:
- GH_PAT: GitHub Personal Access Token with 'repo' scope
- GEMINI_API_KEY: Google Gemini API key
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from core import (
    Update,
    UpdateType,
    add_or_update_project,
    add_update_to_project,
    configure_gemini,
    fetch_commits_since,
    fetch_latest_release,
    fetch_subscriptions,
    find_project,
    generate_site,
    load_digest_data,
    save_digest_data,
    summarize_commits,
    summarize_release,
    update_last_run_timestamp,
)


def setup_logging() -> None:
    """
    Configure structured JSON logging for the application.

    All log output is written to stdout in JSON format for easy parsing
    by log aggregation systems.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )


async def process_repository(
    repo_name: str,
    repo_url: str,
    default_branch: str,
    github_token: str,
    last_run_timestamp: datetime,
    last_checked: datetime,
) -> list[Update]:
    """
    Process a single repository to check for new updates.

    Args:
        repo_name: Repository name in 'owner/repo' format.
        repo_url: Full URL to the repository.
        default_branch: Default branch name (usually 'main' or 'master').
        github_token: GitHub Personal Access Token.
        last_run_timestamp: Global timestamp of the last run.
        last_checked: Timestamp when this project was last checked.

    Returns:
        List of new Update objects (may be empty).
    """
    logger = logging.getLogger(__name__)
    new_updates: list[Update] = []

    owner, repo = repo_name.split("/")

    logger.info(
        f"Processing repository: {repo_name}",
        extra={"context": "main", "repo": repo_name},
    )

    # Check for new releases
    try:
        release = await fetch_latest_release(github_token, owner, repo)

        if release and release.published_at > last_checked:
            logger.info(
                f"Found new release: {release.tag_name}",
                extra={
                    "context": "main",
                    "repo": repo_name,
                    "tag": release.tag_name,
                    "published_at": release.published_at.isoformat(),
                },
            )

            # Generate AI summary
            summary_ru = None
            if release.body:
                try:
                    summary_ru = await summarize_release(release.body)
                except Exception as e:
                    logger.warning(
                        f"Failed to generate summary for release {release.tag_name}",
                        extra={
                            "context": "main",
                            "repo": repo_name,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                        exc_info=True,  # Include full traceback
                    )

            # Create update object
            update = Update(
                type=UpdateType.RELEASE,
                date=release.published_at,
                title=release.name or release.tag_name,
                summary_ru=summary_ru,
                source_content=release.body or "",
                source_url=release.html_url,
            )

            new_updates.append(update)
            logger.info(
                f"Added release update: {update.title}",
                extra={"context": "main", "repo": repo_name, "update_id": update.id},
            )

            # If we found a new release, skip checking commits
            return new_updates

    except Exception as e:
        logger.error(
            f"Failed to fetch releases for {repo_name}",
            extra={"context": "main", "repo": repo_name, "error": str(e)},
        )

    # Check for new commits (only if no new release was found)
    try:
        commits = await fetch_commits_since(
            github_token, owner, repo, default_branch, last_run_timestamp
        )

        if commits:
            logger.info(
                f"Found {len(commits)} new commits",
                extra={"context": "main", "repo": repo_name, "commits_count": len(commits)},
            )

            # Extract commit messages
            commit_messages = [commit.commit["message"] for commit in commits]

            # Generate AI summary
            summary_ru = None
            try:
                summary_ru = await summarize_commits(commit_messages)
            except Exception as e:
                logger.warning(
                    f"Failed to generate summary for commits",
                    extra={
                        "context": "main",
                        "repo": repo_name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,  # Include full traceback
                )

            # Use the most recent commit's date
            latest_commit_date = max(
                datetime.fromisoformat(commit.commit["author"]["date"].replace("Z", "+00:00"))
                for commit in commits
            )

            # Create update object
            update = Update(
                type=UpdateType.COMMIT_BATCH,
                date=latest_commit_date,
                title=f"Updates in {default_branch} ({len(commits)} commits)",
                summary_ru=summary_ru,
                source_content="\n\n".join(f"- {msg}" for msg in commit_messages),
                source_url=f"https://github.com/{repo_name}/commits/{default_branch}",
            )

            new_updates.append(update)
            logger.info(
                f"Added commit batch update: {update.title}",
                extra={"context": "main", "repo": repo_name, "update_id": update.id},
            )

    except Exception as e:
        logger.error(
            f"Failed to fetch commits for {repo_name}",
            extra={"context": "main", "repo": repo_name, "error": str(e)},
        )

    return new_updates


async def main() -> int:
    """
    Main entry point for the daily digest workflow.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting daily digest workflow", extra={"context": "main"})

    # Get environment variables
    github_token = os.getenv("GH_PAT")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not github_token:
        logger.error("GH_PAT environment variable not set", extra={"context": "main"})
        return 1

    if not gemini_api_key:
        logger.error(
            "GEMINI_API_KEY environment variable not set", extra={"context": "main"}
        )
        return 1

    # Configure Gemini API
    configure_gemini(gemini_api_key)

    # Paths
    data_file = Path("digest_data.json")
    templates_dir = Path("templates")
    static_dir = Path("static")
    output_dir = Path("_site")

    # Load existing digest data
    try:
        digest_data = load_digest_data(data_file)
        logger.info(
            "Loaded existing digest data",
            extra={
                "context": "main",
                "projects_count": len(digest_data.projects),
                "last_run": digest_data.last_run_timestamp.isoformat(),
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to load digest data: {e}",
            extra={"context": "main", "error": str(e)},
        )
        return 1

    # Fetch subscriptions
    try:
        repos = await fetch_subscriptions(github_token)
        logger.info(
            f"Fetched {len(repos)} subscriptions",
            extra={"context": "main", "repos_count": len(repos)},
        )
    except Exception as e:
        logger.error(
            f"Failed to fetch subscriptions: {e}",
            extra={"context": "main", "error": str(e)},
        )
        return 1

    # Process each repository
    current_time = datetime.now()

    for repo in repos:
        # Find or create project in digest data
        project = find_project(digest_data, repo.full_name)
        last_checked = project.last_checked if project else digest_data.last_run_timestamp

        # Process repository for updates
        new_updates = await process_repository(
            repo_name=repo.full_name,
            repo_url=str(repo.html_url),
            default_branch=repo.default_branch,
            github_token=github_token,
            last_run_timestamp=digest_data.last_run_timestamp,
            last_checked=last_checked,
        )

        # Update digest data with new project or timestamp
        digest_data = add_or_update_project(
            digest_data,
            repo_name=repo.full_name,
            repo_url=str(repo.html_url),
            last_checked=current_time,
        )

        # Add new updates to the project
        for update in new_updates:
            digest_data = add_update_to_project(
                digest_data,
                repo_name=repo.full_name,
                update=update,
            )

    # Update global last run timestamp
    digest_data = update_last_run_timestamp(digest_data, current_time)

    # Save updated digest data
    try:
        save_digest_data(digest_data, data_file)
        logger.info(
            "Saved updated digest data",
            extra={"context": "main", "file": str(data_file)},
        )
    except Exception as e:
        logger.error(
            f"Failed to save digest data: {e}",
            extra={"context": "main", "error": str(e)},
        )
        return 1

    # Generate static site
    try:
        generate_site(digest_data, templates_dir, static_dir, output_dir)
        logger.info(
            "Successfully generated static site",
            extra={"context": "main", "output_dir": str(output_dir)},
        )
    except Exception as e:
        logger.error(
            f"Failed to generate static site: {e}",
            extra={"context": "main", "error": str(e)},
        )
        return 1

    logger.info(
        "Daily digest workflow completed successfully",
        extra={"context": "main"},
    )

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
