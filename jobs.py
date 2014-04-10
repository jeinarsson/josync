import utils
import json


class Job(object):
    """Parent class for backup jobs."""
    def __init__(self,job_file):
        super(Job, self).__init__()
        with open(job_file) as f:
            json_data=f.read()
            job_params = json.loads(json_data)

        # Check config parameters
        try:
            self.target = job_params['target']
            self.win_sources = job_params['sources']
        except KeyError as e:
            print "One of the necessary job parameters were not found."
            raise
        if not all([os.path.isdir(s) for s in self.win_sources]):
            raise IOError("One or more source directories does not exist.")
        if not os.path.isdir(self.target):
            raise IOError("Target directory does not exist.")

    def run(self):
        pass

class SyncJob(Job):
    """Simple backup syncing dir to dir."""
    def __init__(self,job_file):
        super(SyncJob, self).__init__(job_file)
        if 'datetime_format' not in config:
            self.datetime_format = '%Y-%m-%d-%H%M%S'

    def backup_sources(self):
        target = '{}/{}-{}'.format(config['target'],config['name'],time.strftime('%Y-%m-%d-%H%M%S'))
        rsync_options = ['-avzh','--chmod=ug=rwx,o=rx','--delete','--verbose']

        for s in config['sources']:
            if s[-1]=='/':
                print "Removing trailing / from source path."
                s = s[:-1]
            print "Backing up {} to {}.".format(s,target)

            rsync_call = [cygwin_bash,'--login','-c']+[' '.join(['rsync']+rsync_options+[s,target])]
            print "rsync call is:\n"+' '.join(rsync_call)
            rsync_process = sp.Popen(rsync_call)

            rsync_process.wait()