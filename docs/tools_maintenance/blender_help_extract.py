#!/usr/bin/env python3
# Apache License, Version 2.0
# <pep8 compliant>

import os
import re

# This script extracts the '--help' message from Blender's source code,
# using primitive regex parsing.
#
# e.g:
# python tools/blender_help_extract.py /src/blender/source/creator/creator_args.c manual/advanced/command_line/arguments.rst


def text_remove_comments(text):
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " "
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
        )
    return re.sub(pattern, replacer, text)


def text_join_lines(text):
    # return text.replace(",\n", ",")
    pattern = re.compile(
        '\s*,\n\s*',
        re.DOTALL | re.MULTILINE
        )
    return re.sub(pattern, ", ", text)


def text_expand_macros(text):
    # CB() macro
    def replacer_CB(match):
        return match.group(2) + "_doc, " + match.group(2)

    pattern_CB = re.compile(
        r'\b(CB)\s*\(([^\,]+)\)',
        re.DOTALL | re.MULTILINE
        )

    # CB_EX() macro
    def replacer_CB_EX(match):
        return match.group(2) + "_doc_" + match.group(3) + ", " + match.group(2)

    pattern_CB_EX = re.compile(
        r'\b(CB_EX)\s*\(([^\,]+),\s*([^\)]+)\)',
        re.DOTALL | re.MULTILINE
        )

    # STRINGIFY_ARG() macro
    def replacer_STRINGIFY_ARG(match):
        return "\"``" + match.group(2) + "``\""

    pattern_STRINGIFY_ARG = re.compile(
        r'\b(STRINGIFY_ARG)\s*\(([^\)]+)\)',
        re.DOTALL | re.MULTILINE
        )

    text = re.sub(pattern_CB, replacer_CB, text)
    text = re.sub(pattern_CB_EX, replacer_CB_EX, text)
    text = re.sub(pattern_STRINGIFY_ARG, replacer_STRINGIFY_ARG, text)

    return text


def text_extract_args(text):

    args = {}
    # use replace to scan (misuse!)

    def replacer(match):
        fn = match.group(1)
        s = match.group(2)

        # remove first 2 args
        s = s.split(',', 2)[-1]
        # remove last 2 args
        s = s.rsplit(',', 2)[0]

        if fn == "BLI_argsAdd":
            # get first 2 args
            arg_short, arg_long, s = [w.strip() for w in s.split(",", 2)]
        elif fn == "BLI_argsAddCase":
            # get first 2 args
            arg_short, _, arg_long, _, s = [w.strip() for w in s.split(",", 4)]
            del _
        else:
            # should never happen
            raise Exception("Bad function call %r" % fn)

        if arg_short == "NULL":
            arg_short = None
        else:
            arg_short = eval(arg_short, {})
        if arg_long == "NULL":
            arg_long = None
        else:
            arg_long = eval(arg_long, {})
        args[arg_short, arg_long] = s

        # print(arg_short, arg_long, s)

    pattern = re.compile(
        r'\b(BLI_argsAdd[Case]*)\s*\(((?:(?!\)\s*;).)*?)\)\s*;',
        re.DOTALL | re.MULTILINE
        )

    re.sub(pattern, replacer, text)
    return args


def text_extract_strings(text):
    strings = {}
    # use replace to scan (misuse!)

    text = (text
            ).replace(
            "PY_ENABLE_AUTO", " \" (default)\""
            ).replace(
            "PY_DISABLE_AUTO", " \"\""
            ).replace(
            "STRINGIFY(BLENDER_STARTUP_FILE)", "\"startup.blend\""
            ).replace(
            "STRINGIFY(BLENDER_MAX_THREADS)", "\"64\""
            )

    def replacer(match):
        var = match.group(1).strip()
        s = match.group(2)
        s = " ".join([w.strip() for w in s.split("\n")])
        s = eval(s, {})
        strings[var] = s

    pattern = re.compile(
        r'\bstatic\s+const\s+char\s+([A-Za-z0-9_]+)\[\]\s*=\s*((?:(?!"\s*;).)*?")\s*;',
        re.DOTALL | re.MULTILINE
        )

    re.sub(pattern, replacer, text)
    return strings


