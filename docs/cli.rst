********************
Command-line options
********************

usage: ``josync.py [-h] [--debug] [--nonotifications] [--dry-run] jobfile``

positional arguments:
  jobfile            path to job file specifying josync job

optional arguments:
  -h, --help              show this help message and exit
  --debug                 set all loggers to debug level
  --nonotifications       disable notifications on backup failure
  --dry-run               send --dry-run to rsync and do not actually transfer any
                          files