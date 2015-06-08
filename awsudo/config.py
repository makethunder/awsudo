from os import path

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class NoRoleForProfileError(Exception):
    pass


class Config(object):
    def __init__(self, configDir=path.expanduser('~/.aws')):
        self._config = configparser.RawConfigParser()
        self._config.read([path.join(configDir, 'config')])

        self._credentials = configparser.RawConfigParser()
        self._credentials.read([path.join(configDir, 'credentials')])

    @staticmethod
    def _sectionForProfile(profile):
        if profile is None or profile == 'default':
            return 'default'
        return 'profile %s' % (profile,)

    def getCredentials(self, profile=None):
        section = self._sectionForProfile(profile)

        return {
            'AWS_ACCESS_KEY_ID':
                self._credentials.get(section, 'aws_access_key_id'),
            'AWS_SECRET_ACCESS_KEY':
                self._credentials.get(section, 'aws_secret_access_key'),
        }

    def getSettings(self, profile=None):
        section = self._sectionForProfile(profile)

        settings = {}

        try:
            region = self._config.get(section, 'region')
        except configparser.NoOptionError:
            pass
        else:
            settings['AWS_DEFAULT_REGION'] = region

        return settings

    def getRole(self, profile=None):
        section = self._sectionForProfile(profile)
        try:
            roleArn = self._config.get(section, 'role_arn')
        except (configparser.NoOptionError, configparser.NoSectionError):
            raise NoRoleForProfileError(profile)

        try:
            sourceProfile = self._config.get(section, 'source_profile')
        except configparser.NoOptionError:
            sourceProfile = 'default'

        return sourceProfile, roleArn


class CredentialResolver(object):
    def __init__(self, config, assumeRole):
        self._config = config
        self._assumeRole = assumeRole

    def getEnvironment(self, profile=None):
        """Return environment variables that should be set for the profile."""
        env = {}
        try:
            sourceProfile, arn = self._config.getRole(profile)
        except NoRoleForProfileError:
            env.update(self._config.getCredentials(profile))
        else:
            sourceCredentials = self._config.getCredentials(sourceProfile)
            env.update(self._assumeRole(sourceCredentials, arn))

        env.update(self._config.getSettings(profile))
        return env
