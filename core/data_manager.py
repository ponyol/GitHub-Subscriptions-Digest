"""
Data persistence manager for digest_data.json.

This module provides pure functions for loading, manipulating, and saving
the digest data structure. All functions are side-effect-free except for
file I/O operations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import DigestData, Project, Update

logger = logging.getLogger(__name__)


class DataManagerError(Exception):
    """Raised when data persistence operations fail."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f"Data manager error: {message}")


def load_digest_data(file_path: Path) -> DigestData:
    """
    Load digest data from a JSON file.

    Args:
        file_path: Path to the digest_data.json file.

    Returns:
        DigestData object loaded from the file.

    Raises:
        DataManagerError: If the file cannot be read or parsed.

    NOTE: If the file does not exist, this function returns a new, empty
    DigestData object with the current timestamp.
    """
    logger.debug(
        "Loading digest data",
        extra={"context": "data_manager", "file_path": str(file_path)},
    )

    if not file_path.exists():
        logger.info(
            "Digest data file not found, creating new empty data",
            extra={"context": "data_manager", "file_path": str(file_path)},
        )
        return DigestData(last_run_timestamp=datetime.now(), projects=[])

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        digest_data = DigestData.model_validate(data)

        logger.info(
            "Successfully loaded digest data",
            extra={
                "context": "data_manager",
                "file_path": str(file_path),
                "projects_count": len(digest_data.projects),
                "last_run": digest_data.last_run_timestamp.isoformat(),
            },
        )

        return digest_data

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse digest data JSON",
            extra={
                "context": "data_manager",
                "file_path": str(file_path),
                "error": str(e),
            },
        )
        raise DataManagerError(f"Invalid JSON in {file_path}: {str(e)}") from e
    except Exception as e:
        logger.error(
            "Failed to load digest data",
            extra={
                "context": "data_manager",
                "file_path": str(file_path),
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise DataManagerError(f"Failed to load {file_path}: {str(e)}") from e


def save_digest_data(digest_data: DigestData, file_path: Path) -> None:
    """
    Save digest data to a JSON file.

    Args:
        digest_data: DigestData object to save.
        file_path: Path to the output JSON file.

    Raises:
        DataManagerError: If the file cannot be written.
    """
    logger.debug(
        "Saving digest data",
        extra={
            "context": "data_manager",
            "file_path": str(file_path),
            "projects_count": len(digest_data.projects),
        },
    )

    try:
        # Ensure the parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict with proper datetime serialization
        data_dict = digest_data.model_dump(mode="json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)

        logger.info(
            "Successfully saved digest data",
            extra={
                "context": "data_manager",
                "file_path": str(file_path),
                "projects_count": len(digest_data.projects),
            },
        )

    except Exception as e:
        logger.error(
            "Failed to save digest data",
            extra={
                "context": "data_manager",
                "file_path": str(file_path),
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise DataManagerError(f"Failed to save {file_path}: {str(e)}") from e


def find_project(digest_data: DigestData, repo_name: str) -> Optional[Project]:
    """
    Find a project in the digest data by repository name.

    Args:
        digest_data: DigestData object to search.
        repo_name: Repository name in 'owner/repo' format.

    Returns:
        Project object if found, None otherwise.
    """
    for project in digest_data.projects:
        if project.name == repo_name:
            return project
    return None


def add_or_update_project(
    digest_data: DigestData,
    repo_name: str,
    repo_url: str,
    last_checked: datetime,
) -> DigestData:
    """
    Add a new project or update an existing one's last_checked timestamp.

    This function is pure and returns a new DigestData object with the
    project added or updated. The original object is not modified.

    Args:
        digest_data: Original DigestData object.
        repo_name: Repository name in 'owner/repo' format.
        repo_url: Full URL to the repository.
        last_checked: Timestamp of the check.

    Returns:
        New DigestData object with the project added or updated.
    """
    existing_project = find_project(digest_data, repo_name)

    if existing_project:
        # Update existing project's last_checked
        updated_projects = [
            (
                Project(
                    name=p.name,
                    url=p.url,
                    last_checked=last_checked,
                    updates=p.updates,
                )
                if p.name == repo_name
                else p
            )
            for p in digest_data.projects
        ]
    else:
        # Add new project
        new_project = Project(
            name=repo_name,
            url=repo_url,
            last_checked=last_checked,
            updates=[],
        )
        updated_projects = digest_data.projects + [new_project]

    return DigestData(
        last_run_timestamp=digest_data.last_run_timestamp,
        projects=updated_projects,
    )


def add_update_to_project(
    digest_data: DigestData,
    repo_name: str,
    update: Update,
) -> DigestData:
    """
    Add a new update to a project's update list.

    This function is pure and returns a new DigestData object with the
    update added. The original object is not modified.

    Args:
        digest_data: Original DigestData object.
        repo_name: Repository name in 'owner/repo' format.
        update: Update object to add.

    Returns:
        New DigestData object with the update added.

    Raises:
        DataManagerError: If the project is not found.
    """
    project = find_project(digest_data, repo_name)
    if not project:
        raise DataManagerError(f"Project '{repo_name}' not found in digest data")

    # Create updated projects list with the new update added
    updated_projects = [
        (
            Project(
                name=p.name,
                url=p.url,
                last_checked=p.last_checked,
                updates=p.updates + [update],
            )
            if p.name == repo_name
            else p
        )
        for p in digest_data.projects
    ]

    return DigestData(
        last_run_timestamp=digest_data.last_run_timestamp,
        projects=updated_projects,
    )


def update_last_run_timestamp(
    digest_data: DigestData, timestamp: datetime
) -> DigestData:
    """
    Update the global last_run_timestamp.

    This function is pure and returns a new DigestData object.

    Args:
        digest_data: Original DigestData object.
        timestamp: New timestamp to set.

    Returns:
        New DigestData object with updated timestamp.
    """
    return DigestData(
        last_run_timestamp=timestamp,
        projects=digest_data.projects,
    )
