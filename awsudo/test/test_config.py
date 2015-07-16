def test_import_it():
    '''Lazy man's test: just import the module and create an instance.

    Most of the hard functionality is implemented by awscli anyway, and it's
    easy enough to test manually. At least importing the module will check for
    syntax errors, dependencies that can't be imported, and a lot of other
    stuff.
    '''
    from awsudo import config
    config.CredentialResolver()
