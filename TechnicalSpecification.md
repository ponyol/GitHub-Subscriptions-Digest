# Technical Specification: GitHub Subscriptions Digest

## 1. Project Overview

  * **Project Name:** GitHub Subscriptions Digest
  * **Objective:** To create a static website that automatically aggregates, summarizes (via AI), and displays the latest updates (releases and commits) from repositories the user is watching (`/user/subscriptions`).
  * **End Product:** A public GitHub repository that, on a daily schedule, updates a set of static HTML pages (hosted on GitHub Pages) containing the digested updates.

## 2. Core Architecture

This project is implemented using a serverless paradigm, leveraging GitHub's native CI/CD and hosting capabilities.

  * **Runner:** GitHub Actions
  * **Logic:** Python 3.x
  * **Data Storage:** A single `digest_data.json` file committed to the `gh-pages` branch.
  * **Site Generator:** Python script utilizing the Jinja2 templating engine.
  * **Hosting:** GitHub Pages (from the `gh-pages` branch).
  * **AI / Summarization:** Google Gemini API.

## 3. Data Structure

The central component of the system is the `digest_data.json` file, which serves as the persistent database for all fetched updates.

**Schema for `digest_data.json`:**

```json
{
  "last_run_timestamp": "2025-11-14T10:00:05Z",
  "projects": [
    {
      "name": "owner/repo-name",
      "url": "https://github.com/owner/repo-name",
      "last_checked": "2025-11-14T10:00:00Z",
      "updates": [
        {
          "id": "update-uuid-123",
          "type": "release",
          "date": "2025-11-14T09:30:00Z",
          "title": "v1.2.0 Release",
          "summary_ru": "Краткое обобщение на русском от Gemini...",
          "source_content": "Original text of the release notes...",
          "source_url": "https://github.com/owner/repo-name/releases/v1.2.0"
        },
        {
          "id": "update-uuid-456",
          "type": "commit_batch",
          "date": "2025-11-13T15:00:00Z",
          "title": "Updates in main (3 commits)",
          "summary_ru": "Обобщение коммитов: исправлены баги, добавлена функция...",
          "source_content": "Commit 1: Fix typo...\nCommit 2: Add feature X...",
          "source_url": "https://github.com/owner/repo-name/commits/main"
        }
      ]
    }
  ]
}
```

## 4. Process Flow

### 4.1. Daily Workflow (GitHub Action)

1.  **Trigger:** Scheduled (`cron`) to run once daily (e.g., 05:00 UTC).
2.  **Checkout:** The workflow checks out both the `main` branch (to get the scripts) and the `gh-pages` branch (to get the `digest_data.json`).
3.  **Setup:** Install Python 3.x and dependencies from `requirements.txt` (e.g., `requests`, `Jinja2`, `google-generativeai`).
4.  **Data Ingestion:** The main Python script reads `digest_data.json` from the `gh-pages` checkout to load the current state.
5.  **Fetch Subscriptions:** The script uses the `GITHUB_TOKEN` to call `GET /user/subscriptions` and retrieve the list of all watched repositories.
6.  **ETL & AI Processing Loop:** For each repository in the subscription list:
    a. **Check for Releases:** Fetch the latest release (`GET /repos/{owner}/{repo}/releases/latest`).
    b. If the release `published_at` date is newer than the project's `last_checked` date in the JSON:
    i. Get the release notes (`body`).
    ii. Send the `body` text to the Gemini API with a prompt: "Summarize this text and translate the summary to Russian."
    iii. Create a new `update` object (type: `release`) and add it to the project's `updates` list in the JSON.
    c. **Check for Commits:** If no *new* release was found, check for commits in the `main` branch since the *global* `last_run_timestamp` (`GET /repos/{owner}/{repo}/commits?sha=main&since={last_run_timestamp}`).
    d. If new commits are found:
    i. Concatenate all unique commit messages into a single text block.
    ii. Send this block to the Gemini API with the same prompt.
    iii. Create a new `update` object (type: `commit_batch`) and add it to the project's `updates` list.
    e. Update the project's `last_checked` timestamp.
7.  **Update Global Timestamp:** After the loop, update the global `last_run_timestamp` in the JSON.
8.  **Static Site Generation (SSG):**
    a. The script uses Jinja2 templates and the *updated* `digest_data.json` to generate the static site.
    b. **`index.html` (Main Page):** Generates a list of all projects, sorted by the date of their most recent update. Each entry links to the project page and the specific update summary. Format: `[Project Name (link)] - [Date] - [summary_ru (link)]`.
    c. **`project/{name}.html` (Project Page):** Generates a page for each project, listing *all* historical `summary_ru` entries for that project, sorted by date.
    d. **`update/{id}.html` (Update Page):** Generates a detail page for each update, displaying the raw, original `source_content`.
    e. All generated files are placed in a build directory (e.g., `_site`).
9.  **Deployment:** The workflow commits and pushes the updated `digest_data.json` and all generated HTML/CSS files from the build directory to the `gh-pages` branch, publishing the site.

### 4.2. Initial Data Seeding (Local Script)

A separate, one-time script (`seed_data.py`) will be run *locally* by the user to populate the initial database.

1.  This script reads the GitHub PAT and Gemini API Key from local environment variables.
2.  It iterates through *all* user subscriptions.
3.  For each project, it fetches *only the single latest* release OR the *single latest* commit.
4.  **It does NOT call the Gemini API.**
5.  It generates the initial `digest_data.json` file, populating `source_content` but leaving `summary_ru` as `null` or an empty string.
6.  This file must be manually pushed to the `gh-pages` branch before the GitHub Action is enabled.

## 5. Frontend

  * **Theme:** "Linux Terminal".
  * **Color Palette:** Dark background (e.g., `#1e1e1e`), light text (e.g., `#d4d4d4`), and a green accent for links and headers (e.g., `#00a000`).
  * **Fonts:** All text will use a monospace font stack (e.g., `Consolas, 'Menlo', 'monospace'`).
  * **Frameworks:** None. The site will be static HTML and a single `style.css` file.

## 6. Secrets & Configuration

The following secrets must be configured in the GitHub repository settings (`Settings > Secrets and variables > Actions`):

1.  `GH_PAT`: A GitHub Personal Access Token with `repo` scope (required for reading subscription lists and private repositories, if any).
2.  `GEMINI_API_KEY`: The API key for the Google Gemini API.