def text_extract_help(text, args, static_strings):
    func_id = 'static int arg_handle_print_help(int UNUSED(argc), const char **UNUSED(argv), void *data)\n'
    index_start = text.find(func_id)
    index_end = text.find("\texit(0);", index_start)
    # print(index_start, index_end)
    body = text[index_start + len(func_id):index_end]
    body = [l for l in body.split("\n") if not l.strip().startswith("#")]
    body = [l.strip() for l in body]
    body = [l for l in body if l]

    # args dicts
    args_short = {}
    args_long = {}
    args_used = set()

    for (arg_short, arg_long), value in args.items():
        if arg_short is not None:
            args_short[arg_short] = (arg_short, arg_long), value
        if arg_long is not None:
            args_long[arg_long] = (arg_short, arg_long), value
    # there is some overlap in short/long args, second pass to fix
    # by assigning long-only
    for (arg_short, arg_long), value in args.items():
        if arg_short is not None:
            if arg_long is None:
                args_short[arg_short] = (arg_short, arg_long), value

    def args_get(arg):
        value = args_long.get(arg)
        if value is None:
            value = args_short.get(arg)
            if value is None:
                raise Exception("Can't find %r" % arg)
        return value

    text_rst = []

    # execute the code!
    other_vars = {
        "BLEND_VERSION_STRING_FMT": "Blender |BLENDER_VERSION| ",
        }


    def write_arg(arg):
        (arg_short, arg_long), arg_text = args_get(arg)
        args_used.add((arg_short, arg_long))

        # replacement table
        arg_text = re.sub("\"\s*STRINGIFY_ARG\s*\(([a-zA-Z0-9_]+)\)\"", r"``\1``", arg_text)
        arg_text = arg_text.replace('" STRINGIFY(BLENDER_MAX_THREADS) "', "64")
        arg_text = arg_text.replace('" STRINGIFY(BLENDER_STARTUP_FILE) "', "startup.blend")
        arg_text = arg_text.replace('" PY_ENABLE_AUTO', '\"')
        arg_text = arg_text.replace('" PY_DISABLE_AUTO', ', (default).\"')

        # print(arg_text)
        arg_text = eval(arg_text, static_strings)
        arg_text = arg_text.replace("\t", "   ")

        text_rst.append("``" + "``, ``".join([w for w in (arg_short, arg_long) if w is not None]) + "`` ")
        text_rst.append(arg_text + "\n")


    for l in body:
        if l.startswith("printf"):
            l = eval(l[7:].strip("();"), other_vars)
            if l.lstrip() == l and l.strip("\n").endswith(":"):
                l = l.strip(":\n")
                l = "\n\n" + l + "\n" + len(l) * '=' + "\n\n"
            else:
                l = l.replace("\t", "   ")

            text_rst.append(l)
        elif l.startswith("BLI_argsPrintArgDoc("):
            arg = l.split(",")[-1].strip(");\n")
            arg = eval(arg, {})
            write_arg(arg)
        elif l.startswith("BLI_argsPrintOtherDoc("):
            items = list(args.items())
            # sort as strings since we cant order (None <> str)
            items.sort(key=lambda i: str(i[0]))
            for key, value in items:
                if key not in args_used:
                    write_arg(key[0] or key[1])

    text_rst = "".join(text_rst)

    # not essential, but nice to have <word> as ``<word>``
    text_rst = re.sub(r"([\+\-]*<[a-zA-Z0-9\(\)_\-]+>)", r"``\1``", text_rst)

    # ------
    # Post process (formatting)
    # text_rst = re.split(r"\\n|[()]", text_rst)
    text_rst = text_rst.splitlines()

    for i, l in enumerate(text_rst):
        # detect env var list
        l_strip = l.lstrip()
        if l_strip.startswith("$"):
            l_strip, l_tail = l_strip.lstrip("$").split(" ", 1)
            if l_strip.isupper():
                l = ":%s: %s" % (l_strip, l_tail)
            del l_tail
        elif l_strip.startswith("#"):
            indent = l[:len(l) - len(l_strip)]
            l = "\n" + indent + ".. code-block:: sh\n\n" + indent + "   " + l.lstrip("# ") + "\n"
        else:
            # use "'" as "``", except when used as plural, e.g. "Python's"
            l = re.sub("(?<![a-z])'|'(?![st])", "``", l)
        del l_strip

        text_rst[i] = l.rstrip(" ")

    # finally, make switches literal if they proceed literal args
    # or have their own line.
    # -a ``<b>`` ... --> ``-a`` ``<b>`` 
    # and...
    # -a --> ``-a``
    for i, l in enumerate(text_rst):
        if l.lstrip().startswith("-"):
            l = re.sub(r"(\s+)(\-[a-z])(\s+``)", r"\1``\2``\3", l)
            l = re.sub(r"^(\s+)(\-[a-z])$", r"\1``\2``", l)
            text_rst[i] = l
    
    text_rst = [
        ".. DO NOT EDIT THIS FILE, GENERATED BY %r\n" % os.path.basename(__file__),
        "\n"
        "   CHANGES TO THIS FILE MUST BE MADE IN BLENDER'S SOURCE CODE, SEE:\n"
        "   https://developer.blender.org/diffusion/B/browse/master/source/creator/creator_args.c\n"
        "\n"
        "**********************\n"
        "Command Line Arguments\n"
        "**********************\n"
        "\n"
    ] + text_rst

    text_rst = "\n".join(text_rst)
    text_rst = text_rst.replace("\n\n\n\n", "\n\n\n")

    return text_rst


def main():
    import sys
    source_file = sys.argv[-2]
    output_file = sys.argv[-1]

    if not source_file.endswith("creator_args.c"):
        print("Expected 'creator_args.c' to be passed as the second last argument")
        return
    if not output_file.endswith(".rst"):
        print("Expected an '.rst' file to be passed as the last argument")
        return

    with open(source_file, 'r') as f:
        text = f.read()

    text = text_remove_comments(text)
    # join ',\n' - function args split across lines.
    text = text_join_lines(text)
    # expand CB macros
    text = text_expand_macros(text)
    # first pass, extract 'BLI_argsAdd'

    args = text_extract_args(text)

    static_strings = text_extract_strings(text)

    text_rst = text_extract_help(text, args, static_strings)

    with open(output_file, 'w') as f:
        f.write(text_rst)

if __name__ == "__main__":
    main()
