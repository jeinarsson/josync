import os
import json
import subprocess as sp

config = {}

def read_config(conf_file):
    """Read config file and check values"""
    with open(conf_file) as f:
        config_in = json.loads(f.read())
    config.update(config_in.items())

    # Check config parameters
    try:
        config['cygpath_bin'] = '{}/cygpath.exe'.format(config['cygwin_bin_path'])
    except KeyError as e:
        print "One of the necessary configuration parameters were not found."
        raise
    if not os.path.isfile(config['cygpath_bin']):
        raise IOError("cygpath.exe could not be found at {}.".format(config['cygpath_bin']))


def get_cygwin_path(path):
    """Return cygwin path for a given windows path"""
    if not os.path.exists(path):
        raise ValueError("The given path does not exist. Path given: {}.".format(path))
    cygpath = config['cygpath_bin']
    cygpath_process = sp.Popen([cygpath,path],stdout=sp.PIPE)
    cygwin_path = cygpath_process.communicate()[0].strip()
    if not len(cygwin_path) > 0:
        raise IOError("No cygwin path was found for {}.".format(path))
    else:
        return cygwin_path