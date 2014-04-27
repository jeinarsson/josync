import logging
import logging.config
import json
import argparse
import sys
import os
import subprocess as sp

import jobs
import utils


logger = logging.getLogger(__name__)
run_logger = logging.getLogger('josync_run')

def main():
    parser = argparse.ArgumentParser(description='Scripted backup using rsync on Windows.')
    parser.add_argument('jobfile',help='path to job file specifying josync job',type=str)
    parser.add_argument('--debug',help='set all loggers to debug level',action='store_true')
    parser.add_argument('--notifications',help='enable notifications on backup failure (if configured in job file)',action='store_true')
    
    args = parser.parse_args()

    jobfile = args.jobfile
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if not jobfile.endswith('.josync-job'):
        jobfile = jobfile + '.josync-job'

    logger.info("Session started. Josync version {}.".format(utils.version))
    if args.notifications:
        logger.info("Failure notifications are enabled.")

    # enumerate net drives
    utils.enumerate_net_drives()

    # parse global settings file
    utils.read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')

    # parse job file
    job = None
    try:
        job = jobs.create_job_from_file(jobfile)
		run_logger.info("A josync job was created from {}. No errors encountered.".format(jobfile))
    except Exception as e:
        run_logger.exception(e)

    if job:
        try:
            job.run()
        	try:
            	transferred = job.stats['file_size_transferred']/1024.0
            	total = job.stats['tot_file_size']/1024.0
            	run_logger.info("A josync job was run from {}. {:.1f} of {:.1f} kB updated ({:.1f} %). No errors encountered."\
                					.format(jobfile,transferred,total,100*transferred/total))
        	except KeyError as e:
            	run_logger.info("A josync job was run from {}. No errors were encountered, but stats could not retrieved".format(jobfile))

            if args.notifications:
                job.record_successful_run()
        except Exception as e:
            run_logger.exception(e)
            if args.notifications:
                job.failure_notification()


    logger.info("Session ended.")




if __name__ == '__main__':
    utils.config['is_pythonw'] = (os.path.split(os.path.splitext(sys.executable)[0])[1] == "pythonw")
    startupinfo = sp.STARTUPINFO()
    startupinfo.dwFlags |= sp.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = sp.SW_HIDE
    utils.config['subprocess_startupinfo'] = startupinfo

    with open('default.josync-logging') as f:
        log_config = json.loads(f.read())
    logging.config.dictConfig(log_config)
    logging.getLogger().setLevel(logging.INFO)

    main()
