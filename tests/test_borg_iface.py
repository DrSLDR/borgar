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

    eopts = [None, None, None, "bar", "/tmp/baz", "bar", "/tmp/baz"]

    enc_arg_map = {
        BI.EncryptionType.NONE: ["--encryption", "none"],
        BI.EncryptionType.AUTHENTICATED: ["--encryption", "authenticated"],
        BI.EncryptionType.AUTHENTICATED_B2: ["--encryption", "authenticated-blake2"],
        BI.EncryptionType.REPOKEY: ["--encryption", "repokey"],
        BI.EncryptionType.KEYFILE: ["--encryption", "keyfile"],
        BI.EncryptionType.REPOKEY_B2: ["--encryption", "repokey-blake2"],
        BI.EncryptionType.KEYFILE_B2: ["--encryption", "keyfile-blake2"],
    }

    return (etypes, eopts, enc_arg_map)


@patch("subprocess.run")
def test_init_good(mock_run: MagicMock, init_etypes_opts_args):
    # Scaffold some constants we're gonna need
    etypes, eopts, enc_arg_map = init_etypes_opts_args

    # Test all the good runs
    for etype, eopt in zip(etypes, eopts):
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        assert BI.init(
            name="foo",
            root_path="/tmp",
            encryption=BI.EncTuple(etype, eopt),
        )
        arglist = ["borg", "init"]
        arglist.extend(enc_arg_map[etype])
        arglist.append("/tmp/foo")
        mock_run.assert_called_with(
            arglist,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
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
        assert not BI.init(
            name="foo",
            root_path="/tmp",
            encryption=BI.EncTuple(etype, eopt),
        )
        mock_run.assert_not_called()
        mock_run.reset_mock()
