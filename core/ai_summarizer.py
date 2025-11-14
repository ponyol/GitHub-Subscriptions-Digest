"""
AI-powered text summarization using Google Gemini API.

This module provides async functions for generating summaries of GitHub release
notes and commit messages using the Google Gemini generative AI model.
"""

import logging
from typing import Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)

# Prompt template for Gemini API
SUMMARIZATION_PROMPT = """
Summarize the following text and translate the summary into Russian.
The summary should be concise (2-4 sentences) and capture the key changes or features.

Original text:
{text}

Provide only the Russian summary, without any additional commentary or formatting.
"""


class GeminiAPIError(Exception):
    """Raised when the Gemini API returns an error response."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f"Gemini API error: {message}")


def configure_gemini(api_key: str) -> None:
    """
    Configure the Gemini API with the provided API key.

    This function must be called once before using any summarization functions.

    Args:
        api_key: Google Gemini API key.
    """
    genai.configure(api_key=api_key)
    logger.info(
        "Gemini API configured",
        extra={"context": "ai_summarizer", "operation": "configure"},
    )


async def summarize_text(text: str, model_name: str = "gemini-1.5-flash") -> Optional[str]:
    """
    Generate a Russian summary of the provided text using Gemini AI.

    Args:
        text: The text to summarize (release notes or commit messages).
        model_name: The Gemini model to use (default: gemini-1.5-flash).

    Returns:
        Russian summary of the text, or None if summarization fails.

    Raises:
        GeminiAPIError: If the API request fails.

    NOTE: This function uses the synchronous Gemini API client, but is defined
    as async to maintain consistency with the rest of the codebase. Future
    versions may use an async client if one becomes available.
    """
    if not text or text.strip() == "":
        logger.warning(
            "Empty text provided for summarization",
            extra={"context": "ai_summarizer"},
        )
        return None

    logger.debug(
        "Starting text summarization",
        extra={
            "context": "ai_summarizer",
            "text_length": len(text),
            "model": model_name,
        },
    )

    try:
        model = genai.GenerativeModel(model_name)
        prompt = SUMMARIZATION_PROMPT.format(text=text)

        # NOTE: The Gemini Python SDK does not currently support async operations.
        # This is a blocking call, but we wrap it in an async function for API
        # consistency. Consider using asyncio.to_thread() if this becomes a bottleneck.
        response = model.generate_content(prompt)

        if not response or not response.text:
            logger.warning(
                "Gemini API returned empty response",
                extra={"context": "ai_summarizer", "model": model_name},
            )
            return None

        summary = response.text.strip()

        logger.info(
            "Successfully generated summary",
            extra={
                "context": "ai_summarizer",
                "model": model_name,
                "summary_length": len(summary),
            },
        )

        return summary

    except Exception as e:
        logger.error(
            "Failed to generate summary",
            extra={
                "context": "ai_summarizer",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise GeminiAPIError(f"Failed to generate summary: {str(e)}") from e


async def summarize_release(release_body: str) -> Optional[str]:
    """
    Generate a Russian summary of a GitHub release's body text.

    Args:
        release_body: The release notes text.

    Returns:
        Russian summary of the release notes, or None if summarization fails.

    Raises:
        GeminiAPIError: If the API request fails.
    """
    logger.debug(
        "Summarizing release notes",
        extra={"context": "ai_summarizer", "operation": "summarize_release"},
    )
    return await summarize_text(release_body)


async def summarize_commits(commit_messages: list[str]) -> Optional[str]:
    """
    Generate a Russian summary of a batch of commit messages.

    Args:
        commit_messages: List of commit message strings.

    Returns:
        Russian summary of the commits, or None if summarization fails.

    Raises:
        GeminiAPIError: If the API request fails.
    """
    if not commit_messages:
        logger.warning(
            "Empty commit messages list provided",
            extra={"context": "ai_summarizer", "operation": "summarize_commits"},
        )
        return None

    # Concatenate all commit messages with separators
    combined_text = "\n\n".join(f"- {msg}" for msg in commit_messages)

    logger.debug(
        "Summarizing commit batch",
        extra={
            "context": "ai_summarizer",
            "operation": "summarize_commits",
            "commits_count": len(commit_messages),
        },
    )

    return await summarize_text(combined_text)
