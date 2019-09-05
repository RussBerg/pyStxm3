#!/usr/bin/env python3
# Apache License, Version 2.0

"""
This tool optimizes images if their size can be improved.
Currently only performs lossless compression on PNG images using 'pngcrush'.
"""

import os
BASEDIR = os.path.abspath(os.path.dirname(__file__))

VERBOSE = False

# Ignore result unless it's at least 7.5% improvement
FACTOR = 0.075

def find_vcs_root(test, dirs=(".svn", ".git"), default=None):
    import os
    prev, test = None, os.path.abspath(test)
    while prev != test:
        if any(os.path.isdir(os.path.join(test, d)) for d in dirs):
            return test
        prev, test = test, os.path.abspath(os.path.join(test, os.pardir))
    return default


def run(cmd):
    if VERBOSE:
        print(">>> ", cmd)

    import subprocess
    proc = subprocess.Popen(cmd, shell=False)
    proc.wait()
    return proc.returncode


def files_recursive(path, ext_test):
    for dirpath, dirnames, filenames in os.walk(path):
        if dirpath.startswith((".", "_")):
            continue

        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext.lower().endswith(ext_test):
                yield os.path.join(dirpath, filename)


def main():
    vcs_dir = find_vcs_root(BASEDIR)
    print(vcs_dir)
    if vcs_dir is None:
        print("Can't find version directory, aborting!")
        return

    TMP_NAME = "out.png"
    for f in sorted(files_recursive(vcs_dir, ".png")):

        # ensure we never used a stale file
        if os.path.exists(TMP_NAME):
            os.remove(TMP_NAME)

        if os.path.exists(TMP_NAME):
            print("Error removing %r" % TMP_NAME)

        cmd = [
            "pngcrush",
            "-brute",
            "-reduce",
            "-m", "7",
            f,
            TMP_NAME,
        ]

        run(cmd)

        if os.path.exists(TMP_NAME):
            s = os.path.getsize(f)
            d = os.path.getsize(TMP_NAME)

            if d != 0:
                fac = d / s
                if fac < (1.0 - FACTOR):
                    print("Replacing: %r" % f)
                    os.remove(f)
                    os.rename(TMP_NAME, f)

    if os.path.exists(TMP_NAME):
        os.remove(TMP_NAME)


if __name__ == "__main__":
    main()
