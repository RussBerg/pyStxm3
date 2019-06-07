#!/usr/bin/env python3

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

__all__ = (
    "role_iter",
    "directive_iter",
    )

def _re_iter_edit(fn, find_text, find_re):
    with open(fn, "r", encoding="utf-8") as f:
        data_src = f.read()

    # keep searching the tail of the list until we're done
    data_dst_ls = [data_src]
    offset = 0
    while True:
        g = find_re.search(data_dst_ls[-1], offset)
        if g:
            offset, offset_next = g.span()
            ls_orig = list(g.groups())
            ls = ls_orig[:]
            yield ls
            if ls != ls_orig:
                data_dst_ls[-1:] = [data_dst_ls[-1][:offset]] + ls + [data_dst_ls[-1][offset_next:]]
                offset = 0
            else:
                offset = offset_next
        else:
            break

    if len(data_dst_ls) != 1:
        with open(fn, "w", encoding="utf-8") as f:
            f.write("".join([w for w in data_dst_ls if w is not None]))


def role_iter(fn, role, angle_brackets=False):
    """
    Convenience iterator for roles,
    so you can loop over and manipulate roles without the hassle of involved string manipulation.

    For the string:

        :some_role:`some text <some link>`

    The following list will be given:

        [":some_role:`"
         "some text",
         " <",
         "some link",
         ">`",
         ]

    Or with angle_brackets=False:

        :some_role:`some text`

    Becomes:

        [":some_role:`"
         "some text",
         "`"
         ]
    """
    import re
    if angle_brackets:
        role_re = re.compile(r"(\:" + role + r"\:\`)([^\<,\n]*)(\s+\<)([^\,\n>]+)(\>\`)")
    else:
        role_re = re.compile(r"(\:" + role + r"\:\`)([^`,\n]*)(\`)")

    yield from _re_iter_edit(fn, role, role_re)


def directive_iter(fn, directive):
    """
    Convenience iterator for directives,
    so you can loop over and manipulate roles without the hassle of involved string manipulation.

    For the string:

        .. |my-image| image:: /images/foo.png

    The following list will be given:

        [".. ",                 # 0
         "|my-image|",          # 1, substitution or None if not given.
         "image",               # 2, directive-type
         ":: ",                 # 3
         "/images/foo.png",     # 4, directive
         ]

    Note that directive arguments aren't currently supported.
    """
    import re
    # Support basic directives:
    # ..·image::·/images/foo.png
    # As well as substitutions
    # ..·|my-image|·image::·/images/foo.png
    directive_re = re.compile(r"(\.\.\s+)(\|[^\|]+\|\s+)?(" + directive + r")(\:\:\s+)([^\s,\n]*)")

    yield from _re_iter_edit(fn, directive, directive_re)

