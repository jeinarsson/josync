import logging
import logging.config
import json
import argparse

import jobs
import utils


logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Scripted backup using rsync on Windows.')
    parser.add_argument('jobfile',help='path to job file specifying josync job',type=str)
    args = parser.parse_args()
    jobfile = args.jobfile

    logger.info("Session started. Josync version {}.".format(42))

    # enumerate net drives
    utils.enumerate_net_drives()

    # parse global settings file
    utils.read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')


    # parse and execute job file
    try:
        job = jobs.create_job_from_file(args.jobfile)
        job.run()

    except Exception as e:
        logger.exception(e)


    logger.info("Session ended.")




if __name__ == '__main__':
    with open('default.josync-logging') as f:
        log_config = json.loads(f.read())
    logging.config.dictConfig(log_config)
    logging.getLogger().setLevel(logging.INFO)

    main()
