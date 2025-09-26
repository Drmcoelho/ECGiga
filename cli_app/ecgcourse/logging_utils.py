"""Central logging utilities with colorized formatting."""

from __future__ import annotations
import logging
import sys
from typing import Any

from rich.console import Console
from rich.logging import RichHandler


class ColorizedFormatter(logging.Formatter):
    """Simple colorized formatter for ECGCourse logs."""
    
    COLORS = {
        'DEBUG': '\033[94m',      # Blue
        'INFO': '\033[92m',       # Green
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[95m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        level_name = record.levelname
        if level_name in self.COLORS:
            record.levelname = f"{self.COLORS[level_name]}{level_name}{self.RESET}"
        return super().format(record)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for ECGCourse CLI with rich handler.
    
    Args:
        verbose: If True, set DEBUG level for all ecgcourse loggers.
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Setup rich handler for better formatting
    console = Console(file=sys.stderr)
    rich_handler = RichHandler(
        console=console,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )
    rich_handler.setLevel(level)
    
    # Configure root logger for ecgcourse modules
    root_logger = logging.getLogger("ecgcourse")
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(rich_handler)
    
    # Prevent propagation to avoid duplicate messages
    root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module name."""
    # Ensure name starts with ecgcourse for consistent handling
    if not name.startswith("ecgcourse"):
        name = f"ecgcourse.{name}"
    return logging.getLogger(name)