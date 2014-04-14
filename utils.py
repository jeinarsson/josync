import os
import json
import subprocess as sp
from contextlib import contextmanager
import re
import tempfile
import logging


config = {}
logger = logging.getLogger(__name__)


def read_config(default_cfg,user_cfg):
    """Read config file and check values"""
    logger.debug("Updating config dictionaries from default file \"{}\" and user file \"{}\".".format(default_cfg,user_cfg))
    update_config(default_cfg)
    update_config(user_cfg)

    # Check config parameters
    try:
        config['cygpath_bin'] = '{}/cygpath.exe'.format(config['cygwin_bin_path'])
    except KeyError as e:
        print "One of the necessary configuration parameters were not found."
        raise
    if not os.path.isfile(config['cygpath_bin']):
        raise IOError("cygpath.exe could not be found at {}.".format(config['cygpath_bin']))
    if not os.path.isfile(config['vshadow_bin']):
        raise IOError("vshadow.exe could not be found at {}.".format(config['vshadow_bin']))


def update_config(config_file):
    """Update the module config dict from a config file."""
    logger.debug("Reading from json config {}.".format(config_file))
    with open(config_file) as f:
        config_in = json.loads(f.read())
    config.update(config_in.items())


def get_cygwin_path(path):
    """Return cygwin path for a given windows path"""
    if not os.path.exists(path):
        raise ValueError("The given path does not exist. Path given: {}.".format(path))
    cygpath = config['cygpath_bin']
    cygwin_path = shell_execute([cygpath,path])
    if not len(cygwin_path) > 0:
        raise IOError("No cygwin path was found for {}.".format(path))
    else:
        return cygwin_path

def shell_execute(command):
    '''Run command with Popen

    Returns: 2-tuple with return code and stdout
    '''
    process = sp.Popen(command, stdout=sp.PIPE)

    stdout = process.communicate()[0].strip()
    return (process.returncode, stdout)


@contextmanager
def volume_shadow(drive):

    logger.info("Attempting to create shadow copy of volume {}".format(drive))

    vshadow = config['vshadow_bin']
    vshadow_returncode, vshadow_output = shell_execute([vshadow, '-p', '-nw', drive])
    guidmatch = re.search(r"\* SNAPSHOT ID = (\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\})", vshadow_output)
    if not guidmatch or not vshadow_returncode == 0:
        raise OSError("vhadow did not produce a GUID. Return code: {}".format(vshadow_returncode))
    shadow_guid = guidmatch.group(1)
    logger.debug("Shadow copy GUID: {}".format(shadow_guid))

    try:
        # mount shadow copy in a temp dir
        shadow_path = tempfile.mkdtemp()
        vshadow_returncode, vshadow_output = shell_execute([vshadow, '-el={},{}'.format(shadow_guid, shadow_path)])
        if not vshadow_returncode == 0:
            logger.error("vshadow could not mount shadow copy with GUID {} at {}.\n{}".format(shadow_guid,shadow_path,vshadow_output))
            raise OSError("vshadow could not mount shadow copy: {}".format(shadow_guid))

        logger.info("Shadow copy {} successfully created and mounted at {}".format(shadow_guid,shadow_path))
        yield shadow_path

    finally:

        logger.info("Deleting shadow copy {} of volume {}".format(shadow_guid, drive))
        vshadow_returncode, vshadow_output = shell_execute([vshadow, '-ds={}'.format(shadow_guid)])
        if not vshadow_returncode == 0:
            logger.error("vshadow could not delete shadow copy with GUID {}.\n{}".format(shadow_guid,vshadow_output))
            raise OSError("vshadow could not delete shadow copy: {}".format(shadow_guid))
        os.rmdir(shadow_path)
        logger.info("Shadow copy {} of {} at {} successfully deleted".format(shadow_guid, drive, shadow_path))


def enumerate_net_drives():
    '''Runs NET USE and parses output
    Returns list of drive letters and corresponding UNC paths cygwin-ified (forward slashes, escaped spaces)
    '''
    returncode, output = shell_execute(["net","use"])

    # typical row to match:
    # OK           B:        \\Hawkins\Jonas Backup    Microsoft Windows Network
    #regex matches only drives with assigned letter, and only "Microsoft Windows Network" shares.
    matches=re.finditer(r"(\w+)\s*([A-Z]:)\s*([\w\s\\]+\w)\s+Microsoft Windows Network", output)
    net_drives=[]
    for match in matches:
        drive = match.group(2)
        unc = match.group(3).replace('\\','/').replace(' ', '\\ ')
        net_drives.append((drive,unc))
        
    logger.info("net use reported {} mapped drives".format(len(net_drives)))
    logger.debug("net use drives: {}".format(net_drives))

    config['net_drives'] = net_drives

    return net_drives
