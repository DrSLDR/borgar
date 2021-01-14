"""Borg interface module

The borgar-internal interface for communicating with (that is, mostly
invoking) borg. We hide all that here for modularity and ease of use.
"""

import subprocess


def exists() -> bool:
    """Checks that borg is installed and available on path

    Returns:
        bool: True if borg is available.
    """
    try:
        cp = subprocess.run(
            ["borg", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return cp.returncode == 0
    except FileNotFoundError:
        return False
