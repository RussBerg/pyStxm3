#!/usr/bin/env python3
# Apache License, Version 2.0
# Copyright 2015 Anton Felix Lorenzen <anfelor@web.de>
# <pep8 compliant>

'''
Module of Translation Tracker: report the number of complete strings in a file.
'''

def parse_file(po_filepath):
    msgstrs_complete = -1  # First lines contain a "fake" msgstr
    msgstrs_empty = 0
    msgstrs_fuzzy = 0
    for line in open(po_filepath, encoding='utf8'):
        result = parse_line(line)
        if result == 'COMPLETE' or result == 'EMPTY':
            msgstrs_complete += 1
            if result == 'EMPTY':
                msgstrs_empty += 1
                last_line_was_empty_msg_str = True
        else:
            if result == 'CONTINUATION':
                if last_line_was_empty_msg_str:
                    msgstrs_empty -= 1
            else:
                if result == 'FUZZY' and msgstrs_complete >= 0:
                    # ignore fuzzy on "fake" msgstr
                    msgstrs_fuzzy += 1
            last_line_was_empty_msg_str = False
    return msgstrs_complete, msgstrs_empty, msgstrs_fuzzy

def parse_line(line):
    if line.startswith('msgstr'):
        if line.startswith('msgstr ""'):
            return 'EMPTY'
        return 'COMPLETE'
    if line[0] == '"':
        return 'CONTINUATION'
    # only search in flag comments, "fuzzy" could occur
    # in filenames ("#:"), translator e-mail ("# ") etc.
    if line.startswith('#,') and 'fuzzy' in line:
        return 'FUZZY'
    return 'NONE'
