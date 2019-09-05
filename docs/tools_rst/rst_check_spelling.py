#!/usr/bin/env python3
# Apache License, Version 2.0

"""
Check spelling for all RST files in the repository.

- TODO: more comprehensive docs.
- TODO: some words get extracted that shouldn't.
"""

import os
import sys
import re


# for spelling
import enchant
dict_spelling = enchant.Dict("en_US")

from rst_check_spelling_config import (
    dict_custom,
    dict_ignore,
)

USE_ONCE = True
once_words = set()
bad_words = set()


def find_vcs_root(test, dirs=(".svn", ".git", ".hg"), default=None):
    import os
    prev, test = None, os.path.abspath(test)
    while prev != test:
        if any(os.path.isdir(os.path.join(test, d)) for d in dirs):
            return test
        prev, test = test, os.path.abspath(os.path.join(test, os.pardir))
    return default


def check_word(w):
    if not w:
        return True
    w_lower = w.lower()
    if w_lower in dict_custom or w_lower in dict_ignore:
        return True
    return dict_spelling.check(w)


def check_spelling_body(text):
    for w in text.split():
        # skip directive args (e.g. figure target), could do differently?
        if w.startswith(":") and w.endswith(":"):
            continue
        if w.startswith("<") and w.endswith(">"):
            continue

        w = w.strip("{}[](),.!?;\"'1234567890-_*")

        if w.startswith(":") and w.endswith(":"):
            continue
        if w.startswith("<") and w.endswith(">"):
            continue

        # now we've gotten rid of typical roles, strip other chars
        w = w.strip(":`()<>{}")

        w_ = w
        for w in w_.split("/"):
            if not w:
                continue

            w_lower = w.lower()

            if USE_ONCE and w_lower in once_words:
                continue

            if check_word(w):
                pass
            elif "-" in w and all(check_word(w_split) for w_split in w.split("-")):
                pass  # all words split by dash are correct, also pass
            else:
                bad_words.add(w)
                # print(" %r" % w)

                if USE_ONCE:
                    once_words.add(w_lower)


CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
RST_DIR = find_vcs_root(CURRENT_DIR)


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
        check_spelling(fn)

    # We could have nicer in-context display,
    # for now just print the words
    words_sorted = list(bad_words)
    words_sorted.sort(key=lambda s: s.lower())
    for w in words_sorted:
        print(w)
        # print(w, "->", " ".join(dict_spelling.suggest(w)))


# -----------------------------------------------------------------------------
# Register dummy directives

import docutils
from docutils.parsers.rst import directives, roles


def directive_ignore(
        name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine,
):
    """
    Used to explicitly mark as doctest blocks things that otherwise
    wouldn't look like doctest blocks.

    Note this doesn't ignore child nodes.
    """
    text = '\n'.join(content)
    '''
    if re.match(r'.*\n\s*\n', block_text):
        warning('doctest-ignore on line %d will not be ignored, '
             'because there is\na blank line between ".. doctest-ignore::"'
             ' and the doctest example.' % lineno)
    '''
    return [docutils.nodes.doctest_block(text, text, codeblock=True)]


directive_ignore.content = True


def directive_ignore_recursive(
        name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine,
):
    """
    Ignore everything under this directive (use with care!)
    """
    return []


directive_ignore_recursive.content = True


# ones we want to check
directives.register_directive('index', directive_ignore)
directives.register_directive('seealso', directive_ignore)
directives.register_directive('only', directive_ignore)
directives.register_directive('hlist', directive_ignore)
# directives.register_directive('glossary', directive_ignore)  # wash this data instead

# Recursive ignore, take care!
directives.register_directive('toctree', directive_ignore_recursive)
directives.register_directive('code-block', directive_ignore_recursive)
directives.register_directive('youtube', directive_ignore_recursive)
directives.register_directive('vimeo', directive_ignore_recursive)
directives.register_directive('highlight', directive_ignore_recursive)
directives.register_directive('parsed-literal', directive_ignore_recursive)

# workaround some bug? docutils won't load relative includes!
directives.register_directive('include', directive_ignore_recursive)


# Dummy roles
class RoleIgnore(docutils.nodes.Inline, docutils.nodes.TextElement):
    pass


def role_ignore(
        name, rawtext, text, lineno, inliner,
        options={}, content=[],
):
    # Recursively parse the contents of the index term, in case it
    # contains a substitution (like |alpha|).
    nodes, msgs = inliner.parse(text, lineno, memo=inliner, parent=inliner.parent)
    # 'text' instead of 'rawtext' because it doesn't contain the :role:
    return [RoleIgnore(text, '', *nodes, **options)], []


class RoleIgnoreRecursive(docutils.nodes.Inline, docutils.nodes.TextElement):
    pass


def role_ignore_recursive(
        name, rawtext, text, lineno, inliner,
        options={}, content=[],
):
    return [RoleIgnore("", '', *(), **{})], []


roles.register_canonical_role('abbr', role_ignore)
roles.register_canonical_role('menuselection', role_ignore)

roles.register_canonical_role('class', role_ignore_recursive)
roles.register_canonical_role('doc', role_ignore_recursive)
roles.register_canonical_role('kbd', role_ignore_recursive)
roles.register_canonical_role('mod', role_ignore_recursive)
roles.register_canonical_role('ref', role_ignore_recursive)
roles.register_canonical_role('term', role_ignore_recursive)

# -----------------------------------------------------------------------------
# Special logic to wash filedata
#
# Special Case

