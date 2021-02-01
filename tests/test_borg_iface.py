"""Test suite for the borg interface

I'll be honest. I don't know what I'm doing here. I've never done mocking
before. I don't know how to write efficient tests. But, here we are.
"""

from borgar import borg_iface as BI

from unittest.mock import patch, MagicMock
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
