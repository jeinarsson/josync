*********************
Failure notifications
*********************

Josync can send an e-mail to you if a job fails, for example if the sync target is not found, or is full.

The e-mail receipient and notification trigger is configured per job, in the ``.josync-job``-file. The required settings for sending e-mail must be configured in ``default.josync-config``.

If you have configured failure notifications but would like to run Josync with notifications disabled, use the command line option ``--nonotifications``.

Configuring notification for a job
----------------------------------

The notifications are configured in the job description. For example::

    {
        "type": "sync",
        "sources": [
                    {"path": "d:/phd", "excludes": []},
                    {"path": "d:/projects", "excludes": ["*.pyc;*.pyo"]}
            ],
        "global_excludes": ["*.hdf5"],
        "target": "g:/Josync Backups/work",

        "failure_notification": {
            "hours_since_success": 4,
            "e-mail": "me@domain.com"
        }
    }

In this example a notification e-mail will be sent to ``me@domain.com`` if the job fails and it was more than 4 hours since the last successful run. If ``hours_since_success`` is omitted, or set to ``0``, an e-mail is sent on every failure.

Configuring SMTP settings
-------------------------

In order to send e-mail, Josync requires an SMTP-server. The SMTP settings goes in default.josync-config, like this::

    {
        "cygwin_bin_path": ".",
        "vshadow_bin": "./vshadow.exe",

        "smtp": {
            "host": "mysmtp.com",
            "port": 465,
            "username": "username",
            "password": "password",
            "from_address": "me@domain.com"
        }
    }

You can test your settings by running::

    python testmail.py your@address.com

This command will try to send an e-mail to ``your@address.com`` with the Josync settings.
