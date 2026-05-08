"""
© Ocado Group
Created on 11/12/2023 at 10:59:40(+00:00).

Set up the Code for Life package during installation.
"""

# isort:skip_file

import json
import os
import typing as t
from pathlib import Path

# pylint: disable=import-error
from setuptools import find_packages, setup  # type: ignore[import-untyped]
from setuptools.command.build_py import build_py  # type: ignore[import-untyped]

# pylint: enable=import-error

from codeforlife import DATA_DIR, TEMPLATES_DIR, __version__
from codeforlife.user import FIXTURES_DIR as USER_FIXTURES_DIR
from codeforlife.user import TEMPLATES_DIR as USER_TEMPLATES_DIR

# Get the absolute path of the package.
PACKAGE_DIR = os.path.dirname(__file__)

with open("README.md", "r", encoding="utf-8") as readme:
    long_description = readme.read()


# pylint: disable-next=too-few-public-methods
class BuildPy(build_py):
    """Custom build command to exclude test files."""

    def find_package_modules(self, package: str, package_dir: str):
        """Find all modules in the package, excluding test files."""
        return [
            module
            for module in t.cast(
                t.List[t.Tuple[str, str, str]],
                super().find_package_modules(package, package_dir),
            )
            if not (
                module[1].endswith("_test") or module[1].startswith("test_")
            )
        ]


# Walk through data directory and get relative file paths.
def get_data_files(target_dir: Path):
    """Get the path of all files in a target directory relative to where they
    are located in the package. All subdirectories will be walked.

    Args:
        target_dir: The directory within the package to walk.

    Returns:
        A tuple where the values are (the absolute path to the target directory,
        the paths of all files within the target directory relative to their
        location in the package).
    """
    relative_file_paths: t.List[str] = []
    for dir_path, _, file_names in os.walk(target_dir):
        # Get the relative directory of the current directory.
        relative_dir = os.path.relpath(dir_path, PACKAGE_DIR)
        # Get the relative file path for each file in the current directory.
        relative_file_paths += [
            os.path.join(relative_dir, file_name) for file_name in file_names
        ]

    return str(target_dir), relative_file_paths


def parse_requirements(packages: t.Dict[str, t.Dict[str, t.Any]]):
    """Parse a group of requirements from `Pipfile.lock`.

    https://setuptools.pypa.io/en/latest/userguide/dependency_management.html

    Args:
        packages: The group name of the requirements.

    Returns:
        The requirements as a list of strings, required by `setuptools.setup`.
    """

    requirements: t.List[str] = []
    for name, package in packages.items():
        requirement = name
        if "git" in package:
            requirement += f" @ git+{package['git']}"
            if "ref" in package:
                requirement += f"@{package['ref']}"
            if "subdirectory" in package:
                requirement += f"#subdirectory={package['subdirectory']}"
        elif "version" in package:
            if "extras" in package:
                requirement += f"[{','.join(package['extras'])}]"
            requirement += package["version"]
            if "markers" in package:
                requirement += f"; {package['markers']}"
        requirements.append(requirement)

    return requirements


# Parse Pipfile.lock into strings.
with open("Pipfile.lock", "r", encoding="utf-8") as pipfile_lock:
    lock = json.load(pipfile_lock)
    install_requires = parse_requirements(lock["default"])
    dev_requires = parse_requirements(lock["develop"])

setup(
    name="codeforlife",
    version=__version__,
    author="Ocado",
    author_email="code-for-life-full-time-xd@ocado.com",
    description="Code for Life's common code.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ocadotechnology/codeforlife-package-python",
    packages=find_packages(include=["codeforlife", "codeforlife.*"]),
    package_dir={"codeforlife": "codeforlife"},
    cmdclass={"build_py": BuildPy},
    include_package_data=True,
    data_files=[
        get_data_files(DATA_DIR),
        get_data_files(USER_FIXTURES_DIR),
        get_data_files(TEMPLATES_DIR),
        get_data_files(USER_TEMPLATES_DIR),
    ],
    package_data={"codeforlife": ["py.typed"]},
    python_requires="==3.12.*",
    install_requires=install_requires,
    extras_require={"dev": dev_requires},
    dependency_links=[],
)
