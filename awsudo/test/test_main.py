import sys
import pytest

from awsudo import main


def test_no_args(capsys, monkeypatch):
    '''With no arguments, awsudo exits with usage.'''
    monkeypatch.setattr(sys, 'argv', ['awsudo'])

    with pytest.raises(SystemExit):
        main.main()

    out, err = capsys.readouterr()
    assert 'Usage:' in err
