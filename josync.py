import utils
import jobs
import logging

logger = logging.getLogger(__name__)

def main():

    # parse global settings file
    utils.read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')
    utils.clear_logfile()
    utils.init_logger(utils.logger)
    utils.init_logger(jobs.logger)
    utils.init_logger(logger)

    logger.info("Helo. This is josync v. 42.")

    # TODO parse command line args


    # parse job file

    # execute job

    logger.info("good bye")





if __name__ == '__main__':
    main()