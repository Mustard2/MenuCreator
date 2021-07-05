# Right click functions and operators
def dump(obj, text):
    print('-'*40, text, '-'*40)
    for attr in dir(obj):
        if hasattr( obj, attr ):
            print( "obj.%s = %s" % (attr, getattr(obj, attr)))

def split_path(str):
    """Splits a data path into rna + id.

    This is the core of creating controls for properties.
    """
    # First split the last part of the dot-chain
    rna, path = str.rsplit('.',1)
    # If the last part contains a '][', it's a custom property for a collection item
    if '][' in path:
        # path is 'somecol["itemkey"]["property"]'
        path, rem = path.rsplit('[', 1)
        # path is 'somecol["itemkey"]' ; rem is '"property"]'
        rna = rna + '.' + path
        # rna is 'rna.path.to.somecol["itemkey"]'
        path = '[' + rem
        # path is '["property"]'
    # If the last part only contains a single '[',
    # it's an indexed value
    elif '[' in path:
        # path is 'someprop[n]'
        path, rem = path.rsplit('[', 1)
        # path is 'someprop' ; rem is ignored
    return rna, path
