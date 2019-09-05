#!/usr/bin/env python3
# Apache License, Version 2.0
# <pep8 compliant>
"""
This tool checks for unused locale files,
printing out the command to remove them (if any).
"""

import os
import sys


# if you want to operate on a subdir, e.g: "render"
SUBDIR = ""
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.normpath(os.path.join(CURRENT_DIR, ".."))
RST_DIR = os.path.join(ROOT_DIR, "manual", SUBDIR)
LOCALE_DIR = os.path.join(ROOT_DIR, "locale")

# -----------------------------------------------------------------------------
# Common Utilities


def files_recursive(path, ext_test):
    for dirpath, dirnames, filenames in os.walk(path):
        if dirpath.startswith("."):
            continue

        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext.lower().endswith(ext_test):
                yield os.path.join(dirpath, filename)


def print_title(title, underline="="):
    print(f"\n{title.upper()}\n{len(title) * underline}")


# -----------------------------------------------------------------------------
# Locale Checks

def warn_locale():
    """
    Check for stale PO files.
    """
    files_rst = list(files_recursive(RST_DIR, ext_test=".rst"))
    files_po = list(files_recursive(LOCALE_DIR, ext_test=".po"))

    print_title("List of unused locale:")

    if files_po:
        print(" cd locale")
        for f in files_po:
            # strip LOCALE_DIR from start
            f_sub = f[len(LOCALE_DIR) + 1:-2] + "rst"
            # strip 'fr/LC_MESSAGES'
            f_sub = os.sep.join(f_sub.split(os.sep)[2:])
            f_po_as_rst = os.path.join(RST_DIR, f_sub)
            if not os.path.exists(f_po_as_rst):
                print(" svn rm --force %s" % f[len(LOCALE_DIR) + 1:])
        print(" cd ../")
    return 0


def main():
    if "--help" in sys.argv:
        print(__doc__)
        sys.exit(0)

    return warn_locale()


if __name__ == "__main__":
    main()
