# Josync is scripted backup using rsync on Windows

Josync is a light-weight Python application for backup using rsync/cygwin, using shadow copies for read access to open files.

Backup jobs are specified in minimal JSON configuration files.

It's not difficult, it's just simple.

## Requirements

Josync relies on the following:

* Python 2.7
* A cygwin installation with rsync
* A copy of the windows executable vshadow.exe (can be found within the Windows SDKs, e.g. at \Microsoft SDKs\Windows\v7.0\Bin\x64\vsstools\vshadow.exe, or without x64 for 32-bit version)