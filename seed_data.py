#!/usr/bin/env python3
"""
Initial data seeding script for GitHub Subscriptions Digest.

This script is run ONCE locally by the user to populate the initial digest_data.json.
It fetches the latest release OR latest commit from each subscription but does NOT
call the Gemini API (summary_ru remains null).

The generated digest_data.json must be manually pushed to the gh-pages branch
before enabling the GitHub Action.

Environment variables required:
- GH_PAT: GitHub Personal Access Token with 'repo' scope

NOTE: GEMINI_API_KEY is NOT required for this script.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from core import (
    DigestData,
    Update,
    UpdateType,
    add_or_update_project,
    add_update_to_project,
    fetch_commits_since,
    fetch_latest_release,
    fetch_subscriptions,
    save_digest_data,
)


def setup_logging() -> None:
    """
    Configure logging for the seeding script.

    Uses a simpler format than the main script since this runs locally.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )


async def seed_repository(
    repo_name: str,
    repo_url: str,
    default_branch: str,
    github_token: str,
) -> Update | None:
    """
    Fetch the single latest update (release OR commit) for a repository.

    This function does NOT generate AI summaries.

    Args:
        repo_name: Repository name in 'owner/repo' format.
        repo_url: Full URL to the repository.
        default_branch: Default branch name.
        github_token: GitHub Personal Access Token.

    Returns:
        Update object if found, None otherwise.
    """
    logger = logging.getLogger(__name__)
    owner, repo = repo_name.split("/")

    logger.info(f"Seeding repository: {repo_name}")

    # Try to fetch the latest release first
    try:
        release = await fetch_latest_release(github_token, owner, repo)

        if release:
            logger.info(f"  Found release: {release.tag_name}")

            update = Update(
                type=UpdateType.RELEASE,
                date=release.published_at,
                title=release.name or release.tag_name,
                summary_ru=None,  # No AI summary during seeding
                source_content=release.body or "",
                source_url=release.html_url,
            )

            return update

    except Exception as e:
        logger.warning(f"  Failed to fetch release: {e}")

    # If no release found, fetch the single latest commit
    try:
        # Fetch commits from the last 30 days as a reasonable window
        from datetime import timedelta

        thirty_days_ago = datetime.now() - timedelta(days=30)

        commits = await fetch_commits_since(
            github_token, owner, repo, default_branch, thirty_days_ago
        )

        if commits:
            # Take only the most recent commit
            latest_commit = commits[0]
            commit_message = latest_commit.commit["message"]
            commit_date_str = latest_commit.commit["author"]["date"]
            commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))

            logger.info(f"  Found latest commit: {latest_commit.sha[:7]}")

            update = Update(
                type=UpdateType.COMMIT_BATCH,
                date=commit_date,
                title=f"Latest commit in {default_branch}",
                summary_ru=None,  # No AI summary during seeding
                source_content=commit_message,
                source_url=latest_commit.html_url,
            )

            return update

        logger.info(f"  No recent commits found")

    except Exception as e:
        logger.warning(f"  Failed to fetch commits: {e}")

    return None


async def main() -> int:
    """
    Main entry point for the seeding script.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("GitHub Subscriptions Digest - Initial Data Seeding")
    logger.info("=" * 60)

    # Get GitHub token from environment
    github_token = os.getenv("GH_PAT")

    if not github_token:
        logger.error("ERROR: GH_PAT environment variable not set")
        logger.error("Please set your GitHub Personal Access Token:")
        logger.error("  export GH_PAT='your_token_here'")
        return 1

    # Fetch subscriptions
    logger.info("\nFetching your GitHub subscriptions...")

    try:
        repos = await fetch_subscriptions(github_token)
        logger.info(f"Found {len(repos)} subscriptions")
    except Exception as e:
        logger.error(f"Failed to fetch subscriptions: {e}")
        return 1

    # Initialize digest data
    current_time = datetime.now()
    digest_data = DigestData(last_run_timestamp=current_time, projects=[])

    # Process each repository
    logger.info("\nSeeding initial data (this may take a while)...")
    logger.info("NOTE: AI summaries will NOT be generated during seeding.\n")

    successful_seeds = 0
    failed_seeds = 0

    for i, repo in enumerate(repos, 1):
        logger.info(f"[{i}/{len(repos)}] Processing {repo.full_name}")

        try:
            # Add project to digest data
            digest_data = add_or_update_project(
                digest_data,
                repo_name=repo.full_name,
                repo_url=str(repo.html_url),
                last_checked=current_time,
            )

            # Fetch the latest update
            update = await seed_repository(
                repo_name=repo.full_name,
                repo_url=str(repo.html_url),
                default_branch=repo.default_branch,
                github_token=github_token,
            )

            if update:
                digest_data = add_update_to_project(
                    digest_data,
                    repo_name=repo.full_name,
                    update=update,
                )
                successful_seeds += 1
            else:
                logger.info(f"  No updates found for {repo.full_name}")

        except Exception as e:
            logger.error(f"  ERROR processing {repo.full_name}: {e}")
            failed_seeds += 1

    # Save digest data
    output_file = Path("digest_data.json")

    logger.info("\n" + "=" * 60)
    logger.info("Saving digest data...")

    try:
        save_digest_data(digest_data, output_file)
        logger.info(f"Successfully saved to: {output_file.absolute()}")
    except Exception as e:
        logger.error(f"Failed to save digest data: {e}")
        return 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Seeding Summary:")
    logger.info(f"  Total repositories: {len(repos)}")
    logger.info(f"  Successful seeds: {successful_seeds}")
    logger.info(f"  Failed seeds: {failed_seeds}")
    logger.info(f"  Total projects: {len(digest_data.projects)}")
    logger.info("=" * 60)

    logger.info("\nNext steps:")
    logger.info("  1. Review the generated digest_data.json file")
    logger.info("  2. Create a 'gh-pages' branch if it doesn't exist:")
    logger.info("     git checkout --orphan gh-pages")
    logger.info("  3. Copy digest_data.json to the gh-pages branch")
    logger.info("  4. Commit and push:")
    logger.info("     git add digest_data.json")
    logger.info("     git commit -m 'Initial digest data'")
    logger.info("     git push -u origin gh-pages")
    logger.info("  5. Enable GitHub Actions in your repository")
    logger.info("  6. Configure secrets: GH_PAT and GEMINI_API_KEY")
    logger.info("\nDone!")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
