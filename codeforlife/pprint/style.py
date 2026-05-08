"""
© Ocado Group
Created on 18/03/2026 at 14:37:45(+00:00).
"""

import typing as t

from .ansi import ANSI

if t.TYPE_CHECKING:
    from typing_extensions import Protocol

    # pylint: disable-next=too-few-public-methods
    class ApplyProtocol(Protocol):
        """A protocol for a callable that applies a style to a message."""

        def __call__(self, message: str, **kwargs) -> str: ...


class Style:
    """A callable class that applies styles to messages."""

    Apply: t.TypeAlias = "ApplyProtocol"
    Write: t.TypeAlias = t.Callable[[str], None]

    def __init__(self, apply: Apply, write: Write = print, enabled=True):
        self.original_apply = apply
        self.write = write
        self.enabled = enabled

    def __call__(self, message: str, *args, **kwargs):
        styled_message = self.apply(message)
        self.write(styled_message, *args, **kwargs)

    def apply(self, message: str, **kwargs):
        """Apply the style to the given message.

        Args:
            message: The message to apply the style to.
            **kwargs: Keyword arguments that may be used by the style.

        Returns:
            The styled message.
        """
        return (
            self.original_apply(message, **kwargs) if self.enabled else message
        )

    @classmethod
    def ansi(cls, code: ANSI):
        """Create a style that applies the given ANSI code to messages.

        Args:
            code: The ANSI code to apply.

        Returns:
            A style that applies the given ANSI code to messages.
        """

        def apply(message: str, **kwargs):
            if kwargs.get("reset", True):
                message += ANSI.RESET.value

            return code.value + message

        return cls(apply)

    @classmethod
    def combine(cls, *styles: "Style"):
        """Combine multiple styles into a single style.

        Args:
            *styles: The styles to combine.

        Returns:
            A style that applies all the given styles to messages.
        """

        def apply(message: str, **kwargs):
            for style in styles:
                message = style.apply(message, **kwargs)

            return message

        return cls(apply)

    @classmethod
    def with_defaults(cls, write: Write, enabled=True):
        """Create a style class that uses the given defaults.

        Args:
            write: The function to use for writing the styled message.
            enabled: Whether the style is enabled.

        Returns:
            A style class that uses the given defaults.
        """

        class StyleWithDefaults(cls):  # type: ignore[valid-type,misc]
            """A style class that uses the given defaults."""

            def __init__(
                self, apply: Style.Apply, write=write, enabled=enabled
            ):
                super().__init__(apply, write, enabled)

        return StyleWithDefaults
