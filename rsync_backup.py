#!/usr/bin/env python
import json
import subprocess as sp
import time
import sys
import os
import utils

class CygwinExec(object):
    """Class to execute commands and programs in cygwin."""
    def __init__(self, cygwin_bin_path='C:/cygwin/bin'):
        super(CygwinExec, self).__init__()
        if not os.path.isdir(cygwin_bin_path):
            raise ValueError("The provided cygwin bin path is not a directory. Path given: {}.".format(cygwin_bin_path))

        self.cygpath = '{}/cygpath.exe'.format(cygwin_bin_path)

        if not os.path.isfile(self.cygpath):
            raise IOError("cygpath.exe could not be found at {}.".format(self.cygpath))

    def get_cygwin_path(self,path):
        """Return cygwin path """
        if not os.path.exists(path):
            raise ValueError("The given path does not exist. Path given: {}.".format(path))
        cygpath_process = sp.Popen([self.cygpath,path],stdout=sp.PIPE)
        cygwin_path = cygpath_process.communicate()[0].strip()
        if not len(cygwin_path) > 0:
            raise IOError("No cygwin path was found for {}.".format(path))
        else:
            return cygwin_path

class Backup(object):
    """Class to handle backup through rsync in cygwin."""
    def __init__(self, conf_file):
        super(Backup, self).__init__()
        self.conf_file = conf_file

        # Read config file
        with open(conf_file) as f:
            json_data=f.read()
            config = json.loads(json_data)

        # Check config parameters
        try:
            self.name = config['name']
            self.target = config['target']
            self.win_sources = config['sources']
            self.cygwin_bin_path = config['cygwin_bin_path']
        except KeyError as e:
            print "One of the necessary configuration parameters were not found."
            raise
        if not all([os.path.isdir(s) for s in self.win_sources]):
            raise IOError("One or more source directories does not exist.")
        if not os.path.isdir(self.target):
            raise IOError("Target directory does not exist.")
        if 'datetime_format' not in config:
            self.datetime_format = '%Y-%m-%d-%H%M%S'

        # Create cygwin exec object
        cygwin = CygwinExec(self.cygwin_bin_path)

        # Convert paths to cygwin paths
        self.sources = [cygwin.get_cygwin_path(s) for s in self.win_sources]


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



def print_output(out):
    for line in iter(out.readline, b''):
        print line.strip()
    out.close()


def main():
    backup = Backup('backup.cfg.json')
    print backup.sources

if __name__ == '__main__':
    main()
