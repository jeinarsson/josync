# Josync is backup using rsync on Windows

Josync is a light-weight Python application for backup using rsync/cygwin, using shadow copies for read access to open files.

Documentation at http://josync.readthedocs.org

Please post any bugs you experience in the issue tracker!

Josync is released under a MIT License (see LICENSE.md)

# This is the Stable 1.x branch

In this branch, only bugfixes for version 1 are allowed.

For development, checkout branch "develop".

# Why?

We wanted a simple, scriptable backup on Windows for personal use.

# The goal

Timeline backups using ``rsync`` on Windows. The aim is a ``Timeline`` job type which makes chronological backups (getting sparser as time passes) with hard links for unchanged files.

# Right now

We are at version 1.0 where the core functionality and utilities are in place. A regular syncronization job runs, and logging works.

# Next up

	* Easy installation by bundling everything in an installer
	* Timeline job type
	* (and see Issue tracker for more, or for posting requests!)


# Please note

Josync is a new project under development, and can not in any way be regarded as ready for production. That said, we run it on our own files without any hesitation.