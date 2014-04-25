import logging
import logging.config
import json
import argparse

import jobs
import utils


logger = logging.getLogger(__name__)
run_logger = logging.getLogger('josync_run')

def main():
    parser = argparse.ArgumentParser(description='Scripted backup using rsync on Windows.')
    parser.add_argument('jobfile',help='path to job file specifying josync job',type=str)
    parser.add_argument('--debug',help='set all loggers to debug level',action='store_true')
    args = parser.parse_args()
    jobfile = args.jobfile
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if not jobfile.endswith('.josync-job'):
        jobfile = jobfile + '.josync-job'

    logger.info("Session started. Josync version {}.".format(42))

    # enumerate net drives
    utils.enumerate_net_drives()

    # parse global settings file
    utils.read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')


    # parse and execute job file
    try:
        job = jobs.create_job_from_file(jobfile)
        job.run()
        run_logger.info("A josync job was run from {}. No errors encountered.".format(jobfile))
    except Exception as e:
        run_logger.exception(e)


    logger.info("Session ended.")




if __name__ == '__main__':
    with open('default.josync-logging') as f:
        log_config = json.loads(f.read())
    logging.config.dictConfig(log_config)
    logging.getLogger().setLevel(logging.INFO)

    main()
