***************
Jobs
***************

This version of Josync provides two types of jobs:
	1. sync
	2. add

sync
====

A ``sync`` job does what you expect from a backup program: it mirrors the source onto the target, and only updates changed files. In particular, when files are removed on the source, they are also removed on the target.

add
===

An ``add`` job copies a source onto a target, but never removes anything from the target.

The typical use-case is a music library stored centrally. Imagine that you keep a subset of the music library on your local computer, and you add some new music to your local library. You would like to copy this new music to the main library, but you cannot use a ``sync`` job, because that will remove everything on the target that is not on your local computer.

A Josync ``add`` job will add your new addition to the main library store, but it will never remove anything.




