"""
Configuration for the `adtech` CLI.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    # --- Credentials ---
    # Read when the instance is created, so create it after `.env` is loaded.
    OPENAI_API_KEY: str = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""), repr=False
    )

    # --- Agent ---
    # Model turns per audit before the SDK raises `MaxTurnsExceeded`
    MAX_TURNS: int = 30

    # --- Evals ---
    # Relative to the working directory: run `adtech eval` from the repository root.
    EVAL_SUITE: Path = Path("tests/evals/cases.jsonl")

    # --- Parallelism ---
    THREAD_POOL_SIZE: int = 8

    # --- Logging ---
    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "[adtech] %(asctime)s %(levelname)s %(message)s"
