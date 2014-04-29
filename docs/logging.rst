***************
Logging
***************

Josync provides extensive logging through Python's built in logging modules. By default a summarized log documenting success or failure of each run is appended to a common log file named ``main.josync-log``. More detailed logs are written to ``{job file name}.josync-job-log``.

If you are happy with the log file names and formatting you don't have to touch the logging settings!

Settings
========

Logging is configured through the ``JSON`` file ``logging.josync-config``. Settings are read as a dictionary and fed to the logging module through ``logging.config.dictConfig()``. One handler is created for each log file and a separate handler is created for logging to ``stdout``.

The `Python logging module documentation <https://docs.python.org/2/library/logging.html>`_ describes the the handlers and formatters that determine where log messages are sent and how they are formatted for each handler. These can be defined in the configuration file and added either to the ``root`` logger handling all log messages or to specific loggers defined in the file. Josync uses one logger for each module (python file) and a separate logger ``josync_run`` for the main log.

If you want to customize the logging configuration, have a look at the example dictionary config found in the `Python logging cookbook <https://docs.python.org/2/howto/logging-cookbook.html#an-example-dictionary-based-configuration>`_.
