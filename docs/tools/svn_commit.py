#!/usr/bin/env python3
# Apache License, Version 2.0
# Copyright 2015 Anton Felix Lorenzen <anfelor@web.de>
# <pep8 compliant>

"""
SVN Commit: commit the changes to svn with an helpful commit message.

Example (-p = Prefix, -s = Suffix):

  svn_commit.py ../locale/fr -p 'FR: ' -s 'Happy New Year!'
"""

import os
import subprocess

import importlib.util
mod_file_path = os.path.join(os.path.dirname(__file__), "..", "tools_report", "file_translation_progress.py")
spec = importlib.util.spec_from_file_location("file_translation_progress", mod_file_path)
file_translation_progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(file_translation_progress)


def added_files(path):
    for line in svn_status(path):
        line = line.decode('utf-8')
        # fn
        yield line[8:].rstrip()


def difference(fn):
    added = -1
    deleted = -1
    for line in svn_diff(fn):
        line = line.decode('utf-8')
        if line.startswith('+'):
            added += 1
        if line.startswith('-') and ('-msgstr ""' not in line):
            deleted += 1
    return added, deleted


def file_message(fn, args_path):
    diff = difference(fn)
    report = file_translation_progress.parse_file(fn)
    fn = fn[len(args_path) + len("LC_MESSAGES") + 2:]
    if diff[0] > diff[1]:  # something has appended
        done = report[1] / report[0]
        return 'Translated {:.0%} of {1}'.format(done, fn)
    size = 'Minor' if diff[0] < 20 else 'Major'
    return '{0} changes in {1}'.format(size, fn)


def svn_status(path):
    return exec_command(["status", path])


def svn_diff(fn):
    return exec_command(["diff", "--non-interactive", fn])


def svn_commit(path, message):
    return exec_command(["commit", path, "-m", '"' + message + '"'])


def exec_command(cmd_args):
    cmd = ['svn']
    cmd.extend(cmd_args)
    try:
        output = subprocess.check_output(cmd)
    except OSError as err:
        print("svn", cmd_args[0], "error:", err)
    except ValueError as err:
        print("svn", cmd_args[0], "error:", err)
    except Exception as err:
        print("svn", cmd_args[0], "unexpected error:", err)
    else:
        return output.splitlines()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        usage=__doc__
    )

    parser.add_argument(
        "-s", "--suffix",
        dest="suffix",
        default="",
        help="A suffix for the commit message",
        required=False,
    )

    parser.add_argument(
        "-p", "--prefix",
        dest="prefix",
        default="",
        help="A prefix for the commit message",
        required=False,
    )

    parser.add_argument(
        "path",
        help="directory containing .svn dirs",
        metavar="PATH"
    )

    args = parser.parse_args()
    if svn_status(args.path) == []:
        print('Nothing to do.')
        return
    message = args.prefix
    for fn in added_files(args.path):
        message += file_message(fn, args.path) + '; '
    message += args.suffix
    print('Committing with message: ' + message)
    print(''.join(svn_commit(args.path, message)))


if __name__ == "__main__":
    main()
