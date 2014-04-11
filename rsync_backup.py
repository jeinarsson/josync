#!/usr/bin/env python
import utils
from jobs import SyncJob


def main():
    utils.read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')
    print utils.config['cygwin_bin_path']
    # sj = SyncJob('syncjob.josync-job')
    # for s in sj.params['sources']:
    #     print utils.get_cygwin_path(s)

if __name__ == '__main__':
    main()
