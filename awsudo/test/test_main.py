import sys
import os
import pytest

from awsudo import main


def test_no_args(capsys, monkeypatch):
    '''With no arguments, awsudo exits with usage.'''
    monkeypatch.setattr(sys, 'argv', ['awsudo'])

    with pytest.raises(SystemExit):
        main.main()

    out, err = capsys.readouterr()
    assert 'Usage:' in err


def test_cleanEnvironment(monkeypatch):
    '''cleanEnvironment strips AWS and boto configuration.'''
    environ = {
        'AWS_SECRET': 'password1',
        'BOTO_CONFIG': 'please work',
        'HOME': 'ward bound',
    }
    monkeypatch.setattr(os, 'environ', environ)

    main.cleanEnvironment()

    assert 'AWS_SECRET' not in environ
    assert 'BOTO_CONFIG' not in environ
    assert environ['HOME'] == 'ward bound'
