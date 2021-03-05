"""Borg interface module

The borgar-internal interface for communicating with (that is, mostly
invoking) borg. We hide all that here for modularity and ease of use.
"""

from collections import namedtuple
from enum import Enum, auto
from os import path as op
import tempfile
import subprocess


class BorgMalformedEncryptionException(Exception):
    """Exception type for bad encryption tuples"""


class BorgGeneralException(Exception):
    """Exception class for any Borg error that doesn't have a specific exception"""


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
    """SHA-256 Authenticated and AES-CTR-256 Encrypted. No opt (None) needed."""
    REPOKEY_B2 = auto()
    """BLAKE2b-256 Authenticated and AES-CTR-256 Encrypted. A passphrase (str)
    is needed as opt."""
    KEYFILE_B2 = auto()
    """BLAKE2b-256 Authenticated and AES-CTR-256 Encrypted. No opt (None) needed."""


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


def init(name: str, root_path: str, encryption: EncTuple) -> None:
    """Inits (creates) a borg repo

    Args:
        name (str): name of the new repo
        root_path (str): path the repo will be created in
        encryption (EncTuple): Encryption tuple defining how the repo will be encrypted

    Throws:
        BorgMalformedEncryptionException: Thrown if the passed in EncTuple is an illegal
            combination
        BorgGeneralException: Thrown if Borg returns an error when called
    """
    ENC_ARG_FLAGS = {
        EncryptionType.NONE: "none",
        EncryptionType.AUTHENTICATED: "authenticated",
        EncryptionType.AUTHENTICATED_B2: "authenticated-blake2",
        EncryptionType.REPOKEY: "repokey",
        EncryptionType.REPOKEY_B2: "repokey-blake2",
        EncryptionType.KEYFILE: "keyfile",
        EncryptionType.KEYFILE_B2: "keyfile-blake2",
    }

    base_args = ["borg", "init"]
    repopath = op.join(root_path, name)
    enc_args = ["--encryption={}".format(ENC_ARG_FLAGS[encryption.enc])]

    passwdflag = (
        encryption.enc is EncryptionType.REPOKEY
        or encryption.enc is EncryptionType.REPOKEY_B2
    )

    if passwdflag:
        with tempfile.NamedTemporaryFile() as ntf:
            ntf.write(encryption.opt.encode("utf8"))
            env_dict = {"BORG_PASSPHRASE_FD": ntf.name.encode("utf8")}
            subprocess.run(
                base_args + enc_args + [repopath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env_dict,
            )
    else:
        subprocess.run(
            base_args + enc_args + [repopath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
