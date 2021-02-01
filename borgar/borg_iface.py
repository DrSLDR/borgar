"""Borg interface module

The borgar-internal interface for communicating with (that is, mostly
invoking) borg. We hide all that here for modularity and ease of use.
"""

from collections import namedtuple
from enum import Enum, auto
from os import name, path as op
from typing import Optional
import subprocess


class EncryptionType(Enum):
    """Enumeration of encryption types accepted by Borg"""

    NONE = auto()
    """No encryption. No opt (None) needed."""
    AUTHENTICATED = auto()
    """SHA-265 Authenticated. Uses HMAC but no encryption. No opt (None) needed.
    """
    AUTHENTICATED_B2 = auto()
    """BLAKE2b-256 Authenticated. Uses HMAC but no encryption. No opt (None)
    needed."""
    REPOKEY = auto()
    """SHA-256 Authenticated and AES-CTR-256 Encrypted. A passphrase (str) is
    needed as opt."""
    KEYFILE = auto()
    """SHA-256 Authenticated and AES-CTR-256 Encrypted. A keyfile path (str) is
    optional as opt."""
    REPOKEY_B2 = auto()
    """BLAKE2b-256 Authenticated and AES-CTR-256 Encrypted. A passphrase (str)
    is needed as opt."""
    KEYFILE_B2 = auto()
    """BLAKE2b-256 Authenticated and AES-CTR-256 Encrypted. A keyfile path (str)
    is optional as opt."""


_EncTuple_ = namedtuple("EncryptionTuple", ["enc", "opt"])


class EncTuple(_EncTuple_):
    """Encryption tuple type.

    Used when invoking init() to encapsulate what type of encryption and what
    argument to give it.

    Args:
        enc (EncryptionType): An encryption type to use. None is not permitted -
          use the enum.
        opt (Optional[str]): An argument to pass to the encryption scheme, such
          as password or path to key file. See EncryptionType docs for info.
    """


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


def init(name: str, root_path: str, encryption: EncTuple) -> bool:
    """Inits (creates) a borg repo

    Args:
        name (str): name of the new repo
        root_path (str): path the repo will be created in
        encryption (EncTuple): Encryption tuple defining how the repo will be encrypted

    Returns:
        bool: True if the repo was successfully created. False otherwise.
    """

    return False
