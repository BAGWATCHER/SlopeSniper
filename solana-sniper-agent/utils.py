"""
Utility functions for Solana Sniper

This module provides logging, configuration loading, and helper functions.
"""

import re
import os
import json
import logging
from pathlib import Path
from urllib.parse import urlparse


class Utils:
    @staticmethod
    def setup_logger(name: str = 'SolanaSniper', log_file: str = 'logs/sniper.log', level=logging.INFO):
        """Setup logging for applications."""
        logger = logging.getLogger(name)

        if not logger.hasHandlers():
            logger.propagate = False
            logger.setLevel(level)

            formatter = logging.Formatter('%(asctime)s | %(name)s.%(funcName)s | %(levelname)s | %(message)s')

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # File handler
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @staticmethod
    def load_config(config_path: str = 'config.json') -> dict:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Config file not found: {config_path}. "
                f"Copy config.example.json to config.json and fill in your values."
            )

    @staticmethod
    def get_env_or_config(key: str, config: dict = None, default=None):
        """
        Get value from environment variable or config dict.
        Environment variables take precedence.

        Args:
            key: Key name
            config: Config dictionary
            default: Default value if not found

        Returns:
            Value from env var, config, or default
        """
        # Check environment variable first (convert to uppercase with underscores)
        env_key = key.upper().replace('-', '_').replace('.', '_')
        env_value = os.environ.get(env_key)
        if env_value:
            return env_value

        # Then check config
        if config and key in config:
            return config[key]

        return default

    @staticmethod
    def parse_contract_address(logger: logging.Logger, text: str) -> str:
        """
        Extract Solana contract address from text.

        Args:
            logger: Logger instance
            text: Text to parse

        Returns:
            Contract address or None
        """
        try:
            # Solana address pattern (base58, 32-44 chars)
            pattern = r'\b[A-HJ-NP-Za-km-z1-9]{43,44}\b'
            match = re.search(pattern, text)

            if match:
                contract_address = match.group(0)
                logger.info('Extracted Contract Address: %s', contract_address)
                return contract_address

            # Try extracting from URLs
            url_pattern = r'(https?://\S+)'
            urls = re.findall(url_pattern, text)
            for url in urls:
                parsed_url = urlparse(url)
                path_parts = parsed_url.path.split('/')
                for part in path_parts:
                    if re.match(pattern, part):
                        logger.info('Extracted Contract Address from URL: %s', part)
                        return part

            logger.info('No CA found in the message')
            return None

        except Exception as e:
            logger.exception('Could not parse the CA from the message: %s', e)
            return None

    @staticmethod
    def parse_tickers_from_text(logger: logging.Logger, text: str) -> list:
        """Parse all tickers preceded by $ in the text."""
        tickers = []
        try:
            pattern = r'\$([A-Za-z]{1,10})'
            tickers = re.findall(pattern, text)
        except Exception as e:
            logger.exception('Could not parse tickers from the message: %s', e)
        else:
            if tickers:
                logger.info('Extracted Tickers: %s', tickers)
            else:
                logger.info('No tickers found')
        return tickers
