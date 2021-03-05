"""Test suite for the borg interface

I'll be honest. I don't know what I'm doing here. I've never done mocking
before. I don't know how to write efficient tests. But, here we are.
"""

from borgar import borg_iface as BI

from unittest.mock import patch, MagicMock
import itertools
import pytest
import subprocess


@patch("subprocess.run")
def test_exists(mock_run: MagicMock):
    # Test a good run
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
    assert BI.exists()
    mock_run.assert_called_with(
        ["borg", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Test a failing run
    mock_run.reset_mock()
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=127)
    assert not BI.exists()
    mock_run.assert_called()

    # Test with exception
    mock_run.reset_mock()
    mock_run.side_effect = FileNotFoundError("Je suis mock")
    assert not BI.exists()
    mock_run.assert_called()


@pytest.fixture()
def init_etypes_opts_args():
    etypes = [
        BI.EncryptionType.NONE,
        BI.EncryptionType.AUTHENTICATED,
        BI.EncryptionType.AUTHENTICATED_B2,
        BI.EncryptionType.REPOKEY,
        BI.EncryptionType.KEYFILE,
        BI.EncryptionType.REPOKEY_B2,
        BI.EncryptionType.KEYFILE_B2,
    ]

    eopts = [None, None, None, "bar", None, "bar", None]

    enc_arg_map = {
        BI.EncryptionType.NONE: ["--encryption=none"],
        BI.EncryptionType.AUTHENTICATED: ["--encryption=authenticated"],
        BI.EncryptionType.AUTHENTICATED_B2: ["--encryption=authenticated-blake2"],
        BI.EncryptionType.REPOKEY: ["--encryption=repokey"],
        BI.EncryptionType.KEYFILE: ["--encryption=keyfile"],
        BI.EncryptionType.REPOKEY_B2: ["--encryption=repokey-blake2"],
        BI.EncryptionType.KEYFILE_B2: ["--encryption=keyfile-blake2"],
    }

    return (etypes, eopts, enc_arg_map)


@patch("subprocess.run")
def test_init_good(mock_run: MagicMock, init_etypes_opts_args):
    # Scaffold some constants we're gonna need
    etypes, eopts, enc_arg_map = init_etypes_opts_args

    # Test all the good runs
    for etype, eopt in zip(etypes, eopts):
        password_trap = None

        def trap_password(arglist, **kwargs):
            f = kwargs["env"]["BORG_PASSPHRASE_FD"]
            with open(f, "rt") as fh:
                password_trap = fh.read()

        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        if etype is BI.EncryptionType.REPOKEY or etype is BI.EncryptionType.REPOKEY_B2:
            mock_run.side_effect = trap_password
        BI.init(
            name="foo",
            root_path="/tmp",
            encryption=BI.EncTuple(etype, eopt),
        )
        arglist = ["borg", "init"]
        arglist.extend(enc_arg_map[etype])
        arglist.append("/tmp/foo")
        mock_run.assert_called_with(
            arglist,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if etype is BI.EncryptionType.REPOKEY or etype is BI.EncryptionType.REPOKEY_B2:
            assert password_trap == eopt
        mock_run.reset_mock()


@patch("subprocess.run")
def test_init_bad_enc(mock_run: MagicMock, init_etypes_opts_args):
    # Scaffold some constants we're gonna need
    etypes, eopts, enc_arg_map = init_etypes_opts_args

    # Test all the bad runs, but make sure to skip the good ones
    goodlist = list(zip(etypes, eopts))
    for etype, eopt in itertools.product(etypes, eopts):
        if (etype, eopt) in goodlist:
            continue
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1)
        with pytest.raises(BI.BorgMalformedEncryptionException):
            BI.init(
                name="foo",
                root_path="/tmp",
                encryption=BI.EncTuple(etype, eopt),
            )
        mock_run.assert_not_called()
        mock_run.reset_mock()


# We will not be testing for valid root path or repo name. We will pass any such
# errors on down to borg. If it fails, we pass that error up. If Borg doesn't
# fail, then we're fine. Theoretically.

# If we wanted to be thorough, we could do type testing, but this is Python. If
# a number quacks like a string, we'll let it be.

# @patch("subprocess.run")
# def test_init_bad_misc(mock_run: MagicMock, init_etypes_opts_args):
#     etype = BI.EncryptionType.NONE
#     etup = BI.EncTuple(etype, None)

#     # Test giving None as a name
#     mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=2)

#     goodlist = list(zip(etypes, eopts))
#     for etype, eopt in itertools.product(etypes, eopts):
#         if (etype, eopt) in goodlist:
#             continue
#         mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1)
#         assert not BI.init(
#             name="foo",
#             root_path="/tmp",
#             encryption=BI.EncTuple(etype, eopt),
#         )
#         arglist = ["borg", "init"]
#         arglist.extend(enc_arg_map[etype])
#         arglist.append("/tmp/foo")
#         mock_run.assert_called_with(
#             arglist,
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL,
#         )
#         mock_run.reset_mock()
