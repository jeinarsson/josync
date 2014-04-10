import os
import json
import subprocess as sp

def read_config(conf_file):
    """Read config file and check values"""
    with open(conf_file) as f:
        json_data=f.read()
        config = json.loads(json_data)

    # Check config parameters
    try:
        name = config['name']
        target = config['target']
        win_sources = config['sources']
        config['cygpath_bin'] = '{}/cygpath.exe'.format(config['cygwin_bin_path'])
    except KeyError as e:
        print "One of the necessary configuration parameters were not found."
        raise
    if not os.path.isdir(cygwin_bin_path):
        raise ValueError("The provided cygwin bin path is not a directory. Path given: {}.".format(cygwin_bin_path))
    if not os.path.isfile(self.cygpath):
        raise IOError("cygpath.exe could not be found at {}.".format(self.cygpath))
    if not all([os.path.isdir(s) for s in win_sources]):
        raise IOError("One or more source directories does not exist.")
    if not os.path.isdir(target):
        raise IOError("Target directory does not exist.")



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