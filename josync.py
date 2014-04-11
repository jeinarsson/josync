import utils
import jobs

def main():

    print "Helo. This is josync v. 42."

    # TODO parse command line args

    # parse global settings file
    utils.read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')

    # parse job file
    sj = SyncJob('syncjob-example.josync-job')


    # TODO execute job


    print "good bye"





if __name__ == '__main__':
    main()