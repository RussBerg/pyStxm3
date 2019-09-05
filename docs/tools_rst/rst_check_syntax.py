#!/usr/bin/env python3
# Apache License, Version 2.0
# <pep8 compliant>

import os
import sys
import re


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
    compile_regex(sys.argv[1:])

    for operation, operation_post in operations:
        for fn in rst_files(RST_DIR):
            with open(fn, "r", encoding="utf-8") as f:
                data_src = f.read()
                data_dst = operation(fn, data_src)

            if data_dst is None or (data_src == data_dst):
                continue

            with open(fn, "w", encoding="utf-8") as f:
                data_src = f.write(data_dst)

        if operation_post is not None:
            operation_post()


def compile_regex(args):
    if "--kbd" in args:
        compile_valid_kbd()


def warn_long_lines(fn, data_src):
    """
    Complain about long lines
    """
    lines = data_src.split("\n")
    limit = 118

    for i, l in enumerate(lines):
        if len(l) > limit:
            # rule out tables
            l_strip = l.strip()

            # ignore tables
            if l_strip.startswith("+") and l_strip.endswith(("+", "|")):
                continue
            # for long links which we can't avoid
            if l_strip.strip(",.- ").endswith("__"):
                continue
            if l_strip.startswith(".. parsed-literal:: "):
                continue
            if l_strip.startswith(".. figure:: "):
                continue

            print("%s:%d: long line %d" % (fn, i + 1, len(l)))

    return None


def warn_role_kbd(fn, data_src):
    """
    Report non-conforming uses of the :kbd: role.

    kbd editing regex:
    (\:kbd\:`[^`]*?)search-term([^`]*?`)
    \1replace-term\2

    """
    iter_kbd = warn_role_kbd.iter_kbd
    valid_kbd = warn_role_kbd.valid_kbd
    repeat_kbd = warn_role_kbd.repeat_kbd

    for lineno, line in enumerate(data_src.splitlines()):
        for m in re.finditer(iter_kbd, line):
            content = m.group(1)

            # chained (not pressed simultaneously): e.g. G X 5
            for k in content.split():
                if not re.match(valid_kbd, k) or re.search(repeat_kbd, k):
                    fn_rel = fn[len(RST_DIR) + 1:]
                    out = content
                    if content != k:
                        out += "| " + k
                    print(fn_rel + ":" + str(lineno + 1) + " '" + out + "' " + "invalid keyboard shortcut")

    return None


def compile_valid_kbd():
    # kbd role iterator
    warn_role_kbd.iter_kbd = re.compile(r"\:kbd\:`([^`]*?)`")

    # config: allow "Regular key pressed as a modifier"
    regular_as_mod = True

    pattern_str = ''.join((
        # Modifier
        r"^(Shift(?:\-|\Z))?(Ctrl(?:\-|\Z))?(Alt(?:\-|\Z))?(Cmd(?:\-|\Z))?",

        # Alphanumeric
        r"((?:",
        r"[A-Z0-9]|",
        r"(?:[\[\]<>/~!?'\"=]|\\\\)|",

        # Named
        '|'.join((
            "Comma", "Period", "Slash", "Backslash", "Plus", "Minus",
            # Editing
            "Tab", "Backspace", "Delete", "Return", "Spacebar",
            # Navigation
            "Esc", "PageUp", "PageDown", "Home", "End",
            "Up", "Down", "Left", "Right",
        )), '|',
        # Numpad
        r"(?:Numpad(?:[0-9]|Plus|Minus|Delete|Slash|Period|Asterix))|",
        # Function
        r"(?:F[1-9]|F1[0-2])",
        r")(?:\-|\Z))",
        r"{0,2}" if regular_as_mod else r"?",

        # Mouse
        r"(",
        # Wheel
        r"(?:Wheel(Up|Down|In|Out)?)|",
        # Buttons
        r"(?:(?:L|M|R)MB)|",
        # Stylus
        r"(?:Pen|Eraser)",
        r")?$",
    ))

    warn_role_kbd.valid_kbd = re.compile(pattern_str)

    # Directly repeated pressed key e.g. A-A or Left-Left.
    warn_role_kbd.repeat_kbd = re.compile(r"(?:\-|\A)([^ \-]+?)\-\1")



# define the operations to call
operations = []
operations_checks = {
    "--long": (warn_long_lines, None),
    "--kbd": (warn_role_kbd, None),
}


# generic arg parsing
def print_help():
    print("Blender manual checks\n"
          "    Usage: %s { %s }\n" %
          (os.path.basename(__file__),
           " ".join(arg for arg in sorted(operations_checks.keys()))))


for arg in sys.argv[1:]:
    operation = operations_checks.get(arg)
    if operation is None:
        print_help()
        print("Unknown argument %r" % arg)
        sys.exit(1)

    operations.append(operation)


if __name__ == "__main__":
    if operations:
        main()
    else:
        print_help()
        print("No arguments passed")
