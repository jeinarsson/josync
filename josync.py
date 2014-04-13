import utils
import jobs
import json
import logging
import logging.config

logger = logging.getLogger(__name__)

def main():
    # TODO parse command line args

    logger.info("Session started. Josync version {}.".format(42))

    # parse global settings file
    utils.read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')


    # parse and execute job file
    try:
        job = jobs.SyncJob("syncjob-example.josync-job")
        job.run()
    except Exception as e:
        utils.log_exception(e)


    logger.info("Session ended.")




if __name__ == '__main__':
    with open('default.josync-logging') as f:
        log_config = json.loads(f.read())
    logging.config.dictConfig(log_config)
    logging.getLogger().setLevel(logging.INFO)

    main()
