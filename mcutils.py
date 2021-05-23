# Right click functions and operators
def dump(obj, text):
    print('-'*40, text, '-'*40)
    for attr in dir(obj):
        if hasattr( obj, attr ):
            print( "obj.%s = %s" % (attr, getattr(obj, attr)))
