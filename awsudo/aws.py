"""Interaction with AWS."""

import random
from boto.sts import STSConnection


def assumeRole(credentials, arn):
    sts_connection = STSConnection(
        aws_access_key_id=credentials['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=credentials['AWS_SECRET_ACCESS_KEY'])

    sessionName = "awsudo-%08x" % (random.randint(0, 0xffffffff),)

    response = sts_connection.assume_role(
        role_arn=arn,
        role_session_name=sessionName)

    credentials = response.credentials

    return {
        'AWS_ACCESS_KEY_ID': credentials.access_key,
        'AWS_SECRET_ACCESS_KEY': credentials.secret_key,
        'AWS_SESSION_TOKEN': credentials.session_token,
    }
