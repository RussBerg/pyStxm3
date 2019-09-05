#!/usr/bin/env python3
# Apache License, Version 2.0
# <pep8 compliant>

"""
Remap RST title levels
"""


def title_level_edit(fn, data_src, level_add):

    # as defined by
    # https://docs.python.org/devguide/documenting.html
    #
    # note: include levels not found in Python docs
    # so we can bump up/down and still have a unique title char.
    title_chars = (
        '%',  # not from python docs!
        '#',
        '*',
        '=',
        '-',
        '^',
        '"',
        "'",  # not from python docs!
    )

    title_levels = {ch: i for i, ch in enumerate(title_chars)}

    def retitle(title, level_text, level):
        level_text = title_chars[level] * len(level_text)
        # print(title)
        # print(level_text)
        return title, level_text

    lines = data_src.split("\n")
    l_prev = None
    l_prev_prev = None

    for i in range(len(lines) - 1):
        l = lines[i]
        l = l.rstrip()

        # expect a blank line after the title
        if not lines[i + 1].rstrip():
            is_title = False
            if (l_prev_prev is not None):
                # 3 line title?
                if l_prev and l and (l == l_prev_prev):
                    level = title_levels.get(l[0], -1)
                    if level != -1 and l.count(l[0]) == len(l):

                        # adjust the current title level
                        level += level_add

                        title_new, level_text_new = retitle(l_prev, l, level)
                        lines[i - 2] = lines[i] = level_text_new
                        lines[i - 1] = title_new
                        is_title = True

            if (l_prev is not None) and not is_title:
                # 2 line title?
                if l_prev and l and (len(l) == len(l_prev)):
                    level = title_levels.get(l[0], -1)
                    if level != -1 and l.count(l[0]) == len(l):

                        # adjust the current title level
                        level += level_add

                        title_new, level_text_new = retitle(l_prev, l, level)
                        lines[i] = level_text_new
                        lines[i - 1] = title_new
                        is_title = True

        l_prev_prev = l_prev
        l_prev = l

    data_dst = "\n".join(lines)
    return data_dst


def create_argparse():
    import argparse

    usage_text = __doc__

    parser = argparse.ArgumentParser(
        prog="bam",
        description=usage_text,
    )

    parser.add_argument(
        dest="paths", nargs="*",
        help="Path(s) to operate on",
    )

    parser.add_argument(
        "-l", "--level", dest="level", metavar='LEVEL', required=True,
        default=1, type=int,
        help="The level to add/remove from the titles",
    )
    return parser


def main(argv=None):
    import sys
    import os

    if argv is None:
        argv = sys.argv[1:]

    parser = create_argparse()
    args = parser.parse_args(argv)

    for f in args.paths:
        if os.path.exists(f):
            with open(f, 'r', encoding='utf-8') as f_handle:
                data_src = f_handle.read()
            data_dst = title_level_edit(f, data_src, args.level)
            with open(f, 'w', encoding='utf-8') as f_handle:
                f_handle.write(data_dst)
        else:
            print("Path not found! $r" % f)


if __name__ == "__main__":
    main()
