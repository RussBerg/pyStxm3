#!/usr/bin/env python3
# Apache License, Version 2.0
# <pep8 compliant>

import os
import io
import argparse

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.normpath(os.path.join(CURRENT_DIR, "..", "manual"))
EDIT_FILE = os.path.join(CURRENT_DIR, "broken_doc_links.txt")
ROLE = ":doc:"

to_print = [["#   Location of broken link:", "Line:", "    Link Target:"]]  # list of lists as: [file_with_link, path]


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def rst_files(path):
    for dirpath, dirnames, filenames in os.walk(path):
        if dirpath.startswith("."):
            continue

        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext.lower() == ".rst":
                yield os.path.join(dirpath, filename)


def get_broken_doc_links(fname, anchors='INCLUDE', target_chapter=''):
    with open(fname, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # First get all paths
    paths = []
    for i, l in enumerate(lines):
        if ROLE in l:
            links = l.split(ROLE + "`")
            del links[0]  # first split item will be "blah blah :doc:`" and not a link path
            for path in links:
                if "`" in path:
                    path = path.split("`")[0]
                    if "<" in path and path.endswith(">"):
                        path = path.split("<")[-1][:-1]  # turns "Text <path>" into "path"
                    lfname = path.split('/')[-1]
                    do_append = False
                    if anchors in ['ONLY', 'INCLUDE'] and '#' in lfname:
                        do_append = True
                    elif anchors == 'INCLUDE' or (anchors == 'IGNORE' and '#' not in lfname):
                        do_append = True

                    if do_append:
                        if path.startswith("/" + target_chapter):
                            paths.append([path, str(i + 1) + ' '])  # using i+1 so line number starts from 1

    # Then check validity
    for path in paths:
        line = path[1]
        path = path[0]
        fullp = ROOT_DIR + path + ".rst"
        if not os.path.exists(fullp):
            to_print.append([fname.replace(ROOT_DIR, ""), line, path])


def check_links(sc='', a='INCLUDE', tc=''):
    # Fetch broken links
    for fn in rst_files(ROOT_DIR):
        src = fn.replace(ROOT_DIR, '').replace('\\', '/')
        if src.startswith("/" + sc):
            get_broken_doc_links(fn, anchors=a, target_chapter=tc)

    # Format it nicely
    out = []
    pmaxlen = 0  # max string length of path
    for l in to_print:
        llen = len(l[0])
        if llen > pmaxlen:
            pmaxlen = llen
    lmaxlen = 0  # max string length of line number
    for l in to_print:
        llen = len(l[1])
        if llen > lmaxlen:
            lmaxlen = llen
    for l in to_print:
        p0 = l[0] + (' ' * (pmaxlen - len(l[0])))  # pad with spaces on right
        p1 = (' ' * (lmaxlen - len(l[1]))) + l[1]  # pad with spaces on left
        out.append(' '.join((p0, "::", p1, "::", l[2])))

    # Write to file user will edit, and to file that will be compared to.
    with open(EDIT_FILE, "w") as f:
        f.write('\n'.join(out))
    with open(EDIT_FILE + ".orig", "w") as f:
        f.write('\n'.join(out))


def fix_links():
    with open(EDIT_FILE, "r") as f:
        lines = f.read().split('\n')
    with open(EDIT_FILE + ".orig", "r") as f:
        lines_orig = f.read().split('\n')

    for i, line in enumerate(lines):
        line_orig = lines_orig[i]
        if not line.startswith('#'):
            if line != line_orig:
                path, lineno, target = line.split('::')
                path = path.strip()
                lineno = int(lineno.strip()) - 1  # line number starting from 0
                target = target.strip()
                target_orig = line_orig.split('::')[-1].strip()
                fullp = ROOT_DIR + path
                with io.open(fullp, "r", encoding="utf-8", newline='') as f:
                    # newline is empty str to ensure that the original line ending is not changed
                    flines = f.readlines()
                lorig = flines[lineno]
                flines[lineno] = flines[lineno].replace('<' + target_orig + '>', '<' + target + '>')
                flines[lineno] = flines[lineno].replace('`' + target_orig + '`', '`' + target + '`')
                print(lorig + flines[lineno])
                with io.open(fullp, "w", encoding="utf-8", newline='') as f:
                    f.write(''.join(flines))


def auto_fix_links():
    with open(EDIT_FILE, "r") as f:
        lines = f.read().split('\n')
    with open(EDIT_FILE + ".orig", "r") as f:
        lines_orig = f.read().split('\n')

    success = 0
    total = 0
    for i, line in enumerate(lines):
        line_orig = lines_orig[i]
        if not line.startswith('#'):
            total += 1
            if line == line_orig:  # only check lines that the user has not changed
                path, lineno, target = line.split('::')
                path = path.strip()
                lineno = int(lineno.strip()) - 1  # line number starting from 0
                target = target.strip()

                # check if index exists
                fix = ""
                possibilities = [target + "/index",
                                 target + "/introduction"]
                for p in possibilities:
                    if os.path.exists(ROOT_DIR + p + ".rst"):
                        fix = p
                        success += 1
                        break

                if fix:
                    fullp = ROOT_DIR + path
                    with io.open(fullp, "r", encoding="utf-8", newline='') as f:
                        flines = f.readlines()
                    lorig = flines[lineno]
                    flines[lineno] = flines[lineno].replace('<' + target + '>', '<' + fix + '>')
                    flines[lineno] = flines[lineno].replace('`' + target + '`', '`' + fix + '`')
                    print(lorig + flines[lineno])
                    with io.open(fullp, "w", encoding="utf-8", newline='') as f:
                        f.write(''.join(flines))

    if success == total:
        print("\nSuccessfully fixed all links automatically!")
    elif success > 0:
        print("\nSuccessfully fixed %s links automatically, run this script again to try manually." % success)
    else:
        print("Failed to fix any links automatically :(")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "An interactive script that can be used to manually "
            "or automatically fix broken internal links.\n\n"
            "Basic usage:\n"
            "- Run \"fix_internal_links.py\"\n"
            "- Edit the right column in the text file \"broken_doc_links.txt\"\n"
            "- Enter \"done\" at the prompt, all links will then be updated "
            "as you changed them in the text file."),
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '-a', '--auto',
        action="store_true",
        help="Skip the user input process and\nautomatically try to fix links.",
    )
    parser.add_argument(
        '-ia', '--ignoreanchors',
        action="store_true",
        help="Ignore links with html anchors at the end.",
    )
    parser.add_argument(
        '-oa', '--onlyanchors',
        action="store_true",
        help="Only check links with html anchors at the end.",
    )
    parser.add_argument(
        '-sc', '--sourcechapter',
        help="Only check files in this chapter.",
    )
    parser.add_argument(
        '-tc', '--targetchapter',
        help="Only check for links pointing at this chapter.",
    )

    args = parser.parse_args()
    source_chapter = ''
    target_chapter = ''
    anchors = 'INCLUDE'
    if args.sourcechapter:
        source_chapter = args.sourcechapter
    if args.targetchapter:
        target_chapter = args.targetchapter
    if args.ignoreanchors:
        anchors = 'IGNORE'
    elif args.onlyanchors:
        anchors = 'ONLY'

    if args.auto:
        check_links(source_chapter, anchors, target_chapter)
        auto_fix_links()
    else:
        print("Checking for broken links...")
        check_links(source_chapter, anchors, target_chapter)
        num_broken = len(to_print) - 1
        clear_console()
        if num_broken > 0:
            print("Found: " + str(num_broken) + " broken links\n\n"
                  "Now edit the link targets in the right column of broken_doc_links.txt (next to this script)\n\n"
                  "When finished, type \"done\" below, or anything else to cancel.\n\n"
                  "You may also type \"auto\" to attempt to fix the links automatically.\n")
            response = input("> ")
            if response == "done":
                fix_links()
            elif response == "auto":
                clear_console()
                print("Attempting to fix links automatically...")
                auto_fix_links()
            else:
                print("Canceling")
        else:
            print("No broken links found! Yay!")

    # Delete broken_doc_links.txt
    try:
        os.remove(EDIT_FILE)
        os.remove(EDIT_FILE + ".orig")
    except BaseException as ex:
        # in case file is locked
        print("WARNING: Unable to delete " + EDIT_FILE + " error: " + str(ex) + "\n"
              "Make sure this file (and its \".orig\" duplicate) is deleted before committing.")


if __name__ == "__main__":
    main()
