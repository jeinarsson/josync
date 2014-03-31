# Backup with python using rsync

A simple backup script written in python with capability to create snapshot history and handle open/locked files in windows using shadow copies.

## Requirements

The python rsync backup script relies on the following resources:
* Python 2.7
* A cygwin installation of rsync
* A copy of the windows executable vshadow.exe (can be found within the Windows SDKs, e.g. at C:\Program Files\Microsoft SDKs\Windows\v7.0\Bin\x64\vsstools\vshadow.exe, or without x64 for 32-bit version)