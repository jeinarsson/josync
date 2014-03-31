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

def log_worker(stdout,stderr):
    '''Read output in a thread.'''
    while True:
        # output = non_block_read(stdout).strip()
        output = stdout.readline().strip()
        errors = stderr.readline().strip()
        if output != '' or errors != '':
            print "OUT: "+output
            print "ERR: "+errors





def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

p = Popen(['myprogram.exe'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
q = Queue()
t = Thread(target=enqueue_output, args=(p.stdout, q))
t.daemon = True # thread dies with the program
t.start()

# ... do other things here

# read line without blocking
try:  line = q.get_nowait() # or q.get(timeout=.1)
except Empty:
    print('no output yet')
else: # got line
    # ... do something with line

# def non_block_read(output):
#     '''Reading non-blocking'''
#     fd = output.fileno()
#     fl = fcntl.fcntl(fd, fcntl.F_GETFL)
#     fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
#     try:
#         return output.read()
#     except:
#         return ''


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
        cygwin_bash = '{}/bash.exe'.format(config['cygwin_bindir'])
        rsync_call = [cygwin_bash,'--login','--verbose','-c','rsync']+rsync_options+[s,target]
        rsync_process = sp.Popen(rsync_call,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)


        thread = Thread(target=log_worker, args=[rsync_process.stdout,rsync_process.stderr], name="rsync_output_thread")
        thread.daemon = True
        thread.start()

        rsync_process.wait()
        thread.join(timeout=1)

if __name__ == '__main__':
    main()
