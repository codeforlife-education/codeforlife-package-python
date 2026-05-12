"""
© Ocado Group
Created on 20/02/2024 at 09:28:27(+00:00).
"""

import os
import sys
from pathlib import Path

# Do NOT set manually!
# This is auto-updated by python-semantic-release in the pipeline.
__version__ = "0.34.0"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.joinpath("data")
TEMPLATES_DIR = BASE_DIR.joinpath("templates")
USER_DIR = BASE_DIR.joinpath("user")
LEGACY_DIR = BASE_DIR.joinpath("legacy")


def set_up_settings(service_base_dir: Path, service_name: str):
    """Set up the settings for the service.

    *This needs to be called before importing the CFL settings!*

    Examples:
        ```
        from codeforlife import set_up_settings

        # Must set up settings before importing them!
        set_up_settings(BASE_DIR, service_name="my-service")

        from codeforlife.settings import *
        ```

    Args:
        service_base_dir: The base directory of the service.
        service_name: The name of the service.
    """

    # Validate CFL settings have not been imported yet.
    if "codeforlife.settings" in sys.modules:
        raise ImportError(
            "You must set up the CFL settings before importing them."
        )

    # Set required environment variables.
    os.environ["SERVICE_BASE_DIR"] = str(service_base_dir)
    os.environ["SERVICE_NAME"] = service_name
