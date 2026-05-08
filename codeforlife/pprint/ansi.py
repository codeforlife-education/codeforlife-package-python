"""
© Ocado Group
Created on 18/03/2026 at 14:37:45(+00:00).
"""

from enum import Enum


class ANSI(Enum):
    """ANSI escape codes for styling terminal output."""

    RESET = "\033[0m"

    BLACK = "\033[30m"
    WHITE = "\033[37m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    BLUE = "\033[34m"

    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    OVERLINE = "\033[53m"
