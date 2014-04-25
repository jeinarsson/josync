import os
import json
import subprocess as sp
from contextlib import contextmanager
import re
import tempfile
import logging


config = {}
net_drives = {}
logger = logging.getLogger(__name__)


def read_config(default_cfg,user_cfg):
    """Reads config file and checks values.

    :param default_cfg: Path to default config file.
    :type default_cfg: str
    :param user_cfg: Path to user config file.
    :type user_cfg: str
    :raises: KeyError, IOError
    """
    logger.debug("Updating config dictionaries from default file \"{}\" and user file \"{}\".".format(default_cfg,user_cfg))
    update_config(default_cfg)
    update_config(user_cfg)

    # Check config parameters
    try:
        config['cygpath_bin'] = '{}/cygpath.exe'.format(config['cygwin_bin_path'])
        config['rsync_bin'] = '{}/rsync.exe'.format(config['cygwin_bin_path'])
    except KeyError as e:
        print "One of the necessary configuration parameters were not found."
        raise
    if not os.path.isfile(config['cygpath_bin']):
        raise IOError("cygpath.exe could not be found at {}.".format(config['cygpath_bin']))
    if not os.path.isfile(config['vshadow_bin']):
        raise IOError("vshadow.exe could not be found at {}.".format(config['vshadow_bin']))
    if not os.path.isfile(config['rsync_bin']):
        raise IOError("rsync.exe could not be found at {}.".format(config['rsync_bin']))


def update_config(config_file):
    """Update the module config dict from a config file.

    :param config_file: Path to JSON config file.
    :type config_file: str
    """
    if not os.path.isfile(config_file):
        logger.warning("Config file {} not found (ignoring).".format(config_file))
        return
        
    logger.debug("Reading from json config {}.".format(config_file))
    with open(config_file) as f:
        config_in = json.loads(f.read())
    config.update(config_in.items())


def get_cygwin_path(path):
    """Return cygwin path for a given windows path.

    :param path: The windows path to convert.
    :type path: str
    :returns: str -- The cygwin path to ``path``.
    :raises: ValueError, IOError
    """
    if not os.path.exists(path):
        raise ValueError("The given path does not exist. Path given: {}.".format(path))
    cygpath = config['cygpath_bin']
    returncode,cygwin_path = shell_execute([cygpath,path])
    if returncode != 0:
        raise IOError("cygpath returned with exit code {}".format(returncode))
    if not len(cygwin_path) > 0:
        raise IOError("No cygwin path was found for {}.".format(path))
    return cygwin_path


def shell_execute(command):
    """Run command with ``subprocess.Popen``

    :param command: Command to run.
    :type command: str
    :returns: 2-tuple with return code and stdout.
    """
    process = sp.Popen(command, stdout=sp.PIPE)

    stdout = process.communicate()[0].strip()
    return (process.returncode, stdout)


@contextmanager
def volume_shadow(drive):
    """volume_shadow(drive)
    Creates a shadow copy of a drive and mounts it at a temporary directory.

    Implemented with ``contextmanager`` to be used through the python :keyword:`with` statement.

    :param drive: Drive to shadow copy.
    :type drive: str
    :yields: str -- Path to temp folder where shadow copy is mounted.
    :raises: OSError
    """
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
    '''Runs NET USE and parses output.

    :returns: List of drive letters and corresponding UNC paths cygwin-ified (forward slashes, escaped spaces) as dictionary.
    '''
    returncode, output = shell_execute(["net","use"])

    # typical row to match:
    # OK           B:        \\Hawkins\Jonas Backup    Microsoft Windows Network
    #regex matches only drives with assigned letter, and only "Microsoft Windows Network" shares.
    matches=re.finditer(r"(\w*)\s*([A-Z]:)\s*([^\n]+\w)\s+Microsoft Windows Network", output)
    
    for match in matches:
        drive = match.group(2)
        unc = match.group(3).replace('\\','/').replace(' ', '\\ ')
        logger.debug("enumerate network drives matched: 1: \"{}\", 2: \"{}\", 3: \"{}\"".format(match.group(1),match.group(2),match.group(3)))
        net_drives[drive.lower()] = unc

    logger.info("net use reported {} mapped drives".format(len(net_drives)))
    logger.debug("net use drives: {}".format(net_drives))

    return net_drives

def is_net_drive(drive):
    '''Looks up drive in net_drives

    :returns: True if drive is a net drive (is in net_drives list)
    '''
    return drive.lower() in net_drives.keys()