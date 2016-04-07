from __future__ import print_function

import os
import sys
from os import path
from textwrap import dedent
from retrying import retry
from boto.iam.connection import IAMConnection
from boto.exception import BotoServerError

ACCESS_KEY_DOCS = 'http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html'

try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser


class CredentialsFile(object):
    def __init__(self,
                 section,
                 filename=path.expanduser('~/.aws/credentials')):
        self._filename = filename
        self._config = RawConfigParser()
        self.section = section

        with open(self._filename, 'r') as f:
            self._config.readfp(f)

        if not self._config.has_section(section):
            raise SystemExit('could not find section [%s] in %r'
                             % (section, filename))

    @property
    def keyId(self):
        return self._config.get(self.section, 'aws_access_key_id')

    @property
    def secretKey(self):
        return self._config.get(self.section, 'aws_secret_access_key')

    def updateCredentials(self, keyId, secretKey):
        """Write new credentials to the config file.

        I'll also set the umask to 0066, but since I'm the only thing writing
        files you shouldn't mind.
        """

        self._config.set(self.section, 'aws_access_key_id', keyId)
        self._config.set(self.section, 'aws_secret_access_key', secretKey)

        os.umask(0o0066)
        os.rename(self._filename, self._filename+'~')
        with open(self._filename, 'w') as f:
            self._config.write(f)


def main():
    if len(sys.argv) > 2:
        printUsage()
        raise SystemExit(1)

    try:
        section = sys.argv[1]
    except IndexError:
        section = 'default'

    credentials = CredentialsFile(section)

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
    try:
        deactivateKey(iam, oldKey, userName)
    except BotoServerError as e:
        print(e)
        raise SystemExit(dedent('''
        Failed to deactivate the old key (%s) after one minute of
        retrying. Manual remediation will be required.
        %s
        ''' % (oldKey, ACCESS_KEY_DOCS)).strip())

    credentials.updateCredentials(
        newKey['access_key_id'],
        newKey['secret_access_key'],
    )


def printUsage():
    usage = dedent('''
    Usage: awsrotate [SECTION]

    Rotates AWS API keys.

    The key to rotate will be found in the specified SECTION of
    ~/.aws/credentials. If no SECTION is specified, then use "default".

    AWS limits the number of API keys per user to a maximum of 2. So first, any
    inactive keys are deleted. If there are active keys other than the one
    being rotated, awsrotate will abort. This prevents accidental deletion of
    keys that may still be in use.

    A new key is then created.

    Then, the new key is used to deactivate old key. This demonstrates that the
    new key works. The old key is deactivated, not deleted, so it's possible to
    reactivate the old key should it be discovered that it was still in use.

    Finally, the new key is written to ~/.aws/credentials.
    ''').strip()

    print(usage, file=sys.stderr)


def getUserName(iam):
    me = iam.get_user()['get_user_response']['get_user_result']['user']
    return me['user_name']


@retry(
    stop_max_delay=60*1000,
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
    oldKeys = [k for k in allKeys if k['access_key_id'] != currentKeyId]

    if len(oldKeys) == len(allKeys):
        abort(
            "Very odd: current key %s is not listed" %
            (currentKeyId,)
        )

    for key in oldKeys:
        if key['status'] == 'Active':
            abort(dedent('''
            %s is still active: will not automatically delete it.
            Please delete it manually if it is safe to do so.
            %s
            ''' % (key['access_key_id'], ACCESS_KEY_DOCS)).strip())

    for key in oldKeys:
        iam.delete_access_key(key['access_key_id'])


def makeNewKey(iam, userName):
    response = iam.create_access_key(userName)['create_access_key_response']
    result = response['create_access_key_result']
    return result['access_key']


if __name__ == '__main__':
    main()
