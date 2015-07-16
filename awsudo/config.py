from awscli.handlers import awscli_initialize
from botocore.session import Session
from botocore.hooks import HierarchicalEmitter


class CredentialResolver(object):
    def getEnvironment(self, profile=None):
        """Return environment variables that should be set for the profile."""
        eventHooks = HierarchicalEmitter()
        session = Session(event_hooks=eventHooks)

        if profile:
            session.set_config_variable('profile', profile)

        awscli_initialize(eventHooks)
        session.emit('session-initialized', session=session)
        creds = session.get_credentials()

        env = {}

        def set(key, value):
            if value:
                env[key] = value

        set('AWS_ACCESS_KEY_ID', creds.access_key)
        set('AWS_SECRET_ACCESS_KEY', creds.secret_key)
        set('AWS_SESSION_TOKEN', creds.token)
        set('AWS_DEFAULT_REGION', session.get_config_variable('region'))

        return env