def filedata_glossary_wash(filedata):
    """
    Only list body of text.
    """
    lines_src = filedata.splitlines()
    lines_dst = []
    in_glossary = False
    for l in lines_src:
        l_strip = l.lstrip()
        if l_strip.startswith(".. glossary::"):
            in_glossary = True
            continue
        elif in_glossary is False:
            lines_dst.append(l)
            continue
        else:
            indent = len(l) - len(l_strip)
            if indent <= 3 and l_strip:
                continue
            elif indent >= 6 or not l_strip:
                lines_dst.append(l[6:])
    return "\n".join(lines_dst)


# -----------------------------------------------------------------------------

import docutils.parsers.rst


def rst_to_doctree(filedata, filename):
    # filename only used as an ID
    import docutils.parsers.rst
    parser = docutils.parsers.rst.Parser()
    doc = docutils.utils.new_document(filename)
    doc.settings.tab_width = 3
    doc.settings.pep_references = False
    doc.settings.rfc_references = False
    doc.settings.syntax_highlight = False

    doc.settings.raw_enabled = True  # TODO, check how this works!
    doc.settings.file_insertion_enabled = True
    doc.settings.character_level_inline_markup = False  # TODO, whats sphinx do?
    doc.settings.trim_footnote_reference_space = False  # doesn't seem important

    parser.parse(filedata, doc)
    return doc


def check_spelling(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        filedata = f.read()

        # special content handling
        if filename.endswith(os.path.join("glossary", "index.rst")):
            filedata = filedata_glossary_wash(filedata)

        doc = rst_to_doctree(filedata, filename)
        # print(doc)

    visitor = RstSpellingVisitor(doc)
    doc.walkabout(visitor)


class RstSpellingVisitor(docutils.nodes.NodeVisitor):
    __slots__ = (
        "document",
    )

    def __init__(self, doc):
        self.document = doc

    # -----------------------------
    # Visitors (docutils callbacks)

    def visit_author(self, node):
        print("AUTHOR", node[0])

    # TODO
    def visit_section(self, node):
        pass

    def depart_section(self, node):
        pass

    def visit_title(self, node):
        # print("TITLE", node[0], self.section_level)
        pass

    def depart_title(self, node):
        pass
        # print("/TITLE", node[0])

        '''
        body, body_fmt = self.pop_body()
        align = self.node_align(node)
        elem = BElemText(body, body_fmt, align, self.indent, "style_head%d" % self.section_level)
        self.bdoc.add_elem(elem)
        '''

        # import IPython
        # IPython.embed()

    def visit_list_item(self, node):
        '''
        align = self.node_align(node)
        elem = BElemListItem(align, self.indent, "style_body",
                             self.list_types[-1], self.list_count[-1])
        self.bdoc.add_elem(elem)
        '''
        pass

    def depart_list_item(self, node):
        # self.list_count[-1] += 1
        pass

    def visit_bullet_list(self, node):
        pass
        '''
        self.list_types.append(None)
        self.list_count.append(0)
        '''

    def depart_bullet_list(self, node):
        pass
        '''
        item = self.list_types.pop()
        assert(item == None)
        del self.list_count[-1]
        '''

    def visit_enumerated_list(self, node):
        pass
        '''
        self.list_types.append(node["enumtype"])
        self.list_count.append(0)
        '''

    def depart_enumerated_list(self, node):
        pass
        '''
        item = self.list_types.pop()
        assert(item == node["enumtype"])
        del self.list_count[-1]
        '''

    def visit_paragraph(self, node):
        pass

    def depart_paragraph(self, node):
        pass

        # Just text for now
        # text = node.astext()
        # print(text)
        # check_spelling_body(text)

    def visit_Text(self, node):
        text = node.astext()
        # print(text)
        check_spelling_body(text)

    def depart_Text(self, node):
        pass

    def visit_strong(self, node):
        self.is_strong = True

    def depart_strong(self, node):
        self.is_strong = False

    def visit_emphasis(self, node):
        self.is_emphasis = True

    def depart_emphasis(self, node):
        self.is_emphasis = False

    def visit_math(self, node):
        raise docutils.nodes.SkipNode

    def depart_math(self, node):
        pass

    def visit_literal(self, node):
        raise docutils.nodes.SkipNode

    def depart_literal(self, node):
        pass

    def visit_literal_block(self, node):
        raise docutils.nodes.SkipNode

    def depart_literal_block(self, node):
        pass

    def visit_code_block(self, node):
        raise docutils.nodes.SkipNode

    def depart_code_block(self, node):
        pass

    def visit_reference(self, node):
        raise docutils.nodes.SkipNode

    def depart_reference(self, node):
        pass

    def visit_download_reference(self, node):
        raise docutils.nodes.SkipNode

    def depart_download_reference(self, node):
        pass

    def visit_date(self, node):
        # date = datetime.date(*(
        #    map(int, unicode(node[0]).split('-'))))
        #metadata['creation_date'] = date
        pass

    # def visit_document(self, node):
    #    print("TEXT:", node.astext())
    #    # metadata['searchable_text'] = node.astext()

    def visit_comment(self, node):
        raise docutils.nodes.SkipNode

    def depart_comment(self, node):
        pass

    def visit_raw(self, node):
        raise docutils.nodes.SkipNode

    def depart_raw(self, node):
        pass

    def unknown_visit(self, node):
        pass

    def unknown_departure(self, node):
        pass


if __name__ == "__main__":
    main()
