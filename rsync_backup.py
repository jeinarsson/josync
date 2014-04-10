#!/usr/bin/env python
import json
import subprocess as sp
import time
import sys
import os
import utils


def main():
    backup = Backup('backup.cfg.json')
    print backup.sources

if __name__ == '__main__':
    main()
