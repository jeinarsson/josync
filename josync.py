import utils
import jobs
import json
import logging
import logging.config

logger = logging.getLogger(__name__)

def main():
    # TODO parse command line args

    logger.info("Helo. This is josync v. 42.")

    # parse global settings file
    utils.read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')


    # parse job file
    job = jobs.SyncJob("syncjob-joel-desktop.josync-job")

    # execute job

    logger.info("good bye")





if __name__ == '__main__':
    with open('default.josync-logging') as f:
        log_config = json.loads(f.read())
    logging.config.dictConfig(log_config)
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().info("Starting logging.")
    main()