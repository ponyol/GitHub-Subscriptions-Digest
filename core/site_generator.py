"""
Static site generator for the GitHub Subscriptions Digest.

This module uses Jinja2 templates to generate HTML pages from the digest data.
All functions are pure (except for file I/O) and follow a functional programming style.
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import DigestData, Project, Update

logger = logging.getLogger(__name__)


class SiteGeneratorError(Exception):
    """Raised when site generation operations fail."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f"Site generator error: {message}")


def create_jinja_env(templates_dir: Path) -> Environment:
    """
    Create and configure a Jinja2 environment.

    Args:
        templates_dir: Path to the templates directory.

    Returns:
        Configured Jinja2 Environment object.
    """
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Add custom filters
    env.filters["isoformat"] = lambda dt: dt.isoformat() if dt else ""
    env.filters["format_date"] = lambda dt: dt.strftime("%Y-%m-%d %H:%M UTC") if dt else ""

    logger.debug(
        "Created Jinja2 environment",
        extra={"context": "site_generator", "templates_dir": str(templates_dir)},
    )

    return env


def get_sorted_projects(digest_data: DigestData) -> list[Project]:
    """
    Get all projects sorted by the date of their most recent update.

    Projects with no updates are placed at the end.

    Args:
        digest_data: DigestData object containing all projects.

    Returns:
        List of Project objects sorted by most recent update date (descending).
    """

    def get_latest_update_date(project: Project) -> float:
        """Helper function to get the timestamp of the latest update."""
        if not project.updates:
            return 0.0  # Projects with no updates go to the end
        latest_update = max(project.updates, key=lambda u: u.date)
        return latest_update.date.timestamp()

    return sorted(digest_data.projects, key=get_latest_update_date, reverse=True)


