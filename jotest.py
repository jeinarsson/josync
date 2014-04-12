import utils
from jobs import SyncJob

def main():

    print "Helo. This is josync v. 42."

    # TODO parse command line args

    # parse global settings file
    utils.read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')

    # parse job file
    sj = SyncJob('syncjob-example.josync-job')
    print sj.source_drives


    # TODO execute job


    print "good bye"





if __name__ == '__main__':
    main()