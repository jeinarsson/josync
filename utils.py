import os
import json
import subprocess as sp
from contextlib import contextmanager
import re
import tempfile
import logging
import collections
import threading
import sys
import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header

version = "0.0"
config = {}
net_drives = {}
logger = logging.getLogger(__name__)


def initialize():
    # subprocess flags
    config['is_pythonw'] = (os.path.split(os.path.splitext(sys.executable)[0])[1] == "pythonw")
    startupinfo = sp.STARTUPINFO()
    startupinfo.dwFlags |= sp.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = sp.SW_HIDE
    config['subprocess_startupinfo'] = startupinfo

    # enumerate net drives
    enumerate_net_drives()

    # parse global settings file
    read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')



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
    :raises: IOError
    """
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
    process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE, stdin=sp.PIPE, startupinfo=config['subprocess_startupinfo'])

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
        raise OSError("vhadow did not produce a GUID. Return code: {} (hint: try running as administrator)".format(vshadow_returncode))
    shadow_guid = guidmatch.group(1)
    logger.debug("Shadow copy GUID: {}".format(shadow_guid))

    try:
        # mount shadow copy in a temp dir
        shadow_path = tempfile.mkdtemp()
        shadow_mount_path = "{}\\{}".format(shadow_path, drive[0])
        os.mkdir(shadow_mount_path)
        vshadow_returncode, vshadow_output = shell_execute([vshadow, '-el={},{}'.format(shadow_guid, shadow_mount_path)])
        if not vshadow_returncode == 0:
            logger.error("vshadow could not mount shadow copy with GUID {} at {}.\n{}".format(shadow_guid,shadow_mount_path,vshadow_output))
            raise OSError("vshadow could not mount shadow copy: {}".format(shadow_guid))

        logger.info("Shadow copy {} successfully created and mounted at {}".format(shadow_guid,shadow_mount_path))

        yield shadow_path

    finally:

        logger.info("Deleting shadow copy {} of volume {}".format(shadow_guid, drive))
        vshadow_returncode, vshadow_output = shell_execute([vshadow, '-ds={}'.format(shadow_guid)])
        if not vshadow_returncode == 0:
            logger.error("vshadow could not delete shadow copy with GUID {}.\n{}".format(shadow_guid,vshadow_output))
            raise OSError("vshadow could not delete shadow copy: {}".format(shadow_guid))
        os.rmdir(shadow_mount_path)
        os.rmdir(shadow_path)
        logger.info("Shadow copy {} of {} at {} successfully deleted".format(shadow_guid, drive, shadow_mount_path))


def enumerate_net_drives():
    '''Runs NET USE and parses output.

    :returns: List of drive letters and corresponding UNC path as dictionary.
    '''
    returncode, output = shell_execute(["net","use"])

    # typical row to match:
    # OK           B:        \\Hawkins\Jonas Backup    Microsoft Windows Network
    #regex matches only drives with assigned letter, and only "Microsoft Windows Network" shares.
    matches=re.finditer(r"(\w*)\s*([A-Z]:)\s*(\\\\[^\n]+\w)\s+Microsoft Windows Network", output)

    for match in matches:
        drive = match.group(2)
        unc = match.group(3)
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


class Rsync(sp.Popen):
    """Sub-class of subprocess.Popen to run rsync process."""
    def __init__(self, source, target, options=None):
        # Construct rsync call and create process.
        options = options if options is not None else []
        if config['dry_run']:
            options += ['--dry-run']
        self.rsync_call = [config['rsync_bin']]+options+[source,target]
        logger.debug("rsync process created from call {}".format(' '.join(self.rsync_call)))
        logger.info("Starting rsync process.")
        super(Rsync, self).__init__(self.rsync_call,
                                    stdout=sp.PIPE, stderr=sp.PIPE, stdin=sp.PIPE,
                                    bufsize=1,startupinfo=config['subprocess_startupinfo'])

        self.output_buffer = collections.deque(maxlen=20)
        self.threads = [
            self.output_thread(self.stdout,self.stdout_send),
            self.output_thread(self.stderr,self.stderr_send)
        ]


    def output_thread(self,pipe,send):
        """Start thread handling output from rsync."""

        def handle_output(out):
            for line in iter(out.readline, b''):
                # Do something with line
                send(line.rstrip())

        # start thread
        t = threading.Thread(target=handle_output,
                             args=(pipe,))
        t.start()
        return t

    def stdout_send(self,line):
        sys.stdout.write(line+'\n')
        self.output_buffer.append(line)

    def stderr_send(self,line):
        logger.warning(line)

    def wait(self):
        super(Rsync, self).wait()
        for t in self.threads:
            t.join()


def get_file_modification_date(filename):
    """Read 'last modified' metadata of file

    :param filename: filename (with path)
    :type filename: str
    :returns: Datetime object with last modified datetime
    """
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

def send_email(msg_address, msg_subject, msg_body):
    """Sends an e-mail notification using SMTP settings in config.

	:param msg_subject: Message subject.
	:type msg_subject: str
	:param msg_body: Message body.
	:type msg_body: str
	:param user_email: E-mail to send notification to.
	:type user_email: str
	"""
    try:
        s = None
        success = False
        smtp = config['smtp']

        msg = MIMEText(msg_body, 'plain', 'utf-8')
        msg['Subject'] = Header(msg_subject, 'utf-8')
        msg['From'] = smtp['from_address']
        msg['To'] = msg_address

        s = smtplib.SMTP_SSL(smtp['host'], smtp['port'], timeout=10)

        logger.debug("Attempting to log in to {}:{} as {} and send e-mail to {}.".format(smtp['host'],smtp['port'],smtp['username'], msg_address))
        s.login(smtp['username'], smtp['password'])
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        success = True
        logger.info("E-mail successfully sent")
    except KeyError as e:
        logger.error("Could not find required setting in config: {}".format(str(e)))
    except Exception as e:
        logger.exception(e)
    finally:
        if not success:
            logger.info("Could not send e-mail.")
        if s:
            s.quit()


class TargetNotFoundError(Exception):
    pass

class JsonSyntaxError(Exception):
    pass

class JobDescriptionKeyError(Exception):
    pass

class JobDescriptionValueError(Exception):
    pass


class FailureNotifier(object):
    """Keeps track of when the last time a job was successfully run.

    Notifies user per e-mail."""
    def __init__(self, job_file):
        super(FailureNotifier, self).__init__()

        self.job_file = job_file

        logger.info("Creating FailureNotifier from {}.".format(job_file))
        with open(job_file) as f:
            params = json.loads(f.read())

        try:
            notification_options = params['failure_notification']
        except KeyError:
            self.enabled = False

        try:
            self.email = notification_options["e-mail"]
        except KeyError as e:
            raise JobDescriptionKeyError(e.message)

        self.enabled = True

        try:
            self.hours_since_success = self.notification_options["hours_since_success"]
            self.always_send = False
        except KeyError:
            self.always_send = True

        filename, fileext = os.path.splitext(job_file)
        self.last_successful_run = None
        self.last_successful_run_filename = filename + ".josync-job-success"
        if os.path.isfile(self.last_successful_run_filename):
            self.last_successful_run = get_file_modification_date(self.last_successful_run_filename)


    def notify(self):
        """Check if conditions for notification are fulfilled, and send e-mail.
        """
        if not self.enabled:
            return

        will_send = self.always_send

        if not will_send and self.last_successful_run == None:
            logger.warning("Failure notification not sent because no previous successful run detected.")
            return

        if not will_send and not self.hours_since_success is None:
            hours_since_success = (datetime.datetime.now()-self.last_successful_run).total_seconds()/3600.
            if hours_since_success > self.hours_since_success:
                will_send = True
            else:
                logger.info("Failure notification not sent, because time elapsed since last successful run was only {} hour(s)".format(hours_since_success))

        if will_send:
            body = """Your Josync backup job {} have failed and triggered this e-mail notification.

Please check the Josync logs for details.

""".format(self.job_file)
            logger.info("Sending failure notification e-mail.")
            send_email(self.email, "Josync backup job {} failed.".format(self.job_file),body)

    def record_successful_run(self):
        """ Create an empty .josync-job-success file to mark a successful run.
        """
        if not self.notification_options:
            return

        open(self.last_successful_run_filename, 'w').close()
