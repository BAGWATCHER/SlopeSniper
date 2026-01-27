"""
Utility functions for SlopeSniper SDK.

Provides logging and validation helpers.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from urllib.parse import urlparse


class Utils:
    """Utility class with static helper methods."""

    @staticmethod
    def setup_logger(
        name: str = "SlopeSniper",
        log_file: str | None = None,
        level: int = logging.INFO,
    ) -> logging.Logger:
        """
        Set up a logger with console and optional file output.

        Args:
            name: Logger name
            log_file: Optional log file path (if None, console only)
            level: Logging level

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)

        if not logger.hasHandlers():
            logger.propagate = False
            logger.setLevel(level)

            formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
            )

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # File handler (optional)
            if log_file:
                Path(log_file).parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        return logger

    @staticmethod
    def get_env_or_default(key: str, default: str | None = None) -> str | None:
        """
        Get value from environment variable.

        Args:
            key: Key name
            default: Default value if not found

        Returns:
            Value from env var or default
        """
        env_key = key.upper().replace("-", "_").replace(".", "_")
        return os.environ.get(env_key, default)

    @staticmethod
    def is_valid_solana_address(address: str) -> bool:
        """
        Check if a string is a valid Solana address.

        Validates base58 encoding and length (32-44 chars).

        Args:
            address: Address to validate

        Returns:
            True if valid Solana address
        """
        if not address or not isinstance(address, str):
            return False
        pattern = r"^[A-HJ-NP-Za-km-z1-9]{32,44}$"
        return bool(re.match(pattern, address))

    @staticmethod
    def parse_contract_address(text: str) -> str | None:
        """
        Extract Solana contract address from text.

        Handles both raw addresses and URLs containing addresses.

        Args:
            text: Text to parse

        Returns:
            Contract address or None if not found
        """
        try:
            # Solana address pattern (base58, 43-44 chars)
            pattern = r"\b[A-HJ-NP-Za-km-z1-9]{43,44}\b"
            match = re.search(pattern, text)

            if match:
                return match.group(0)

            # Try extracting from URLs
            url_pattern = r"(https?://\S+)"
            urls = re.findall(url_pattern, text)
            for url in urls:
                parsed_url = urlparse(url)
                path_parts = parsed_url.path.split("/")
                for part in path_parts:
                    if re.match(pattern, part):
                        return part

            return None

        except Exception:
            return None
