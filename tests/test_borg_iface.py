"""Test suite for the borg interface

I'll be honest. I don't know what I'm doing here. I've never done mocking
before. I don't know how to write efficient tests. But, here we are.
"""

from borgar import borg_iface as BI

from unittest.mock import patch, MagicMock
import itertools
import pytest
import subprocess
import tempfile


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
        passwdflag = (
            etype is BI.EncryptionType.REPOKEY or etype is BI.EncryptionType.REPOKEY_B2
        )

        if passwdflag:
            passwdstore = tempfile.TemporaryFile()

        cp = subprocess.CompletedProcess(args=[], returncode=0)

        def trap_password(arglist, **kwargs):
            f = kwargs["env"]["BORG_PASSPHRASE_FD"]
            with open(f, "rb") as fh:
                passwd = fh.read()
                passwdstore.write(passwd)
            return cp

        if passwdflag:
            mock_run.side_effect = trap_password
        else:
            mock_run.return_value = cp
        BI.init(
            name="foo",
            root_path="/tmp",
            encryption=BI.EncTuple(etype, eopt),
        )
        arglist = ["borg", "init"]
        arglist.extend(enc_arg_map[etype])
        arglist.append("/tmp/foo")
        assert arglist == mock_run.call_args.args[0]
        assert ("stdout", subprocess.PIPE) in mock_run.call_args.kwargs.items()
        assert ("stderr", subprocess.PIPE) in mock_run.call_args.kwargs.items()
        if passwdflag:
            assert "env" in mock_run.call_args.kwargs.keys()
            assert "BORG_PASSPHRASE_FD" in mock_run.call_args.kwargs["env"]
            passwdstore.seek(0)
            trapped_passwd = passwdstore.read().decode("utf8")
            passwdstore.close()
            assert trapped_passwd == eopt
        mock_run.reset_mock(side_effect=True)


@patch("subprocess.run")
def test_init_bad_enc(mock_run: MagicMock, init_etypes_opts_args):
    # Scaffold some constants we're gonna need
    etypes, eopts, _ = init_etypes_opts_args

    # Extend the eopts with some bad types
    eopts.extend([[], 0, -1, ("a", "b"), (), "foo".encode("utf8")])

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


@patch("subprocess.run")
def test_init_bad_stems(mock_run: MagicMock, init_etypes_opts_args):
    _, _, enc_arg_map = init_etypes_opts_args

    etype = BI.EncryptionType.NONE
    etup = BI.EncTuple(etype, None)

    # Test empty strings as stems
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=2)

    with pytest.raises(BI.BorgGeneralException):
        BI.init("", "", etup)

    mock_run.assert_called_once_with(
        ["borg", "init", enc_arg_map[etype][0], ""],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    mock_run.reset_mock()

    # Test illegal types as stems
    stem = [2, 0, -1, (), None, {}]

    for root, name in itertools.product(stem, stem):
        with pytest.raises(IOError):
            BI.init(name, root, etup)
        mock_run.assert_not_called()
