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

        try:
            self.target = params['target']
            self.raw_sources = params['sources']
        except KeyError as e:
            raise utils.JobDescriptionKeyError(e.message)

        try:
            self.global_excludes = params['global_excludes']
        except KeyError:
            self.global_excludes = []

        self.rsync_base_options = ['--stats','--chmod=ugo=rwX','--compress']
        if not utils.config['is_pythonw']:
            self.rsync_base_options += ['--verbose']

        target_drive, target_path = os.path.splitdrive(self.target)
        if utils.is_net_drive(target_drive):
            unc = utils.net_drives[target_drive]
            self.target = unc + target_path
            logger.debug("Replacing target drive {} with UNC path {}".format(target_drive, unc))
        self.cygtarget = utils.get_cygwin_path(self.target)

        if not os.path.isdir(self.target):
            raise utils.TargetNotFoundError(self.target)

        self.sources = {}
        for s in self.raw_sources:
            drive, path = os.path.splitdrive(s['path'])
            if utils.is_net_drive(drive):
                logger.warning("The source path {} is a mounted net drive (ignoring source).".format(drive+path))
            elif not os.path.isdir(drive+path):
                logger.warning("The source directory {} does not exist (ignoring source).".format(drive+path))
            else:
                relative_source = {
                    'path': path,
                    'excludes': []
                }
                if 'excludes' in s:
                    relative_source['excludes'] = s['excludes']
                if drive in self.sources:
                    self.sources[drive].append(relative_source)
                else:
                    self.sources[drive] = [relative_source]

        self.stats = {}



    def run(self):
        raise NotImplementedError("Run method of job was not implemented.")


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
            "num_files": re.compile("Number of files:\s+([1-9][0-9]{0,2}(?:,[0-9]{3})*|\d+)\s"),
            "files_transferred": re.compile("Number of files transferred:\s+([1-9][0-9]{0,2}(?:,[0-9]{3})*|\d+)\s"),
            "tot_file_size": re.compile("Total file size:\s+([1-9][0-9]{0,2}(?:,[0-9]{3})*|\d+)\s"),
            "file_size_transferred": re.compile("Total transferred file size:\s+([1-9][0-9]{0,2}(?:,[0-9]{3})*|\d+)\s")
        }

        for line in rsync_process.output_buffer:
            for key,pattern in pattern_dict.items():
                match = pattern.match(line)
                if match:
                    value = float(match.group(1).replace(',',''))
                    if key in self.stats:
                        self.stats[key] += value
                    else:
                        self.stats[key] = value


class BaseSyncJob(Job):
    """Base class for sync-type jobs."""
    def __init__(self,params):
        super(BaseSyncJob, self).__init__(params)
        self.rsync_base_options += ['--archive']

    def run(self):
        """Run rsync to sync one or more sources with one target directory."""
        self.rsync_base_options += self.excludes_to_options(self.global_excludes)

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
        logger.debug("SyncJob constructor.")

        # Delete option (also excluded) to keep up-to-date with sources
        # Relative option to create directory tree at target
        self.rsync_base_options += ['--delete','--delete-excluded','--relative']


class AdditiveJob(BaseSyncJob):
    """Updating target with new files from sources."""
    def __init__(self,params):
        super(AdditiveJob, self).__init__(params)
        logger.debug("AdditiveJob constructor.")
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


    try:
        if not params['type'] in job_types:
            raise utils.JobDescriptionValueError('Job type {} is not valid.'.format(params['type']))
    except KeyError as e:
        raise utils.JobDescriptionKeyError(e.message)

    params['job_file'] = job_file

    return job_types[params['type']](params)
