import os
import json
import subprocess as sp
from contextlib import contextmanager

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

def shell_execute(command):
    process = sp.Popen(command, stdout=sp.PIPE)
    return process.communicate()[0].strip()    

    
@contextmanager
def volume_shadow(drive):
    
    # create and mount volume shadow
    vshadow = config['vshadow_bin']
    vshadow_output = shell_execute([vshadow, '-p', '-nw', drive])
    # TODO parse guid
    shadow_guid = ""
    # TODO invent clever temp path
    shadow_path = ""
    vshadow_output = shell_execute([vshadow, '-el={},{}'.format(shadow_guid, shadow_path)])

    try:
        yield shadow_path
    finally:
        # dismount and delete volume shadow
        vshadow_output = shell_execute([vshadow, '-ds={}'.format(shadow_guid)])
        #TODO parse output for success