def generate_index_page(
    digest_data: DigestData, env: Environment, output_dir: Path
) -> None:
    """
    Generate the main index.html page.

    The page lists all projects sorted by their most recent update, with
    each entry showing the project name, date, and a link to the summary.

    Args:
        digest_data: DigestData object containing all projects.
        env: Configured Jinja2 Environment.
        output_dir: Path to the output directory for generated files.

    Raises:
        SiteGeneratorError: If the template cannot be rendered or file cannot be written.
    """
    logger.info(
        "Generating index page",
        extra={"context": "site_generator", "operation": "generate_index_page"},
    )

    try:
        template = env.get_template("index.html")
        sorted_projects = get_sorted_projects(digest_data)

        # Prepare data for the template
        # Each project needs its latest update for display
        projects_with_latest = []
        for project in sorted_projects:
            latest_update = None
            if project.updates:
                latest_update = max(project.updates, key=lambda u: u.date)

            projects_with_latest.append(
                {
                    "project": project,
                    "latest_update": latest_update,
                }
            )

        html = template.render(
            projects=projects_with_latest,
            last_run=digest_data.last_run_timestamp,
            css_path="static/style.css",
        )

        output_file = output_dir / "index.html"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(
            "Successfully generated index page",
            extra={
                "context": "site_generator",
                "output_file": str(output_file),
                "projects_count": len(sorted_projects),
            },
        )

    except Exception as e:
        logger.error(
            "Failed to generate index page",
            extra={
                "context": "site_generator",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise SiteGeneratorError(f"Failed to generate index page: {str(e)}") from e


def generate_project_page(
    project: Project, env: Environment, output_dir: Path
) -> None:
    """
    Generate a project-specific page showing all historical updates.

    Args:
        project: Project object to generate a page for.
        env: Configured Jinja2 Environment.
        output_dir: Path to the output directory for generated files.

    Raises:
        SiteGeneratorError: If the template cannot be rendered or file cannot be written.
    """
    logger.debug(
        "Generating project page",
        extra={"context": "site_generator", "project_name": project.name},
    )

    try:
        template = env.get_template("project.html")

        # Sort updates by date (most recent first)
        sorted_updates = sorted(project.updates, key=lambda u: u.date, reverse=True)

        html = template.render(
            project=project,
            updates=sorted_updates,
            css_path="../static/style.css",
        )

        # Create output path: project/{owner}_{repo}.html
        # Replace '/' with '_' to avoid filesystem issues
        safe_name = project.name.replace("/", "_")
        output_file = output_dir / "project" / f"{safe_name}.html"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        logger.debug(
            "Successfully generated project page",
            extra={
                "context": "site_generator",
                "project_name": project.name,
                "output_file": str(output_file),
                "updates_count": len(sorted_updates),
            },
        )

    except Exception as e:
        logger.error(
            "Failed to generate project page",
            extra={
                "context": "site_generator",
                "project_name": project.name,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise SiteGeneratorError(
            f"Failed to generate project page for {project.name}: {str(e)}"
        ) from e


def generate_update_page(
    update: Update, project_name: str, env: Environment, output_dir: Path
) -> None:
    """
    Generate a detail page for a single update showing the source content.

    Args:
        update: Update object to generate a page for.
        project_name: Name of the project (for context in the page).
        env: Configured Jinja2 Environment.
        output_dir: Path to the output directory for generated files.

    Raises:
        SiteGeneratorError: If the template cannot be rendered or file cannot be written.
    """
    logger.debug(
        "Generating update page",
        extra={
            "context": "site_generator",
            "update_id": update.id,
            "project_name": project_name,
        },
    )

    try:
        template = env.get_template("update.html")

        html = template.render(
            update=update,
            project_name=project_name,
            css_path="../static/style.css",
        )

        output_file = output_dir / "update" / f"{update.id}.html"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        logger.debug(
            "Successfully generated update page",
            extra={
                "context": "site_generator",
                "update_id": update.id,
                "output_file": str(output_file),
            },
        )

    except Exception as e:
        logger.error(
            "Failed to generate update page",
            extra={
                "context": "site_generator",
                "update_id": update.id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise SiteGeneratorError(
            f"Failed to generate update page for {update.id}: {str(e)}"
        ) from e


def copy_static_files(static_dir: Path, output_dir: Path) -> None:
    """
    Copy all static files (CSS, etc.) to the output directory.

    Args:
        static_dir: Path to the static files directory.
        output_dir: Path to the output directory.

    Raises:
        SiteGeneratorError: If files cannot be copied.
    """
    logger.debug(
        "Copying static files",
        extra={
            "context": "site_generator",
            "static_dir": str(static_dir),
            "output_dir": str(output_dir),
        },
    )

    try:
        import shutil

        output_static_dir = output_dir / "static"
        if output_static_dir.exists():
            shutil.rmtree(output_static_dir)

        shutil.copytree(static_dir, output_static_dir)

        logger.info(
            "Successfully copied static files",
            extra={
                "context": "site_generator",
                "static_dir": str(static_dir),
                "output_dir": str(output_static_dir),
            },
        )

    except Exception as e:
        logger.error(
            "Failed to copy static files",
            extra={
                "context": "site_generator",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise SiteGeneratorError(f"Failed to copy static files: {str(e)}") from e


def generate_site(
    digest_data: DigestData,
    templates_dir: Path,
    static_dir: Path,
    output_dir: Path,
) -> None:
    """
    Generate the complete static site.

    This is the main entry point for site generation. It creates all HTML
    pages and copies static assets.

    Args:
        digest_data: DigestData object containing all projects and updates.
        templates_dir: Path to the Jinja2 templates directory.
        static_dir: Path to the static files directory.
        output_dir: Path to the output directory for generated files.

    Raises:
        SiteGeneratorError: If site generation fails.
    """
    logger.info(
        "Starting site generation",
        extra={
            "context": "site_generator",
            "operation": "generate_site",
            "projects_count": len(digest_data.projects),
            "output_dir": str(output_dir),
        },
    )

    try:
        env = create_jinja_env(templates_dir)

        # Generate index page
        generate_index_page(digest_data, env, output_dir)

        # Generate project and update pages
        for project in digest_data.projects:
            generate_project_page(project, env, output_dir)

            for update in project.updates:
                generate_update_page(update, project.name, env, output_dir)

        # Copy static files
        copy_static_files(static_dir, output_dir)

        logger.info(
            "Successfully generated complete site",
            extra={
                "context": "site_generator",
                "operation": "generate_site",
                "output_dir": str(output_dir),
            },
        )

    except Exception as e:
        logger.error(
            "Failed to generate site",
            extra={
                "context": "site_generator",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise SiteGeneratorError(f"Site generation failed: {str(e)}") from e
