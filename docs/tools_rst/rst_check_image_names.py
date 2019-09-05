#!/usr/bin/env python3
# Apache License, Version 2.0
# <pep8 compliant>

"""
This utility checks naming conventions (Blender specific).
"""
import os
import sys
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


def print_title_multiline(title, underline="="):
    print(
        '\n' +
        title.upper() + '\n' +
        (underline * max(len(l) for l in title.splitlines()))
    )


# -----------------------------------------------------------------------------
# Global Variables

# .. |SomeID| image:: /images/some_image.png
# .. image:: /images/some_image.png
# .. figure:: /images/some_image.png
#
# note: no checks for commented text currently.
# groups: (1) ID, (2) image name, (3) dot + img. extension
image_regex = re.compile(
    r"\.\.\s+"
    # |SomeID|  (optional)
    "(?:\|([a-zA-Z0-9\-_]+)\|\s+)?"
    # figure/image::
    "(?:figure|image)\:\:\s+"
    # image path
    "/images/(.*?)(\.(?:png|gif|jpg|svg))",
    re.MULTILINE
)


# -----------------------------------------------------------------------------
# Find Bad Image Names


def check_image_names(fn, data_src, name_data):
    """
    Complain if the image name doesn't matches the file name
    """

    def compare_image_name(file_derive, record):
        """
        image name: image path[file path + file name] + image ID
        """
        # exclude icon library from rule
        if record["image_name"].startswith("icons_"):
            name_data["icon"].append(record)
        else:
            path_match = re.match(file_derive, record["image_name"])

            if path_match:
                if file_derive == record["image_name"]:
                    name_data["no_id"].append(record)
                else:
                    imgid = re.sub(file_derive + '_', "", record["image_name"])
                    contains_underscore = re.search(r"_", imgid)

                    if contains_underscore:
                        name_data["path_us"].append(record)
                    else:
                        name_data["ok"].append(record)
            else:
                name_data["path"].append(record)
        return None

    def derive_image_name(locpath):
        # derive image path from file path and name
        file_derive = re.sub(r"_", "-", locpath)
        file_derive = re.sub(r"/", "_", file_derive)
        file_derive = re.sub(r"\.rst", "", file_derive)
        return file_derive

    fn = fn.replace("\\", "/")
    locpath = fn[len(RST_DIR):]
    for lineno, line in enumerate(data_src.splitlines()):
        linematch = re.search(image_regex, line)
        if linematch:
            record = dict()
            record["filepath"] = locpath
            record["lineno"] = lineno
            record["image_name"] = linematch.group(2)
            record["image_ext"] = linematch.group(3).lower()
            file_derive = derive_image_name(locpath)
            record["file_derive"] = file_derive
            compare_image_name(file_derive, record)

    return None


def check_image_names_report(name_data):
    """
    Processes and then output the results of the image name check
    """

    name_report = {
        "icon": [],
        "ok": [],
        "no_id": [],
        "path_us": [],
        "path": [],
        "multi_ok": [],
        "multi_no": [],
        "multi_path": [],
    }

    def check_multi_used():
        """
        When an image is used on multiple pages checks if the image name matches the file path and name once.
        """
        found = False
        multi = False
        for keyprime, listprime in name_data.items():
            for ent in listprime:
                if keyprime == "icon" or keyprime == "ok":
                    name_report[keyprime].append(ent)
                else:
                    # recursively loop over the list
                    for keyrec, listrec in name_data.items():
                        for rec in listrec:
                            if (
                                    ent["image_ext"] == rec["image_ext"] and
                                    ent["image_name"] == rec["image_name"] and
                                    ent["filepath"] != rec["filepath"]
                            ):
                                if keyrec == "ok":
                                    name_report["multi_ok"].append(ent)
                                    found = True
                                    break
                                if keyprime == "no_id":
                                    name_report["multi_no"].append(ent)
                                    found = True
                                    break
                                else:
                                    multi = True
                                    # positive could be past this point continue search
                        if found:
                            break
                    if not found:
                        if multi:
                            name_report["multi_path"].append(ent)
                        else:
                            name_report[keyprime].append(ent)
                multi = False
                found = False

    check_multi_used()

    messages = {
        "no_id": "without an ID:",
        "path_us": "with a wrong path or\nname contains an underscore:",
        "path": "with a wrong path:",
        "multi_no": "without an ID and\nused on multiple pages:",
        "multi_path": "with a wrong path and\nused on multiple pages:"
    }

    for id in messages:
        if len(name_report[id]) != 0:
            print_title_multiline("List of images " + messages[id])
            for ent in name_report[id]:
                print(ent["filepath"] + ":" + str(ent["lineno"] + 1) + " " + ent["image_name"] + ent["image_ext"])
                print("   Should be: " + ent["file_derive"])


def main():
    if "--help" in sys.argv:
        print(__doc__)
        sys.exit(0)

    # Collect info while iterating over the files.
    name_data = {
        "icon": [],
        "ok": [],
        "no_id": [],
        "path_us": [],
        "path": [],
    }

    for fn in files_recursive(RST_DIR, ext_test=".rst"):
        with open(fn, "r", encoding="utf-8") as f:
            data_src = f.read()
            check_image_names(fn, data_src, name_data)
    check_image_names_report(name_data)


if __name__ == "__main__":
    main()
