import utils
import json
import os

class Job(object):
    """Parent class for backup jobs."""
    def __init__(self,job_file):
        super(Job, self).__init__()
        with open(job_file) as f:
            self.params = json.loads(f.read())

        if 'name' not in self.params:
            filename,filext = os.path.splitext(os.path.basename(job_file))
            self.params['name'] =filename

        # Check config parameters
        try:
            self.target = self.params['target']
            self.win_sources = self.params['sources']
        except KeyError as e:
            print "One of the necessary job parameters were not found."
            raise
        if not all([os.path.isdir(s) for s in self.win_sources]):
            raise IOError("One or more source directories does not exist.")
        if not os.path.isdir(self.target):
            raise IOError("Target directory does not exist.")

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
    def __init__(self,job_file):
        super(SyncJob, self).__init__(job_file)

    def run(self):
        target = self.target
        rsync_options = ['-avzh','--chmod=ug=rwx,o=rx','--delete','--verbose']

        for drive,paths in self.sources:
            print "Backup sources on {}.".format(drive)
            with utils.volume_shadow(drive) as drive_root:
                for source_path in paths:
                    print "Run rsync for source {}.".format(source_path)
                    # if s[-1]=='/':
                    #     print "Removing trailing / from source path."
                    #     s = s[:-1]
                    # print "Backing up {} to {}.".format(s,target)

                    # rsync_call = ['rsync']+rsync_options+[s,target]
                    # print "rsync call is:\n"+' '.join(rsync_call)

                    # rsync_process = sp.Popen(rsync_call)
                    # rsync_process.wait()


class TimelineJob(Job):
    """Backups to a timeline of snapshots."""
    def __init__(self, job_file):
        super(TimelineJob, self).__init__(job_file)
        if 'datetime_format' not in self.params:
            self.params['datetime_format'] = '%Y-%m-%d-%H%M%S'

    def run(self):
        target = '{}/{}-{}'.format(self.params['target'],self.params['name'],self.params['datetime_format'])
        rsync_options = ['-avzh','--chmod=ug=rwx,o=rx','--delete','--verbose']

        for s in config['sources']:
            if s[-1]=='/':
                print "Removing trailing / from source path."
                s = s[:-1]
            print "Backing up {} to {}.".format(s,target)

            rsync_call = ['rsync']+rsync_options+[s,target]
            print "rsync call is:\n"+' '.join(rsync_call)

            rsync_process = sp.Popen(rsync_call)
            rsync_process.wait()