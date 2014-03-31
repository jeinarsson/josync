#!/usr/bin/env python
import json
import subprocess as sp
import time
import sys
import os
import fcntl
import subprocess
from threading import Thread


def log_worker(stdout):
    '''Read output in a thread.'''
    while True:
        output = non_block_read(stdout).strip()
        if output != '':
            print output


def non_block_read(output):
    '''Reading non-blocking'''
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        return output.read()
    except:
        return ''


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
        rsync_call = ['rsync']+rsync_options+[s,target]
        rsync_process = sp.Popen(rsync_call,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        thread = Thread(target=log_worker, args=[rsync_process.stdout], name="rsync_output_thread")
        thread.daemon = True
        thread.start()

        rsync_process.wait()
        thread.join(timeout=1)

if __name__ == '__main__':
    main()
