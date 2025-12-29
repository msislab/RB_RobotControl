"""Logger configuration and format setup."""

from loguru import logger
import sys


def setup_logger(
    format_string: str = None,
    level: str = "INFO",
    colorize: bool = True,
    remove_default: bool = True
):
    """
    Configure loguru logger format and settings.
    
    Args:
        format_string: Custom format string. If None, uses default format.
                      Default: "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> - "
                               "{level:<5} - "
                               "[ {file:>25}:{line:<4} ] - "
                               "{message}"
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        colorize: Whether to use colors in output
        remove_default: Whether to remove default handler before adding custom one
    """
    if remove_default:
        logger.remove()  # Remove default handler
    
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> - "
            "{level:<5} - "
            "[{file:>20}:{line:<4} ] - "
            "{message}"
        )
    
    logger.add(
        sys.stderr,
        format=format_string,
        level=level,
        colorize=colorize,
        backtrace=True,
        diagnose=True
    )


def set_simple_format():
    """Set a simple logger format without colors."""
    setup_logger(
        format_string="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        colorize=False
    )


def set_detailed_format():
    """Set a detailed logger format with all information."""
    setup_logger(
        format_string=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> - "
            "{level:<5} - "
            "[ {file:>25}:{line:<4} ] - "
            "{message}"
        )
    )


def set_minimal_format():
    """Set a minimal logger format."""
    setup_logger(
        format_string="{time:HH:mm:ss} | {level} | {message}",
        colorize=False
    )

