#!/usr/bin/env python3
"""
Test script to verify Gemini API configuration.

This script helps diagnose issues with Gemini AI summarization by:
1. Checking if GEMINI_API_KEY is set
2. Testing the API connection
3. Generating a simple test summary

Environment variables required:
- GEMINI_API_KEY: Google Gemini API key

Usage:
    export GEMINI_API_KEY='your_api_key_here'
    python test_gemini.py
"""

import asyncio
import os
import sys


async def test_gemini() -> int:
    """Test Gemini API configuration."""
    print("=" * 70)
    print("Gemini API Configuration Test")
    print("=" * 70)

    # Check environment variable
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("\n❌ ERROR: GEMINI_API_KEY environment variable not set")
        print("\nPlease set your Gemini API key:")
        print("  export GEMINI_API_KEY='your_api_key_here'")
        print("\nGet your API key at: https://makersuite.google.com/app/apikey")
        return 1

    print(f"\n✓ GEMINI_API_KEY is set (length: {len(api_key)} chars)")

    # Test import
    print("\nTesting imports...")
    try:
        from core import configure_gemini, summarize_text

        print("✓ Successfully imported core modules")
    except ImportError as e:
        print(f"❌ Failed to import modules: {e}")
        print("\nMake sure to install dependencies:")
        print("  pip install -r requirements.txt")
        return 1

    # Configure Gemini
    print("\nConfiguring Gemini API...")
    try:
        configure_gemini(api_key)
        print("✓ Gemini API configured")
    except Exception as e:
        print(f"❌ Failed to configure Gemini: {e}")
        return 1

    # Test summarization
    print("\nTesting summarization...")
    test_text = """
    Release v2.5.0

    This release includes several new features and bug fixes:

    New Features:
    - Added support for dark mode
    - Implemented user authentication
    - Added export functionality

    Bug Fixes:
    - Fixed memory leak in data processing
    - Corrected timezone handling
    - Resolved CSS rendering issues

    Breaking Changes:
    - Removed deprecated API endpoints
    - Updated configuration format
    """

    try:
        print("Generating summary (this may take a few seconds)...")
        summary = await summarize_text(test_text)

        if summary:
            print("\n" + "=" * 70)
            print("✅ SUCCESS! Summary generated:")
            print("=" * 70)
            print(summary)
            print("=" * 70)
            print("\n✓ Gemini API is working correctly!")
            return 0
        else:
            print("\n❌ ERROR: Gemini returned empty summary")
            print("\nPossible causes:")
            print("  1. API key may not be valid")
            print("  2. API quota may be exhausted")
            print("  3. API service may be unavailable")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: Failed to generate summary")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull error details:")
        import traceback

        traceback.print_exc()

        print("\n" + "=" * 70)
        print("Troubleshooting:")
        print("=" * 70)
        print("1. Verify your API key at: https://makersuite.google.com/app/apikey")
        print("2. Check your API quota and limits")
        print("3. Ensure you have network connectivity")
        print("4. Try regenerating your API key if the issue persists")

        return 1


async def main() -> int:
    """Main entry point."""
    return await test_gemini()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
