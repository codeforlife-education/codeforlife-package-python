"""
These are the common settings that need to be imported in all django projects
throughout our system. Place the following at the END of every settings.py file.

`from codeforlife.settings import *`

If you need to reference a specific CFL setting in a project's setting:
`
# Place this at the top of your file.
from codeforlife import settings as cfl_settings

# Do something with EXAMPLE_SETTING from codeforlife's settings.
cfl_settings.EXAMPLE_SETTING
`
"""

from ._secrets import LatestSecret, TypedLatestSecret, get_secret
from .custom import *
from .django import *
from .google import *
from .third_party import *
