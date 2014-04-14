import utils
import json
import os
import logging

logger = logging.getLogger(__name__)



class Job(object):
    """Parent class for backup jobs."""
    def __init__(self,params):
        super(Job, self).__init__()

        logger.info("Initializing Job")
        self.params = params

        if 'name' not in self.params:
            filename,filext = os.path.splitext(os.path.basename(params['job_file']))
            self.params['name'] =filename

        # Check config parameters
        self.target = self.params['target']

        raw_win_sources = self.params['sources']
        self.win_sources = []
        for s in raw_win_sources:
            if not os.path.isdir(s):
                logger.warning("The source directory {} does not exist (ignoring).".format(s))
            else:
                self.win_sources.append(s)
        self.params['sources'] = self.win_sources

        if not os.path.isdir(self.target):
            raise IOError("Target directory {} does not exist.".format(self.target))

        # Group sources in a dict of drives
        self.sources = {}
        for source in self.win_sources:
            drive, path = os.path.splitdrive(source)
            if not os.path.ismount(drive+'/'):
                raise IOError("Unable to identify drive {}.".format(drive))
            if drive in self.sources:
                self.sources[drive].append(path)
            else:
                self.sources[drive] = [path]



    def run(self):
        raise NotImplementedError("Run method of job was not implemented.")


class SyncJob(Job):
    """Simple backup syncing dir to dir."""
    def __init__(self,params):
        super(SyncJob, self).__init__(params)
        logger.info("Initializing SyncJob.")

    def run(self):
        """Run rsync to sync one or more sources with one target directory."""
        target = self.target
        rsync_options = ['-avzh','--chmod=ug=rwx,o=rx','--delete','--verbose']

        for drive,paths in self.sources.items():
            logger.info("Backing up sources on {}".format(drive))
            with utils.volume_shadow(drive) as drive_root:
                for source_path in paths:
                    logger.info("Backing up {}".format(source_path))
                    # TODO run rsync for source_path

# enumerate all possible job types and their constructors
job_types = {
    'sync': SyncJob
}


def create_job_from_file(job_file):
        logger.info("Creating Job from {}.".format(job_file))
        with open(job_file) as f:
            params = json.loads(f.read())
        if not 'type' in params:
            raise IOError('Job file does not specify a job type.')    
    
        if not params['type'] in job_types:
            raise IOError('Job type {} is not valid.'.format(params['type']))

        params['job_file'] = job_file

        return job_types[params['type']](params)
