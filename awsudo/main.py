from awscli.errorhandler import ClientError
from awsudo.config import CredentialResolver
from textwrap import dedent
import errno
import getopt
import os
import sys


def run(args, extraEnv):
    env = os.environ.copy()
    env.update(extraEnv)
    try:
        os.execvpe(args[0], args, env)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
        raise SystemExit("%s: command not found" % (args[0],))


def cleanEnvironment():
    """Delete from the environment any AWS or BOTO configuration.

    Since it's this program's job to manage this environment configuration, we
    can blow all this away to avoid any confusion.
    """
    for k in list(os.environ.keys()):
        if k.startswith('AWS_') or k.startswith('BOTO_'):
            del os.environ[k]


def usage():
    sys.stderr.write('''\
Usage: awsudo [-u USER] [--] COMMAND [ARGS] [...]

Sets AWS environment variables and then executes the COMMAND.
''')
    sys.exit(1)


def parseArgs():
    try:
        options, args = getopt.getopt(sys.argv[1:], 'u:')
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)
        usage()

    if not (args):
        usage()

    profile = None
    for (option, value) in options:
        if option == '-u':
            profile = value
        else:
            raise Exception("unknown option %s" % (option,))

    return profile, args


def main():
    profile, args = parseArgs()

    cleanEnvironment()
    resolver = CredentialResolver()
    try:
        run(args, resolver.getEnvironment(profile))
    except ClientError as e:
        if e.error_code != 'InvalidClientTokenId':
            raise
        if e.operation_name != 'AssumeRole':
            raise

        raise SystemExit(dedent('''
            %s

            Are the credentials in ~/.aws/credentials valid?
            ''' % (e.message,)).strip())
