"""
© Ocado Group
Created on 18/03/2026 at 14:37:45(+00:00).
"""

import os
import typing as t
from timeit import default_timer

from .ansi import ANSI
from .style import Style


# pylint: disable-next=too-many-instance-attributes
class PrettyPrinter:
    """A utility class for pretty-printing styled messages to the terminal."""

    def __init__(
        self,
        write: Style.Write,
        name: str,
        indent_level=0,
        disable_styles=False,
    ):
        self.write = write
        self.name = name
        self.indent_level = indent_level
        self.disable_styles = disable_styles
        self.start_time: t.Optional[float] = None
        self.end_time: t.Optional[float] = None

        self.style = Style.with_defaults(
            write=self.__call__, enabled=not disable_styles
        )

        # Black and white.
        self.black = self.style.ansi(ANSI.BLACK)
        self.white = self.style.ansi(ANSI.WHITE)

        # Red, green, and blue.
        self.red = self.style.ansi(ANSI.RED)
        self.green = self.style.ansi(ANSI.GREEN)
        self.blue = self.style.ansi(ANSI.BLUE)

        # Cyan, magenta, and yellow.
        self.cyan = self.style.ansi(ANSI.CYAN)
        self.magenta = self.style.ansi(ANSI.MAGENTA)
        self.yellow = self.style.ansi(ANSI.YELLOW)

        # Common text styles.
        self.bold = self.style.ansi(ANSI.BOLD)
        self.underline = self.style.ansi(ANSI.UNDERLINE)
        self.overline = self.style.ansi(ANSI.OVERLINE)

        # Status styles.
        self.success = self.style.combine(self.green, self.bold)
        self.error = self.style.combine(self.red, self.bold)
        self.warn = self.warning = self.style.combine(self.yellow, self.bold)
        self.info = self.notice = self.style.combine(self.blue, self.bold)

        # Heading styles.
        self.h1 = self.style(
            lambda message, **kwargs: "\n".join(
                [
                    self.bold.apply(self.divider("="), **kwargs),
                    self.bold.apply(message, **kwargs),
                    self.bold.apply(self.divider("="), **kwargs),
                ]
            )
        )
        self.h2 = self.style(
            lambda message, **kwargs: "\n".join(
                [
                    self.bold.apply(self.divider("-"), **kwargs),
                    self.bold.apply(message, **kwargs),
                    self.bold.apply(self.divider("-"), **kwargs),
                ]
            )
        )
        self.h3 = self.style.combine(self.overline, self.underline, self.bold)

    def __call__(self, message: str, *args, **kwargs):
        # pylint: disable=line-too-long
        """Write a message to the terminal.

        Args:
            message: The message to write.
            *args: Additional positional arguments to pass to the write function.
            **kwargs: Additional keyword arguments to pass to the write function.
        """
        # pylint: enable=line-too-long
        indented_message = self.indent(self.indent_level) + message
        self.write(indented_message, *args, **kwargs)

    def __enter__(self):
        self.bold(self.name)
        self.indent_level = max(0, self.indent_level + 1)

        self.start_time = default_timer()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = default_timer()
        elapsed_time = self.end_time - (self.start_time or self.end_time)

        self.indent_level = max(0, self.indent_level - 1)
        self(
            self.bold.apply(f"{self.name} ")
            + (self.error.apply("✘") if exc_type else self.success.apply("✔"))
            + self.bold.apply(f" ({elapsed_time:.2f}s elapsed)")
        )

    def process(
        self,
        name: str,
        indent_level: t.Optional[int] = None,
        disable_styles: t.Optional[bool] = None,
    ):
        """
        A context manager for processing a message with automatic success or
        error handling. If an exception is raised within the context, the
        message is marked as an error; otherwise, it is marked as a success.

        Any messages written within the context are indented by the specified
        level and written when the context is entered.
        """
        return self.__class__(
            write=self.write,
            name=name,
            indent_level=(
                self.indent_level if indent_level is None else indent_level
            ),
            disable_styles=(
                self.disable_styles
                if disable_styles is None
                else disable_styles
            ),
        )

    def divider(self, char="-", default_columns=80):
        # pylint: disable=line-too-long
        """Write a divider line with the specified character.

        Args:
            default_columns: The default number of columns to use if the terminal width cannot be determined.
            char: The character to use for the divider.
        """
        # pylint: enable=line-too-long
        try:
            columns = os.get_terminal_size().columns
        except OSError:
            columns = default_columns

        return char * columns

    def indent(self, count: int, spaces=4, char=" "):
        """Write an indentation of the specified number of spaces.

        Args:
            count: The number of indentation levels.
            spaces: The number of spaces per indentation level.
            char: The character to use for indentation.
        """
        return char * count * spaces


pprint = PrettyPrinter(write=print, name="main")
