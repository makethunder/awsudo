from awsudo.config import CredentialResolver, Config
from awsudo.aws import assumeRole

import errno
import getopt
import os
import sys


def run(args, extraEnv):
    env = os.environ.copy()
    env.update(extraEnv)
    try:
        os.execvpe(args[0], args, env)
    except OSError, e:
        if e.errno != errno.ENOENT:
            raise
        raise SystemExit("%s: command not found" % (args[0],))


def cleanEnvironment():
    """Delete from the environment any AWS or BOTO configuration.

    Since it's this program's job to manage this environment configuration, we
    can blow all this away to avoid any confusion.
    """
    for k in os.environ.keys():
        if k.startswith('AWS_') or k.startswith('BOTO_'):
            del os.environ[k]


def usage():
    sys.stderr.write('''\
Usage: awsudo [-u USER] [--] COMMAND [ARGS] [...]

Sets AWS environment variables and then executes the COMMAND.
''')
    sys.exit(1)


def parseArgs():
    options, args = getopt.getopt(sys.argv[1:], 'u:')

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
    config = Config()
    resolver = CredentialResolver(config, assumeRole)
    run(args, resolver.getEnvironment(profile))
