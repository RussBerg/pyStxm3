#!/usr/bin/env python3
# Apache License, Version 2.0
# <pep8 compliant>

# DEVELOPER NOTE:
#
# This script should be cleaned up and is more of grab-back of functions
# which can be useful for maintenance.
#
# Not a general command line tools for general use.
#
# While it's not to bad to keep it for now, consider changing how this is exposed.
# ~ ideasman42

import os
# if you want to operate on a subdir, e.g: "render"
SUBDIR = ""
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
RST_DIR = os.path.normpath(os.path.join(CURRENT_DIR, "..", "manual", SUBDIR))


def rst_files(path):
    for dirpath, dirnames, filenames in os.walk(path):
        if dirpath.startswith("."):
            continue

        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext.lower() == ".rst":
                yield os.path.join(dirpath, filename)


def main():
    for fn in rst_files(RST_DIR):
        with open(fn, "r", encoding="utf-8") as f:
            data_src = f.read()
            data_dst = operation(fn, data_src)

        if data_dst is None or (data_src == data_dst):
            continue

        with open(fn, "w", encoding="utf-8") as f:
            data_src = f.write(data_dst)


# ---------------------------------------
# Custom Code - do whatever you like here
# (only commit reusable examples).
#
# Functions take a (file_name, file_contents)
# returns the new file_contents (or None to skip the operation)


def preset_strip_trailing_space(fn, data_src):
    """
    Strips trailing white-space from all RST files.
    """

    lines = data_src.split("\n")

    for i, l in enumerate(lines):
        l = l.rstrip()
        lines[i] = l

    data_dst = "\n".join(lines)

    # 2 empty lines max
    data_dst = data_dst.replace("\n\n\n\n", "\n\n\n")
    return data_dst


def preset_find_and_replace(fn, data_src):
    """
    Simply finds and replaces text
    """
    # handy for replacing exact words
    use_whole_words = False

    find_replace_pairs = (
        ("−", "-"),
    )

    if use_whole_words:
        import re
        find_replace_pairs_re = [
            (re.compile("\b" + src + "\b"), dst)
            for src, dst in find_replace_pairs
        ]

    lines = data_src.split("\n")

    for i, l in enumerate(lines):
        old_l = l
        do_replace = False
        if use_whole_words:
            for src_re, dst in find_replace_pairs_re:
                l = re.sub(src_re, dst, l)
        else:
            for src, dst in find_replace_pairs:
                l = l.replace(src, dst)

        if old_l != l:
            lines[i] = l
            # print ("Replaced:", old_l, "\n    With:", l, "\n")

    data_dst = "\n".join(lines)
    return data_dst


def preset_replace_table(fn, data_src):
    """
    Replace ASCII tables with list-table.
    """

    lines = data_src.split("\n")

    is_table = -1
    tot_row = -1

    def is_div(l):
        return l.startswith("+") and l.endswith("+") and set(l) == {"+", "-"}

    i = 0
    while i < len(lines):
        l = lines[i]
        l = l.strip()
        if is_table == -1:
            if is_div(l):
                is_table = i
                tot_row = l.count("+") - 1
        else:
            if l.startswith(("+", "|")) and l.endswith(("+", "|")):
                pass
            else:
                # table is [is_table : i]
                table_content = []

                def add_col():
                    table_content.append([[] for k in range(tot_row)])

                add_col()
                tot_indent = len(lines[is_table]) - len(lines[is_table].lstrip())
                for j in range(is_table + 1, i - 1):
                    l = lines[j].strip()
                    # print(l)
                    if is_div(l):
                        add_col()
                    else:
                        for ir, r in enumerate(l[1:-1].split("|")):
                            table_content[-1][ir].append(r.rstrip())

                # optionally complain about single cell-tables
                if tot_row == 1 and len(table_content) == 1:
                    raise Exception(fn + ":" + str(i + 1))

                indent = " " * tot_indent
                indent_dot = indent + (" " * 3)
                indent_item = indent_dot + (" " * 4)

                list_table = [indent + ".. list-table::", ""]

                for col in table_content:
                    for ir in range(tot_row):
                        if ir >= len(col):
                            data = [""]
                        else:
                            data = col[ir]
                            if not data:
                                data = [""]

                        if ir == 0:
                            list_table.append(indent_dot + "* - " + data[0])
                        else:
                            list_table.append(indent_dot + "  - " + data[0])

                        for d in data[1:]:
                            list_table.append(indent_item + d)
                        # figures need blank space between bullets, for now just add for all,
                        # can remove manually later if we want.
                        list_table.append("")

                # ensure newlines before & after
                list_table = [""] + [lt.rstrip() for lt in list_table] + [""]

                # no double-blank lines
                li = 1
                while li < len(list_table):
                    if list_table[li] == "":
                        if list_table[li - 1] == "":
                            del list_table[li]
                            li -= 1
                            continue
                    li += 1

                if 1:
                    lines[is_table - 1:i] = list_table
                    i = is_table
                    is_table = -1

        i += 1

    data_dst = "\n".join(lines)

    # 2 empty lines max
    data_dst = data_dst.replace("\n\n\n\n", "\n\n\n")
    return data_dst


