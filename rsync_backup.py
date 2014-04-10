#!/usr/bin/env python
import utils
from jobs import SyncJob


def main():
    utils.read_config('settings.josync-config')
    sj = SyncJob('syncjob.josync-job')
    for s in sj.params['sources']:
        print utils.get_cygwin_path(s)

if __name__ == '__main__':
    main()
