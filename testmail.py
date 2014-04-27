import logging
import logging.config
import json
import argparse

import jobs
import utils


logger = logging.getLogger(__name__)
run_logger = logging.getLogger('josync_run')

def main():
    parser = argparse.ArgumentParser(description='Test e-mail sending of Josync.')
    parser.add_argument('address',help='e-mail address to send test message to',type=str)
    
    args = parser.parse_args()


    logger.info("E-mail test started. Josync version {}.".format(utils.version))

    # parse global settings file
    utils.read_config(default_cfg='default.josync-config',user_cfg='user.josync-config')

    try:
        utils.send_email(args.address, "Josync test e-mail", """
            Congratulations, this e-mail was successfully sent from Josync.
            """)
    except Exception as e:
        run_logger.exception(e)

    logger.info("Session ended.")




if __name__ == '__main__':
    with open('default.josync-logging') as f:
        log_config = json.loads(f.read())
    logging.config.dictConfig(log_config)
    logging.getLogger().setLevel(logging.DEBUG)

    main()
