#!/usr/bin/env python
import json
import subprocess as sp
import time
import sys
import os
# import fcntl
import subprocess
from threading import Thread
from Queue import Queue, Empty

ON_POSIX = 'posix' in sys.builtin_module_names

def print_output(out):
    for line in iter(out.readline, b''):
        print line.strip()
    out.close()


def main():
    # Read config file
    with open('backup.cfg.json') as f:
        json_data=f.read()
        config = json.loads(json_data)



    target = '{}/{}-{}'.format(config['target'],config['name'],time.strftime('%Y-%m-%d-%H%M%S'))
    rsync_options = ['-avzh','--chmod=ug=rwx,o=rx','--delete','--verbose']

    # TODO: clean sources from bad content

    for s in config['sources']:
        if s[-1]=='/':
            raise Exception('Source directories must not end with /')
        print "Backing up {} to {}.".format(s,target)

        cygpath = '{}/cygpath.exe'.format(config['cygwin_bindir'])
        cygwin_bash = '{}/bash.exe'.format(config['cygwin_bindir'])
        cygpath_process = sp.Popen([cygpath,s],stdout=sp.PIPE)
        print cygpath_process.communicate()[0]
        exit()

        rsync_call = [cygwin_bash,'--login','-c']+[' '.join(['rsync']+rsync_options+[s,target])]
        print "rsync call is:\n"+' '.join(rsync_call)
        rsync_process = sp.Popen(rsync_call,stdout=sp.PIPE,stderr=sp.PIPE,bufsize=1,close_fds=ON_POSIX)

        thread_err = Thread(target=print_output, args=(rsync_process.stderr,), name="rsync_error_thread")
        thread_err.daemon = True
        thread_err.start()
        thread_out = Thread(target=print_output, args=(rsync_process.stdout,), name="rsync_out_thread")
        thread_out.daemon = True
        thread_out.start()

        rsync_process.wait()
        thread_err.join()
        thread_out.join()

if __name__ == '__main__':
    main()
