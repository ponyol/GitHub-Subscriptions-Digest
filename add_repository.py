#!/usr/bin/env python3
"""
Utility script to manually add a repository to digest_data.json.

This is useful when the GitHub API doesn't return all watched repositories
or when you want to track a repository without watching it on GitHub.

Environment variables required:
- GH_PAT: GitHub Personal Access Token

Usage:
    python add_repository.py owner/repo
    python add_repository.py coinbase/x402
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

from core import (
    add_or_update_project,
    fetch_latest_release,
    load_digest_data,
    save_digest_data,
)


async def add_repository(repo_full_name: str, github_token: str) -> bool:
    """
    Add a repository to the digest data.

    Args:
        repo_full_name: Repository name in 'owner/repo' format.
        github_token: GitHub Personal Access Token.

    Returns:
        True if successful, False otherwise.
    """
    try:
        owner, repo = repo_full_name.split("/")
    except ValueError:
        print(f"ERROR: Invalid repository format: {repo_full_name}")
        print("Expected format: owner/repo (e.g., coinbase/x402)")
        return False

    print(f"Adding repository: {repo_full_name}")
    print("-" * 60)

    # Check if repository exists on GitHub
    print("Verifying repository exists on GitHub...")
    try:
        release = await fetch_latest_release(github_token, owner, repo)
        if release:
            print(f"✓ Repository exists (found release: {release.tag_name})")
        else:
            print("✓ Repository exists (no releases found)")
    except Exception as e:
        print(f"✗ Error accessing repository: {e}")
        print("  Make sure:")
        print("  1. The repository exists")
        print("  2. Your GH_PAT has access to it (for private repos)")
        print("  3. The format is correct (owner/repo)")
        return False

    # Load digest data
    data_file = Path("digest_data.json")
    print(f"\nLoading digest data from {data_file}...")

    try:
        digest_data = load_digest_data(data_file)
        print(f"✓ Loaded digest data ({len(digest_data.projects)} existing projects)")
    except Exception as e:
        print(f"✗ Error loading digest data: {e}")
        return False

    # Check if already exists
    existing = any(p.name == repo_full_name for p in digest_data.projects)
    if existing:
        print(f"\n⚠ WARNING: Repository {repo_full_name} already exists in digest!")
        response = input("Update last_checked timestamp? [y/N]: ")
        if response.lower() != "y":
            print("Cancelled.")
            return False

    # Add or update project
    print(f"\n{'Updating' if existing else 'Adding'} project...")
    repo_url = f"https://github.com/{repo_full_name}"
    current_time = datetime.now()

    digest_data = add_or_update_project(
        digest_data,
        repo_name=repo_full_name,
        repo_url=repo_url,
        last_checked=current_time,
    )

    # Save digest data
    print(f"Saving to {data_file}...")
    try:
        save_digest_data(digest_data, data_file)
        print("✓ Successfully saved!")
    except Exception as e:
        print(f"✗ Error saving digest data: {e}")
        return False

    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"Repository {repo_full_name} has been added to the digest.")
    print("\nNext steps:")
    print("1. Commit and push digest_data.json to the gh-pages branch:")
    print("   git add digest_data.json")
    print("   git commit -m 'Add repository: {}'".format(repo_full_name))
    print("   git push")
    print("2. Wait for the next scheduled run, or trigger the workflow manually")
    print("\nDone!")

    return True


async def main() -> int:
    """Main entry point."""
    import os

    print("=" * 60)
    print("Add Repository to Digest")
    print("=" * 60)

    # Check arguments
    if len(sys.argv) < 2:
        print("\nUsage: python add_repository.py owner/repo")
        print("\nExample:")
        print("  python add_repository.py coinbase/x402")
        print("\nYou can also add multiple repositories:")
        print("  python add_repository.py owner1/repo1 owner2/repo2")
        return 1

    # Get GitHub token
    github_token = os.getenv("GH_PAT")
    if not github_token:
        print("\nERROR: GH_PAT environment variable not set")
        print("Please set your GitHub Personal Access Token:")
        print("  export GH_PAT='your_token_here'")
        return 1

    # Process each repository
    repos_to_add = sys.argv[1:]
    success_count = 0

    for repo_full_name in repos_to_add:
        print("\n")
        success = await add_repository(repo_full_name, github_token)
        if success:
            success_count += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"Added {success_count} out of {len(repos_to_add)} repositories")
    print("=" * 60)

    return 0 if success_count == len(repos_to_add) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
