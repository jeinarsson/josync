import utils
import json
import os
import logging
import subprocess as sp

logger = logging.getLogger(__name__)



class Job(object):
    """Parent class for backup jobs."""
    def __init__(self,params):
        super(Job, self).__init__()
        self.rsync_options = []

        logger.info("Initializing Job")
        self.params = params

        if 'name' not in self.params:
            filename,filext = os.path.splitext(os.path.basename(params['job_file']))
            self.params['name'] =filename

        # Check config parameters
        self.target = self.params['target']

        target_drive, target_path = os.path.splitdrive(self.target)
        if utils.is_net_drive(target_drive):
            unc = utils.net_drives[target_drive]
            self.target = unc + target_path
            logger.info("Replacing target drive {} with UNC path {}".format(target_drive, unc))

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

    def prepare_source(self,source_drive,mount_root,source_path):
        """Prepare source for rsync call.

        :param source_drive: Drive letter for source drive.
        :type source_drive: str
        :param mount_root: Temp dir for source drive shadow copy.
        :type mount_root: str
        :param source_path: Relative path to source from drive root.
        :type source_path: str
        :returns: str -- Source path ready for rsync.
        """
        return utils.get_cygwin_path("{}{}".format(mount_root,source_path))

    def prepare_target(self,source_drive,source_path,target_path):
        """Prepare target for rsync call.

        :param source_drive: Drive letter for source drive.
        :type source_drive: str
        :param source_path: Relative path to source from drive root.
        :type source_path: str
        :param target_path: Path to target.
        :type target_path: str
        :returns: str -- Target path ready for rsync."""
        return utils.get_cygwin_path(target_path)

    def add_excludes(self,excludes):
        """Add a list of strings to rsync_options as excludes.

        :param excludes: List of excludes.
        """
        for excl in excludes:
            self.rsync_options += ["--exclude",excl]


class BaseSyncJob(Job):
    """Base class for sync-type jobs."""
    def __init__(self,params):
        super(BaseSyncJob, self).__init__(params)
        self.rsync_options += ['-avzP','--chmod=ugo=rwX']

    def run(self):
        """Run rsync to sync one or more sources with one target directory."""
        self.add_excludes(self.params['global_excludes'])

        for drive,sources in self.sources.items():
            logger.info("Backing up sources on {}".format(drive))
            with utils.volume_shadow(drive) as shadow_root:
                for s in sources:
                    logger.info("Backing up {}{} to {}".format(drive,s['path'],self.target))
                    logger.debug("Drive root is found at {} and source path is {}.".format(shadow_root,s['path']))

                    cygsource = self.prepare_source(drive,shadow_root,s['path'])
                    cygtarget = self.prepare_target(drive,s['path'],self.target)
                    self.add_excludes(s['excludes'])

                    rsync_call = [utils.config['rsync_bin']]+self.rsync_options+[cygsource,cygtarget]
                    logger.debug("rsync call is {}".format(' '.join(rsync_call)))
                    # Run rsync
                    # TODO capture and maybe parse output
                    logger.info("Running rsync.")
                    rsync_process = sp.Popen(rsync_call)
                    rsync_process.wait()
                    if rsync_process.returncode != 0:
                        # Appropriate exception type?
                        raise IOError("rsync returned with exit code {}.".format(rsync_process.returncode))
                    else:
                        logger.info("rsync finished successfully.")


class SyncJob(BaseSyncJob):
    """Simple backup syncing multiple sources to a target directory with full tree structure."""
    def __init__(self,params):
        super(SyncJob, self).__init__(params)
        logger.info("Initializing SyncJob.")

        # Delete option to keep up-to-date with sources
        # Relative option to create directory tree at target
        self.rsync_options += ['--delete','--relative']

    def prepare_source(self,source_drive,mount_root,source_path):
        # Insert /./ in source path to create tree at target relative to after /cygdrive/
        cyg_root = utils.get_cygwin_path(mount_root)
        cyg_source_path = utils.get_cygwin_path(source_path)
        full_source_path = '{}/.{}'.format(cyg_root,cyg_source_path)
        return full_source_path

    def prepare_target(self,source_drive,source_path,target_path):
        drive = source_drive.replace(":","")
        return super(SyncJob,self).prepare_target(source_drive,source_path,target_path)+'/{}'.format(drive)


class AdditiveJob(BaseSyncJob):
    """Updating target with new files from sources."""
    def __init__(self,params):
        super(AdditiveJob, self).__init__(params)
        logger.info("Initializing AdditiveJob.")

    def prepare_source(self,source_drive,mount_root,source_path):
        # Add / at the end to start in folder
        return super(AdditiveJob, self).prepare_source(source_drive,mount_root,source_path)+'/'


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
