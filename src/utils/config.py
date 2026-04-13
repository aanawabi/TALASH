"""
Configuration Module
Manages application settings and environment variables.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Application configuration management."""

    def __init__(self, env_file: str = ".env"):
        """
        Load configuration from environment variables.

        Args:
            env_file: Path to .env file
        """
        # Load .env file if it exists
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)

        # API Keys
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

        # Model Settings
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")

        # Paths
        self.input_folder: str = os.getenv("INPUT_FOLDER", "data/input_cvs")
        self.output_folder: str = os.getenv("OUTPUT_FOLDER", "data/output")

        # Processing Settings
        self.max_cv_length: int = int(os.getenv("MAX_CV_LENGTH", "50000"))
        self.batch_size: int = int(os.getenv("BATCH_SIZE", "5"))

        # API Settings
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))

    def validate(self) -> bool:
        """
        Validate required configuration.

        Returns:
            True if configuration is valid
        """
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required. Set it in .env file.")
        return True

    @property
    def input_path(self) -> Path:
        """Get input folder as Path object."""
        path = Path(self.input_folder)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def output_path(self) -> Path:
        """Get output folder as Path object."""
        path = Path(self.output_folder)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global config instance
config = Config()
