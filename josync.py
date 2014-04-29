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
main_logger = logging.getLogger('josync_run')

def main():
    parser = argparse.ArgumentParser(description='Scripted backup using rsync on Windows.')
    parser.add_argument('jobfile',help='path to job file specifying josync job',type=str)
    parser.add_argument('--debug',help='set all loggers to debug level',action='store_true')
    parser.add_argument('--nonotifications',help='disable notifications on backup failure',action='store_false')
    parser.add_argument('--dry-run',help='send --dry-run to rsync and do not actually transfer any files',action='store_true')

    args = parser.parse_args()
    jobfile = args.jobfile

    with open('logging.josync-config') as f:
        log_config = json.loads(f.read())
    log_config['handlers']['details_file_handler']['filename'] = \
        log_config['handlers']['details_file_handler']['filename'].format(jobfile.replace('.josync-job',''))
    logging.config.dictConfig(log_config)
    logging.getLogger().setLevel(logging.INFO)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if not jobfile.endswith('.josync-job'):
        jobfile = jobfile + '.josync-job'

    logger.info("************************************************************")
    logger.info("Session started. Josync version {}.".format(utils.version))
    if args.nonotifications:
        logger.info("Failure notifications are disabled.")

    utils.initialize()
    utils.config['dry_run'] = args.dry_run

    # parse job file and run job
    try:
        if not args.nonotifications:
            failure_notifier = utils.FailureNotifier(jobfile)

        job = jobs.create_job_from_file(jobfile)
        job.run()
        try:
            transferred = job.stats['file_size_transferred']/1024.0
            total = job.stats['tot_file_size']/1024.0
            main_logger.info("Josync job {} successfully run. {:.1f} of {:.1f} kB updated ({:.1f} %)."\
                                .format(jobfile,transferred,total,100*transferred/total))
        except KeyError as e:
            main_logger.info("Josync job {} successfully run, however, stats could not be retrieved".format(jobfile))

        if not args.nonotifications:
            failure_notifier.record_successful_run()

    except utils.JobDescriptionKeyError as e:
        main_logger.error("The required job parameter '{}' was not found in the job file.".format(e))
    except utils.JobDescriptionValueError as e:
        main_logger.error("Error in job description: {}".format(e))
    except utils.JsonSyntaxError as e:
        main_logger.error("One of the JSON configuration files could not be parsed: {}".format(e))
    except utils.TargetNotFoundError as e:
        main_logger.error("The target directory {} does not exist for job {}.".format(e,jobfile))
        if not args.nonotifications:
            failure_notifier.notify()
    except Exception as e:
        main_logger.error("Josync job {} failed with an exception: {}".format(jobfile,e))
        logger.exception(e)
        if not args.nonotifications:
            failure_notifier.notify()

    logger.info("Session ended.")


if __name__ == '__main__':
    main()
