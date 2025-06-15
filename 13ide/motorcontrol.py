from time import time, sleep
from epics import caget


def get_xps(conn='mapping_xps'):
    return _scandb.connections.get(conn, None)

def rehome_finemotors():
    xps = _scandb.connections.get('mapping_xps', None)
    if xps is None:
        print("no XPS for mapping defined?")

    else:
        print("Initialize Fine")
        try:
            xps.initialize_group('Fine', home=True)
        except:
            pass
        print("Enable Fine")
        try:
            xps.enable_group('Fine')
        except:
            pass
