def test_entrypoint():
    '''This is a simple enough program that some lazy developer didn't bother
    writing tests. However, importing it will reveal some issues.
    '''
    from awsudo import rotate
    assert hasattr(rotate, 'main')