def preset_wrap_lines(fn, data_src):
    """
    Wrap long lines, attempt to split on delimiters.
    """

    # ideal margin
    MARGIN_TARGET = 75
    # max allowable margin
    MARGIN_MAX = 118
    # ignore lines shorter
    MARGIN_MIN = 20

    lines = data_src.split("\n")

    i = 0
    while i < len(lines):
        l_orig = lines[i].rstrip()
        l = l_orig.lstrip()
        if len(l_orig) >= MARGIN_MAX:

            # ignore directives since their formatting cant always be split
            if l.lstrip(" *-").startswith(".. "):
                print("Ignoring %s:%d: " % (fn, i + 1))
                print(l_orig)
                i += 1
                continue

            if l.startswith("#. "):
                indent = 3
            elif l.startswith("- "):
                indent = 2
            elif l.startswith("| "):
                indent = 2
            else:
                indent = 0
            indent += len(l_orig) - len(l)

            index_best = -1
            index_weight_best = 1000000.0
            c_best = ""

            # now attempt to split the line
            # lower values are weighted to wrap
            for c, w in (
                    (". ", 0.2),
                    ("? ", 0.2),
                    ("! ", 0.2),

                    ("; ", 0.5),
                    (", ", 1.0),
                    (" (", 0.75),
                    (") ", 0.75),
                    ("- ", 2.0),
                    (" :", 2.0),
                    # last resort
                    (" ", 10.0),
            ):

                index = l_orig[:(MARGIN_TARGET + MARGIN_MAX) // 2].rfind(c)
                if index == -1:
                    index = l_orig[:MARGIN_MAX - 1].rfind(c)

                if index > MARGIN_MIN and index < MARGIN_MAX:
                    # either align with the target length or split the line in half
                    index_weight = min(abs(index - MARGIN_TARGET),
                                       abs(index - (len(l_orig) // 2)))
                    index_weight = (index_weight + 1) * w
                    if index_weight < index_weight_best:
                        index_weight_best = index_weight
                        index_best = index
                        c_best = c

            if index_best != -1:
                index_best += 1
                lines[i:i + 1] = [l_orig[:index_best].rstrip(), (indent * " ") + l_orig[index_best:].lstrip()]
                i -= 1
            else:
                print("Not found %s:%d: " % (fn, i + 1))
                print(l_orig)

        # lines[i] = l
        i += 1

    data_dst = "\n".join(lines)
    return data_dst


def preset_help(operations):
    """
    Shows help text.
    """
    import textwrap
    print("Operations:\n")
    for op, op_arg, op_fn in operations:
        print("%s:" % op_arg)
        print(textwrap.indent(op_fn.__doc__.strip(), "  "))
        print()


def operation_from_args():
    import sys
    namespace = globals()

    operations = []
    for op, op_fn in namespace.items():
        if op.startswith("preset_"):
            if callable(op_fn):
                op_arg = "--%s" % op[7:]
                operations.append((op, op_arg, op_fn))
    operations.sort()

    operations_map = {op_arg: (op, op_fn) for (op, op_arg, op_fn) in operations}

    operation = None
    for arg in sys.argv:
        if arg.startswith("--"):
            op, op_fn = operations_map.get(arg, (None, None))
            if op is not None:
                operation = op_fn
                break
            else:
                print(
                    "Argument '%s' not in %s" %
                    (arg, " ".join(sorted(operations_map.keys()))))
                return None

    if operation is None:
        print("No command passed")
    elif operation is preset_help:
        preset_help(operations)
        operation = None
    return operation


# define the operation to call
# operation = preset_strip_trailing_space
operation = operation_from_args()

if __name__ == "__main__":
    if operation is not None:
        main()
