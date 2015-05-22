import os
from os import path
from retrying import retry
from ConfigParser import RawConfigParser
from boto.iam.connection import IAMConnection
from boto.exception import BotoServerError


class CredentialsFile(object):
    def __init__(self, filename=path.expanduser('~/.aws/credentials')):
        self._filename = filename
        self._config = RawConfigParser()

        with open(self._filename, 'r') as f:
            self._config.readfp(f)

    @property
    def keyId(self):
        return self._config.get('default', 'aws_access_key_id')

    @property
    def secretKey(self):
        return self._config.get('default', 'aws_secret_access_key')

    def updateCredentials(self, keyId, secretKey):
        """Write new credentials to the config file.

        I'll also set the umask to 0066, but since I'm the only thing writing
        files you shouldn't mind.
        """

        self._config.set('default', 'aws_access_key_id', keyId)
        self._config.set('default', 'aws_secret_access_key', secretKey)

        os.umask(0o0066)
        os.rename(self._filename, self._filename+'~')
        with open(self._filename, 'w') as f:
            self._config.write(f)


def main():
    credentials = CredentialsFile()

    iam = IAMConnection(
        aws_access_key_id=credentials.keyId,
        aws_secret_access_key=credentials.secretKey,
    )

    userName = getUserName(iam)
    deleteOldKeys(iam, credentials.keyId, userName)
    newKey = makeNewKey(iam, userName)

    iam = IAMConnection(
        aws_access_key_id=newKey['access_key_id'],
        aws_secret_access_key=newKey['secret_access_key'],
    )

    oldKey = credentials.keyId
    deactivateKey(iam, oldKey, userName)

    credentials.updateCredentials(
        newKey['access_key_id'],
        newKey['secret_access_key'],
    )


def getUserName(iam):
    me = iam.get_user()['get_user_response']['get_user_result']['user']
    return me['user_name']


@retry(
    stop_max_delay=30*1000,
    wait_exponential_multiplier=250,
    wait_exponential_max=10*1000,
    retry_on_exception=lambda e: isinstance(e, BotoServerError))
def deactivateKey(iam, oldKey, userName):
    """Set the given key as inactive.

    I'll retry a few times if necessary because AWS's API is eventually
    consistent, and it can take a few seconds for new access keys to start
    working.
    """
    iam.update_access_key(oldKey, 'Inactive', userName)


def abort(message):
    raise SystemExit(message + "\nAborted")


def deleteOldKeys(iam, currentKeyId, userName):
    """Delete all keys except the currentKeyId.

    I'll only delete inactive keys. If I find any that are active, I'll abort
    the program.

    We must delete old keys because each user can have a maximum of two.
    """
    response = iam.get_all_access_keys(userName)['list_access_keys_response']
    allKeys = response['list_access_keys_result']['access_key_metadata']
    oldKeys = filter(lambda k: k['access_key_id'] != currentKeyId, allKeys)

    if len(oldKeys) == len(allKeys):
        abort(
            "Very odd: current key %s is not listed" %
            (currentKeyId,)
        )

    for key in oldKeys:
        if key['status'] == 'Active':
            abort(
                "%s is still active; I will not automatically delete it" %
                (key['access_key_id'],)
            )

    for key in oldKeys:
        iam.delete_access_key(key['access_key_id'])


def makeNewKey(iam, userName):
    response = iam.create_access_key(userName)['create_access_key_response']
    result = response['create_access_key_result']
    return result['access_key']
