import utils
import json
import os
import logging
import subprocess as sp
import re
import datetime

logger = logging.getLogger(__name__)

class Job(object):
    """Parent class for backup jobs."""
    def __init__(self,params):
        super(Job, self).__init__()
        logger.debug("Entering Job constructor.")

        self.params = params

        self.rsync_base_options = ['--stats','--chmod=ugo=rwX','--compress']
        if not utils.config['is_pythonw']:
            self.rsync_base_options += ['--verbose']

        filename, fileext = os.path.splitext(os.path.basename(params['job_file']))
        if 'name' not in self.params:
            self.params['name'] = filename

        self.last_successful_run = None
        self.success_file = filename + ".josync-job-success"
        if os.path.isfile(self.success_file):
            self.last_successful_run = utils.get_file_modification_date(self.success_file)

        self.target = self.params['target']

        target_drive, target_path = os.path.splitdrive(self.target)
        if utils.is_net_drive(target_drive):
            unc = utils.net_drives[target_drive]
            self.target = unc + target_path
            logger.info("Replacing target drive {} with UNC path {}".format(target_drive, unc))
        self.cygtarget = utils.get_cygwin_path(self.target)

        if not os.path.isdir(self.target):
            raise IOError("Target directory {} does not exist.".format(self.target))

        # Check source path validity: exists and local
        raw_win_sources = self.params['sources']
        self.win_sources = []
        for s in raw_win_sources:
            drive, path = os.path.splitdrive(s['path'])
            if utils.is_net_drive(drive):
                logger.warning("The source path {} is a mounted net drive (ignoring source).".format(s['path']))
            elif not os.path.isdir(s['path']):
                logger.warning("The source directory {} does not exist (ignoring source).".format(s['path']))
            else:
                self.win_sources.append(s)
        self.params['sources'] = self.win_sources

        # Group sources in a dict of drives
        self.sources = {}
        for s in self.win_sources:
            drive, path = os.path.splitdrive(s['path'])
            s['path'] = path
            if 'excludes' not in s:
                s['excludes'] = []
            if not os.path.ismount(drive+'/'):
                raise IOError("Unable to identify drive {}.".format(drive))
            if drive in self.sources:
                self.sources[drive].append(s)
            else:
                self.sources[drive] = [s]

        if 'global_excludes' not in self.params:
            self.params['global_excludes'] = []



    def run(self):
        raise NotImplementedError("Run method of job was not implemented.")

    def failure_notification(self):

        if not 'failure_notification' in self.params:
            return


        notification_options = {
            "always": False
        }
        notification_options.update(self.params['failure_notification'])

        if not 'e-mail' in notification_options:
            raise ValueError("Notifications enabled, but no e-mail address specified in job file.")
            return

        will_send = notification_options["always"]

        if not will_send and self.last_successful_run == None:
            logger.warning("Failure notification not sent because no previous successful run detected.")
            return

        if not will_send and 'hours_since_success' in notification_options:
            hours_since_success = (datetime.datetime.now()-self.last_successful_run).total_seconds()/3600.
            if hours_since_success > notification_options["hours_since_success"]:
                will_send = True
            else:
                logger.info("Failure notification not sent, because time elapsed since last successful run was only {} hour(s)".format(hours_since_success))

        if will_send:
            body = """Your Josync backup job {} have failed and triggered this e-mail notification.

Please check the Josync logs for details.

""".format(self.params['name'])
            logger.info("Sending failure notification e-mail.")
            utils.send_email(notification_options["e-mail"], "Josync backup job {} failed.".format(self.params['name']),body)

    def record_successful_run(self):
        if not 'failure_notification' in self.params:
            return
        
        open(self.success_file, 'w').close()

    def excludes_to_options(self,excludes):
        """Convert a list of strings to a list of exclude options to rsync.

        :param excludes: List of excludes.
        """
        options = []
        for excl in excludes:
            options.append("--exclude={}".format(excl))
        return options

    def run_rsync(self):
        rsync_options = self.rsync_base_options + self.rsync_options
        rsync_process = utils.Rsync(self.rsync_source,self.rsync_target,rsync_options)
        rsync_process.wait()

        if rsync_process.returncode != 0:
            # Appropriate exception type?
            raise IOError("rsync returned with exit code {}.".format(rsync_process.returncode))
        else:
            logger.info("rsync finished successfully.")

        # Parse rsync stats output, typically finde the numbers in lines like:
        # Number of files: 211009
        # Number of files transferred: 410
        # Total file size: 903119614118 bytes
        # Total transferred file size: 9046197739 bytes
        pattern_dict = {
            "num_files": re.compile("Number of files:\s+(\d+)"),
            "files_transferred": re.compile("Number of files transferred:\s+(\d+)"),
            "tot_file_size": re.compile("Total file size:\s+(\d+)"),
            "file_size_transferred": re.compile("Total transferred file size:\s+(\d+)")
        }
        self.stats = {}
        for line in rsync_process.output_buffer:
            for key,pattern in pattern_dict.items():
                match = pattern.match(line)
                if match:
                    self.stats[key] = float(match.group(1))


class BaseSyncJob(Job):
    """Base class for sync-type jobs."""
    def __init__(self,params):
        super(BaseSyncJob, self).__init__(params)
        self.rsync_base_options += ['--archive']

    def run(self):
        """Run rsync to sync one or more sources with one target directory."""
        self.rsync_base_options += self.excludes_to_options(self.params['global_excludes'])

        for drive,sources in self.sources.items():
            logger.info("Backing up sources on {}".format(drive))
            with utils.volume_shadow(drive) as shadow_root:
                for s in sources:
                    logger.info("Backing up {}{} to {}".format(drive,s['path'],self.target))
                    logger.debug("Drive root is found at {} and source path is {}.".format(shadow_root,s['path']))

                    drive_letter = drive[0]
                    self.rsync_source = '{}/./{}{}'.format(
                                    utils.get_cygwin_path(shadow_root),
                                    drive_letter,
                                    utils.get_cygwin_path(s['path']))
                    self.rsync_target = self.cygtarget
                    self.rsync_options = self.excludes_to_options(s['excludes'])

                    self.run_rsync()


class SyncJob(BaseSyncJob):
    """Simple backup syncing multiple sources to a target directory with full tree structure."""
    def __init__(self,params):
        super(SyncJob, self).__init__(params)
        logger.info("Initializing SyncJob.")

        # Delete option (also excluded) to keep up-to-date with sources
        # Relative option to create directory tree at target
        self.rsync_base_options += ['--delete','--delete-excluded','--relative']


class AdditiveJob(BaseSyncJob):
    """Updating target with new files from sources."""
    def __init__(self,params):
        super(AdditiveJob, self).__init__(params)
        logger.info("Initializing AdditiveJob.")
        for s in self.sources:
            s['path'] += '/'


# enumerate all possible job types and their constructors
job_types = {
    'sync': SyncJob,
    'add': AdditiveJob
}


def create_job_from_file(job_file):
    """Creates a job from a JSON job specification.

    :param job_file: Path to job file.
    :type job_file: str
    :returns: Job object of specified type.
    """
    logger.info("Creating Job from {}.".format(job_file))
    with open(job_file) as f:
        params = json.loads(f.read())
    if not 'type' in params:
        raise IOError('Job file does not specify a job type.')

    if not params['type'] in job_types:
        raise IOError('Job type {} is not valid.'.format(params['type']))

    params['job_file'] = job_file

    return job_types[params['type']](params)
