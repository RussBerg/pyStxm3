#!/usr/bin/env python3
# Apache License, Version 2.0
# <pep8 compliant>

"""
This utility checks image paths:

- Are correct and exist.
- Are all used.
"""

import sys
import os
import re


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
# Global Variables

# .. |SomeID| image:: /images/some_image.png
# .. image:: /images/some_image.png
# .. figure:: /images/some_image.png
#
# note: no checks for commented text currently.
# groups: (1) ID, (2) image name & extension

image_regex = re.compile(
    r"\.\.\s+"
    # |SomeID|  (optional)
    "(?:\|([a-zA-Z0-9\-_]+)\|\s+)?"
    # figure/image::
    "(?:figure|image)\:\:\s+"
    # image path
    "/images/(.*?\.(?:png|gif|jpg|svg))",
    re.MULTILINE
)

# -----------------------------------------------------------------------------
# Find Unused/Missing Images


def rst_images(fn, data_src):
    for match in re.finditer(image_regex, data_src):
        yield match.group(2)


def rst_files_report(img_refs):
    """
    Outputs the results of unused/missing images
    """
    imgpath = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "manual", "images"))
    img_files_set = set([f for f in os.listdir(imgpath)])
    img_refs_set = set(img_refs)

    print_title("List of unused images:")
    for fn in sorted(img_files_set - img_refs_set):
        print(" svn rm --force manual/images/%s" % fn)

    print_title("List of missing images:")
    for fn in sorted(img_refs_set - img_files_set):
        print(fn)

    if len(img_files_set) != len(set([fn.lower() for fn in img_files_set])):
        img_files_set_lower = set()
        print_title("List of case-colliding images:")
        for fn in sort(img_files_set):
            fn_lower = fn.lower()
            if fn_lower in img_files_set_lower:
                print(fn)
            img_files_set_lower.add(fn_lower)


def main():
    if "--help" in sys.argv:
        print(__doc__)
        sys.exit(0)

    rst_file_list = []
    for fn in files_recursive(RST_DIR, ext_test=".rst"):
        with open(fn, "r", encoding="utf-8") as f:
            rst_file_list.extend(rst_images(fn, f.read()))
    rst_files_report(rst_file_list)


if __name__ == "__main__":
    main()
