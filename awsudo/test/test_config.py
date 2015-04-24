import pytest

from textwrap import dedent

from awsudo.config import Config, NoRoleForProfileError, CredentialResolver


class TestConfig:
    def test_getCredentials(self, tmpdir):
        tmpdir.join('credentials').write(dedent('''\
            [default]
            aws_access_key_id = ACCESSKEY
            aws_secret_access_key = SECRET

            [profile test]
            aws_access_key_id = TESTKEY
            aws_secret_access_key = TESTSECRET
            '''))

        config = Config(str(tmpdir))

        # by default, use the default profile
        assert config.getCredentials() == {
            'AWS_ACCESS_KEY_ID': 'ACCESSKEY',
            'AWS_SECRET_ACCESS_KEY': 'SECRET',
        }

        # "default" also works for the default profile
        assert config.getCredentials('default') == {
            'AWS_ACCESS_KEY_ID': 'ACCESSKEY',
            'AWS_SECRET_ACCESS_KEY': 'SECRET',
        }

        # but other profiles can be specified
        assert config.getCredentials('test') == {
            'AWS_ACCESS_KEY_ID': 'TESTKEY',
            'AWS_SECRET_ACCESS_KEY': 'TESTSECRET',
        }

    def test_getSettings(self, tmpdir):
        tmpdir.join('config').write(dedent('''\
            [default]
            region = us-east-1

            [profile two]
            region = us-east-2

            [profile none]
            # this profile does not specify a region
            '''))

        config = Config(str(tmpdir))

        # by default, returns the default profile
        assert config.getSettings() == {
            'AWS_DEFAULT_REGION': 'us-east-1',
        }

        # can specify another profile
        assert config.getSettings('two') == {
            'AWS_DEFAULT_REGION': 'us-east-2',
        }

        # if region is not specified, then that setting isn't present.
        assert config.getSettings('none') == {}

    def test_getRole(self, tmpdir):
        role_arn = 'arn:aws:iam::1234567890:role/developer'
        source_profile = 'default'

        tmpdir.join('config').write(dedent('''\
            [profile developer]
            role_arn = %s
            source_profile = %s

            [profile norole]
            # this profile does not specify a role
            ''' % (role_arn, source_profile)))

        config = Config(str(tmpdir))

        assert config.getRole('developer') == (source_profile, role_arn)

        with pytest.raises(NoRoleForProfileError):
            config.getRole('norole')


class TestCredentialResolver:
    def test_getEnvironment_trivial(self):
        """In the simplest case, the resolver gets the config and the
        credentials and combines them.
        """

        PROFILE = object()
        CREDENTIALS = {'credentials': 'CREDENTIALS'}
        SETTINGS = {'settings': 'SETTINGS'}

        class TestConfig(object):
            def getCredentials(self, profile=None):
                assert profile == PROFILE
                return CREDENTIALS

            def getSettings(self, profile=None):
                assert profile == PROFILE
                return SETTINGS

            def getRole(self, profile=None):
                raise NoRoleForProfileError(profile)

        resolver = CredentialResolver(TestConfig(), None)

        expected = CREDENTIALS.copy()
        expected.update(SETTINGS)

        assert resolver.getEnvironment(PROFILE) == expected

    def test_getEnvironment_assumeRole(self):
        """A role is assumed, if the configuration says so.

        In this scenario, a profile named 'developer' assumes a role, and uses
        the credentials under the 'source' profile to do it.
        """

        ARN = 'arn:aws:iam::1234567890:role/developer'
        SOURCE_CREDENTIALS = {'credentials': 'SOURCE'}
        ASSUMED_CREDENTIALS = {'credentials': 'ASSUMED'}
        SETTINGS = {'settings': 'SETTINGS'}

        class TestConfig(object):
            def getCredentials(self, profile=None):
                assert profile == 'source'
                return SOURCE_CREDENTIALS

            def getSettings(self, profile=None):
                assert profile == 'developer'
                return SETTINGS

            def getRole(self, profile=None):
                assert profile == 'developer'
                return 'source', ARN

        def assumeRole(credentials, arn):
            assert credentials == SOURCE_CREDENTIALS
            assert arn == ARN
            return ASSUMED_CREDENTIALS

        resolver = CredentialResolver(TestConfig(), assumeRole)

        expected = ASSUMED_CREDENTIALS.copy()
        expected.update(SETTINGS)

        assert resolver.getEnvironment('developer') == expected
