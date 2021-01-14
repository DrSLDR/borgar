"""Test suite for the borg interface

I'll be honest. I don't know what I'm doing here. I've never done mocking
before. I don't know how to write efficient tests. But, here we are.
"""

from borgar import borg_iface as BI

from unittest.mock import patch


def test_dummy():
    assert 1 == 1


@patch("subprocess.run")
def test_dummy_2(mock):
    print(mock)
    BI.dummy()
    mock.assert_called_once_with(["touch", "no"])
