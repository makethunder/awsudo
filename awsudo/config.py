from awscli.customizations.assumerole import inject_assume_role_provider_cache
from botocore.session import Session
from botocore.hooks import HierarchicalEmitter


class CredentialResolver(object):
    def getEnvironment(self, profile=None):
        """Return environment variables that should be set for the profile."""
        eventHooks = HierarchicalEmitter()
        session = Session(event_hooks=eventHooks)

        if profile:
            session.set_config_variable('profile', profile)

        eventHooks.register('session-initialized',
                            inject_assume_role_provider_cache,
                            unique_id='inject_assume_role_cred_provider_cache')

        session.emit('session-initialized', session=session)
        creds = session.get_credentials()

        env = {}

        def set(key, value):
            if value:
                env[key] = value

        set('AWS_ACCESS_KEY_ID', creds.access_key)
        set('AWS_SECRET_ACCESS_KEY', creds.secret_key)

        # AWS_SESSION_TOKEN is the ostensibly the standard:
        # http://blogs.aws.amazon.com/security/post/Tx3D6U6WSFGOK2H/A-New-and-Standardized-Way-to-Manage-Credentials-in-the-AWS-SDKs
        # http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-environment
        set('AWS_SESSION_TOKEN', creds.token)

        # ...but boto expects AWS_SECURITY_TOKEN. Set both for compatibility.
        # https://github.com/boto/boto/blob/b016c07d834df5bce75141c4b9d2f3d30352e1b8/boto/connection.py#L438
        set('AWS_SECURITY_TOKEN', creds.token)

        set('AWS_DEFAULT_REGION', session.get_config_variable('region'))

        return env
