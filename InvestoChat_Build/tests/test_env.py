#!/usr/bin/env python3
"""
Test suite for validating .env configuration.

Usage:
    python test_env.py              # Run all tests
    python test_env.py --verbose    # Run with detailed output
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional

# Try to load .env or .env.local file
try:
    from dotenv import load_dotenv
    from pathlib import Path

    env_path = Path(__file__).parent / ".env"
    env_local_path = Path(__file__).parent / ".env.local"

    if env_path.exists():
        load_dotenv(env_path)
    elif env_local_path.exists():
        load_dotenv(env_local_path)
except ImportError:
    print("Warning: python-dotenv not installed. Reading environment variables only.")


class EnvValidator:
    """Validates environment configuration for InvestoChat."""

    # Required environment variables
    REQUIRED_VARS = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
    ]

    # Recommended environment variables
    RECOMMENDED_VARS = [
        "DEEPINFRA_API_KEY",
        "CHAT_MODEL",
        "EMBEDDING_MODEL",
    ]

    # Optional environment variables
    OPTIONAL_VARS = [
        "OPENAI_BASE_URL",
        "USE_OCR_SQL",
        "DEBUG_RAG",
        "DEFAULT_PROJECT_ID",
        "WHATSAPP_VERIFY_TOKEN",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
        "API_RATE_LIMIT",
        "WHATSAPP_RATE_LIMIT",
        "RATE_LIMIT_WINDOW",
        "TOP_K",
        "TIMEOUT_S",
        "OLMOCR_ENDPOINT",
        "FLASK_SECRET_KEY",
    ]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []

    def log(self, message: str, level: str = "INFO"):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            prefix = {
                "PASS": "✓",
                "WARN": "⚠",
                "ERROR": "✗",
                "INFO": "ℹ",
            }.get(level, "•")
            print(f"{prefix} {message}")

    def test_env_file_exists(self) -> bool:
        """Test if .env or .env.local file exists."""
        env_path = Path(__file__).parent / ".env"
        env_local_path = Path(__file__).parent / ".env.local"

        if env_path.exists():
            self.log(f".env file found at {env_path}", "PASS")
            self.passed.append("Environment file exists (.env)")
            return True
        elif env_local_path.exists():
            self.log(f".env.local file found at {env_local_path}", "PASS")
            self.passed.append("Environment file exists (.env.local)")
            return True
        else:
            self.errors.append("No .env or .env.local file found")
            self.log("No .env or .env.local file found in InvestoChat_Build/", "ERROR")
            return False

    def test_required_vars(self) -> bool:
        """Test if all required environment variables are set."""
        all_present = True
        for var in self.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Required variable {var} is not set")
                self.log(f"Required variable {var} is not set", "ERROR")
                all_present = False
            else:
                self.passed.append(f"Required variable {var} is set")
                self.log(f"Required variable {var} is set", "PASS")
        return all_present

    def test_database_url_format(self) -> bool:
        """Test if DATABASE_URL has valid PostgreSQL format."""
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return False

        # PostgreSQL connection string pattern
        pattern = r"^postgresql://[^:]+:[^@]+@[^:]+:\d+/\w+$"
        if re.match(pattern, db_url):
            self.passed.append("DATABASE_URL has valid format")
            self.log(f"DATABASE_URL format is valid", "PASS")
            return True
        else:
            self.errors.append(
                "DATABASE_URL format is invalid. "
                "Expected: postgresql://user:password@host:port/database"
            )
            self.log("DATABASE_URL format is invalid", "ERROR")
            return False

    def test_openai_api_key_format(self) -> bool:
        """Test if OPENAI_API_KEY has valid format."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False

        # OpenAI API keys typically start with sk- and have reasonable length
        if api_key.startswith("sk-") and len(api_key) > 20:
            self.passed.append("OPENAI_API_KEY has valid format")
            self.log("OPENAI_API_KEY format appears valid", "PASS")
            return True
        else:
            self.warnings.append(
                "OPENAI_API_KEY format appears invalid. "
                "Should start with 'sk-' and be longer than 20 characters"
            )
            self.log("OPENAI_API_KEY format appears invalid", "WARN")
            return False

    def test_deepinfra_api_key(self) -> bool:
        """Test if DEEPINFRA_API_KEY is set (recommended for OCR)."""
        api_key = os.getenv("DEEPINFRA_API_KEY")
        if not api_key:
            self.warnings.append(
                "DEEPINFRA_API_KEY is not set. OCR processing (process_pdf.py) will not work."
            )
            self.log("DEEPINFRA_API_KEY is not set (recommended for OCR)", "WARN")
            return False
        else:
            if len(api_key) > 10:
                self.passed.append("DEEPINFRA_API_KEY is set")
                self.log("DEEPINFRA_API_KEY is set", "PASS")
                return True
            else:
                self.warnings.append("DEEPINFRA_API_KEY appears too short")
                self.log("DEEPINFRA_API_KEY appears too short", "WARN")
                return False

    def test_recommended_vars(self) -> bool:
        """Test if recommended environment variables are set."""
        all_present = True
        for var in self.RECOMMENDED_VARS:
            if var == "DEEPINFRA_API_KEY":
                continue  # Already tested separately

            value = os.getenv(var)
            if not value:
                self.warnings.append(f"Recommended variable {var} is not set")
                self.log(f"Recommended variable {var} is not set", "WARN")
                all_present = False
            else:
                self.passed.append(f"Recommended variable {var} is set")
                self.log(f"Recommended variable {var} is set", "PASS")
        return all_present

    def test_optional_vars(self) -> None:
        """Log information about optional environment variables."""
        if self.verbose:
            self.log("Checking optional variables...", "INFO")
            for var in self.OPTIONAL_VARS:
                value = os.getenv(var)
                if value:
                    self.log(f"Optional variable {var} = {value}", "INFO")
                else:
                    self.log(f"Optional variable {var} is not set", "INFO")

    def test_whatsapp_config(self) -> bool:
        """Test if WhatsApp configuration is complete (all or none)."""
        whatsapp_vars = [
            "WHATSAPP_VERIFY_TOKEN",
            "WHATSAPP_ACCESS_TOKEN",
            "WHATSAPP_PHONE_NUMBER_ID",
        ]
        set_vars = [var for var in whatsapp_vars if os.getenv(var)]

        if len(set_vars) == 0:
            self.log("WhatsApp integration not configured (optional)", "INFO")
            return True
        elif len(set_vars) == len(whatsapp_vars):
            self.passed.append("WhatsApp configuration is complete")
            self.log("WhatsApp configuration is complete", "PASS")
            return True
        else:
            self.warnings.append(
                f"Partial WhatsApp configuration detected. "
                f"Set all of: {', '.join(whatsapp_vars)}"
            )
            self.log(
                f"Partial WhatsApp config: {set_vars} set, but missing {[v for v in whatsapp_vars if v not in set_vars]}",
                "WARN",
            )
            return False

    def test_numeric_vars(self) -> bool:
        """Test if numeric environment variables have valid values."""
        numeric_vars = {
            "TOP_K": (1, 100),
            "TIMEOUT_S": (1, 600),
            "API_RATE_LIMIT": (1, 1000),
            "WHATSAPP_RATE_LIMIT": (1, 1000),
            "RATE_LIMIT_WINDOW": (1, 3600),
            "DEFAULT_PROJECT_ID": (1, None),
        }

        all_valid = True
        for var, (min_val, max_val) in numeric_vars.items():
            value = os.getenv(var)
            if not value:
                continue  # Skip if not set

            try:
                num_value = int(value)
                if num_value < min_val:
                    self.warnings.append(f"{var}={num_value} is below minimum {min_val}")
                    self.log(f"{var}={num_value} is below minimum {min_val}", "WARN")
                    all_valid = False
                elif max_val and num_value > max_val:
                    self.warnings.append(f"{var}={num_value} exceeds maximum {max_val}")
                    self.log(f"{var}={num_value} exceeds maximum {max_val}", "WARN")
                    all_valid = False
                else:
                    self.passed.append(f"{var}={num_value} is valid")
                    self.log(f"{var}={num_value} is valid", "PASS")
            except ValueError:
                self.errors.append(f"{var}={value} is not a valid integer")
                self.log(f"{var}={value} is not a valid integer", "ERROR")
                all_valid = False

        return all_valid

    def run_all_tests(self) -> Tuple[int, int, int]:
        """Run all validation tests and return (errors, warnings, passed) counts."""
        self.log("Starting environment validation...", "INFO")
        self.log("=" * 60, "INFO")

        # Run tests
        self.test_env_file_exists()
        self.test_required_vars()
        self.test_database_url_format()
        self.test_openai_api_key_format()
        self.test_deepinfra_api_key()
        self.test_recommended_vars()
        self.test_whatsapp_config()
        self.test_numeric_vars()
        self.test_optional_vars()

        return len(self.errors), len(self.warnings), len(self.passed)

    def print_summary(self):
        """Print a summary of validation results."""
        print("\n" + "=" * 60)
        print("ENVIRONMENT VALIDATION SUMMARY")
        print("=" * 60)

        if self.errors:
            print(f"\n✗ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n⚠ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.verbose and self.passed:
            print(f"\n✓ PASSED ({len(self.passed)} checks)")

        print("\n" + "=" * 60)

        if self.errors:
            print("RESULT: FAILED ✗")
            return False
        elif self.warnings:
            print("RESULT: PASSED WITH WARNINGS ⚠")
            return True
        else:
            print("RESULT: ALL TESTS PASSED ✓")
            return True


def main():
    """Main entry point for the test script."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    validator = EnvValidator(verbose=verbose)
    errors, warnings, passed = validator.run_all_tests()
    success = validator.print_summary()

    # Exit with appropriate code
    if errors > 0:
        sys.exit(1)  # Fatal errors
    elif warnings > 0:
        sys.exit(0)  # Warnings are okay
    else:
        sys.exit(0)  # All good


if __name__ == "__main__":
    main()
