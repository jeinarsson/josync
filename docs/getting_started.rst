***************
Getting started
***************


Prerequisites
=============

Running Josync 1.x requires, in addition to Josync itself,
	* Python 2.7,
	* Cygwin with ``rsync`` and ``cygpath`` binaries,
	* A copy of ``vshadow.exe`` for your operating system.


Python 2.7
----------
Download and install from https://www.python.org/downloads/

Cygwin
------
Download and install from http://cygwin.com/install.html

vshadow.exe
-----------
Either
	* download a zip with binaries from the GitHub 1.0 release https://github.com/jeinarsson/josync/releases, unzip and rename the version appropriate for you to simply ``vshadow.exe``.
Or
	* install the Windows SDK for your Windows version and find ``vshadow.exe`` from the Samples section.


Getting Josync
==============

Either 
	* Download the 1.0 release zip file from GitHub, and unzip.
Or with git installed
	* ``git clone repo/1.0``

Basic configuration
===================

Josync reads its configuration from a JSON-formatted files. 

To get started Josync needs to know where to find the external binaries. By default Josync looks for them in the current working directory. If they are available elsewhere, specify the corresponding paths in ``default.josync-config``. 

Running a basic sync job
========================

Josync reads job descriptions from JSON-formatted job-files.

Josync 1.0 contains a sample job description in ``syncjob-example.josync-job``, it looks like this::

	{
	    "type": "sync",
	    "sources": [
	    		{"path": "d:/phd", "excludes": []},
	    		{"path": "d:/projects", "excludes": ["*.pyc;*.pyo"]}
	    	],
	    "global_excludes": ["*.hdf5"],
	    "target": "g:/Josync Backups/work"
	}


Job descriptions consist of a job type, a list of source paths and a target path. Optionally, a job description may contain exclusion patterns. Excludes may be specified either globally or per source.

To run this job, execute the following command::
	
	python josync.py syncjob-example

The file extension ``.josync-job`` may optionally be left out.