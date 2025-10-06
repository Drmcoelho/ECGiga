"""Root CLI dispatcher for ECGCourse with global options."""

from __future__ import annotations
import typer
from typing_extensions import Annotated

from .logging_utils import setup_logging, get_logger
from .quiz_cli import quiz_app
from .analyze_cli import analyze_app
from .ingest_cli import ingest_app
from .cv_cli import cv_app
from .assets_cli import assets_app

logger = get_logger(__name__)

app = typer.Typer(
    help="ECGCourse CLI — interactive ECG learning platform with quizzes, analysis, and computer vision tools."
)

def version_callback(value: bool):
    """Print version information."""
    if value:
        from pathlib import Path
        version_file = Path(__file__).parent.parent.parent / "VERSION"
        if version_file.exists():
            version = version_file.read_text().strip()
        else:
            version = "unknown"
        typer.echo(f"ECGCourse CLI version: {version}")
        raise typer.Exit()


@app.callback()
def main(
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v",
        help="Enable debug logging for all ecgcourse modules"
    )] = False,
    version: Annotated[bool, typer.Option(
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    )] = False,
):
    """ECGCourse CLI — Interactive ECG learning platform.
    
    Provides tools for ECG quiz management, signal analysis, image processing,
    and educational content generation.
    """
    # Setup logging based on verbose flag
    setup_logging(verbose=verbose)
    
    if verbose:
        logger.debug("Debug logging enabled for all ecgcourse modules")


# Add sub-applications
app.add_typer(quiz_app, name="quiz", help="Quiz management and interactive learning")
app.add_typer(analyze_app, name="analyze", help="ECG signal analysis and calculations")
app.add_typer(ingest_app, name="ingest", help="ECG image ingestion and processing")
app.add_typer(cv_app, name="cv", help="Computer vision operations for ECG images")
app.add_typer(assets_app, name="assets", help="Asset management and downloads")


if __name__ == "__main__":
    app()