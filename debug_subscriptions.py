#!/usr/bin/env python3
"""
Debug script to check GitHub subscriptions.

This script helps debug issues with missing repositories by:
1. Fetching all subscriptions from GitHub API
2. Displaying detailed information about each repository
3. Checking if a specific repository is in the list

Environment variables required:
- GH_PAT: GitHub Personal Access Token
"""

import asyncio
import os
import sys

from core import fetch_subscriptions


async def main() -> int:
    """Main entry point for the debug script."""
    print("=" * 70)
    print("GitHub Subscriptions Debug Tool")
    print("=" * 70)

    # Get GitHub token from environment
    github_token = os.getenv("GH_PAT")

    if not github_token:
        print("ERROR: GH_PAT environment variable not set")
        print("Please set your GitHub Personal Access Token:")
        print("  export GH_PAT='your_token_here'")
        return 1

    # Fetch subscriptions
    print("\nFetching subscriptions from GitHub API...")
    try:
        repos = await fetch_subscriptions(github_token)
        print(f"✓ Successfully fetched {len(repos)} repositories\n")
    except Exception as e:
        print(f"✗ Error fetching subscriptions: {e}")
        return 1

    # Display all repositories
    print("=" * 70)
    print("All Subscriptions:")
    print("=" * 70)
    for i, repo in enumerate(repos, 1):
        print(f"{i:3d}. {repo.full_name}")
        print(f"     URL: {repo.html_url}")
        print(f"     Default branch: {repo.default_branch}")
        print()

    # Check for specific repository
    print("=" * 70)
    print("Checking for specific repositories:")
    print("=" * 70)

    test_repos = ["coinbase/x402"]
    for test_repo in test_repos:
        found = any(repo.full_name == test_repo for repo in repos)
        status = "✓ FOUND" if found else "✗ NOT FOUND"
        print(f"{status}: {test_repo}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    print(f"Total repositories: {len(repos)}")
    print(f"Unique owners: {len(set(repo.full_name.split('/')[0] for repo in repos))}")

    # Save to file for inspection
    output_file = "subscriptions_debug.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("GitHub Subscriptions List\n")
        f.write("=" * 70 + "\n\n")
        for repo in sorted(repos, key=lambda r: r.full_name.lower()):
            f.write(f"{repo.full_name}\n")
            f.write(f"  URL: {repo.html_url}\n")
            f.write(f"  Default branch: {repo.default_branch}\n\n")

    print(f"\nFull list saved to: {output_file}")
    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
