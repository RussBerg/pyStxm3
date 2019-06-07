# -----------
# System Vars
OS:=$(shell uname -s)

# ------------------------------------------
# Get the number of cores for threaded build
ifndef NPROCS
	NPROCS:=1
	ifeq ($(OS), Linux)
		NPROCS:=$(shell nproc)
	endif
	ifneq (,$(filter $(OS),Darwin FreeBSD NetBSD))
		NPROCS:=$(shell sysctl -n hw.ncpu)
	endif
endif

# End System Vars
# ---------------

SPHINXOPTS    = -j "$(NPROCS)"
PAPER         =
SPHINXBUILD   = sphinx-build
BUILDDIR      = build

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d "$(BUILDDIR)/doctrees" $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) manual
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) manual

# full paths
CHAPTERS_FULL:=$(filter %/, $(wildcard manual/*/))
# names only
CHAPTERS:=$(notdir $(sort $(CHAPTERS_FULL:%/=%)))
# intersect make goals and possible chapters
QUICKY_CHAPTERS=$(filter $(MAKECMDGOALS),$(CHAPTERS))


# -----------------------
# for echoing output only
ifeq ($(QUICKY_CHAPTERS), )
	CONTENTS_HTML="index.html"
else
	CONTENTS_HTML="contents_quicky.html"
endif

# os specific
ifeq ($(OS), Darwin)
	# OSX
	OPEN_CMD="open"
else
	# Linux/FreeBSD
	OPEN_CMD="xdg-open"
endif
# end output for echoing
# ----------------------


ifneq "$(findstring singlehtml, $(MAKECMDGOALS))" ""
	.DEFAULT_GOAL := singlehtml
else ifneq "$(findstring pdf, $(MAKECMDGOALS))" ""
	.DEFAULT_GOAL := pdf
else
	.DEFAULT_GOAL := html
endif


$(CHAPTERS): $(.DEFAULT_GOAL)


# --------------------
# Check commands exist

.SPHINXBUILD_EXISTS:
	@if ! which $(SPHINXBUILD) > /dev/null 2>&1; then \
		echo -e >&2 \
			"The '$(SPHINXBUILD)' command was not found.\n"\
			"Make sure you have Sphinx installed, then set the SPHINXBUILD environment variable to\n"\
			"point to the full path of the '$(SPHINXBUILD)' executable.\n"\
			"Alternatively you can add the directory with the executable to your PATH.\n"\
			"If you don't have Sphinx installed, grab it from http://sphinx-doc.org)\n"; \
		false; \
	fi

# End command checking
# --------------------


html: .FORCE .SPHINXBUILD_EXISTS
	# './' (input), './html/' (output)
	QUICKY_CHAPTERS=$(QUICKY_CHAPTERS) \
	$(SPHINXBUILD) -b html $(SPHINXOPTS) ./manual "$(BUILDDIR)/html"

	@echo "To view, run:"
	@echo "  "$(OPEN_CMD) $(shell pwd)"/$(BUILDDIR)/html/$(CONTENTS_HTML)"

html_server: .FORCE .SPHINXBUILD_EXISTS
	# './' (input), './html/' (output)
	# - Single thread because we run many builds at once.
	# - Optimize to use less memory per-process.
	PYTHONOPTIMIZE=2 \
	$(SPHINXBUILD) -a -E -b html $(SPHINXOPTS) -j 1 ./manual "$(BUILDDIR)/html"

epub: .FORCE .SPHINXBUILD_EXISTS
	# './' (input), './epub/' (output)
	QUICKY_CHAPTERS=$(QUICKY_CHAPTERS) \
	$(SPHINXBUILD) -b epub $(SPHINXOPTS) ./manual "$(BUILDDIR)/epub"

	@echo "To view, run:"
	@echo "  "$(OPEN_CMD) $(shell pwd)"/$(BUILDDIR)/epub/*.epub"

singlehtml: .FORCE .SPHINXBUILD_EXISTS
	# './' (input), './html/' (output)
	QUICKY_CHAPTERS=$(QUICKY_CHAPTERS) \
	$(SPHINXBUILD) -b singlehtml $(SPHINXOPTS) ./manual "$(BUILDDIR)/singlehtml"

	@echo "To view, run:"
	@echo "  "$(OPEN_CMD) $(shell pwd)"/$(BUILDDIR)/singlehtml/$(CONTENTS_HTML)"

pdf: .FORCE
	QUICKY_CHAPTERS=$(QUICKY_CHAPTERS) \
	$(SPHINXBUILD) -b latex ./manual "$(BUILDDIR)/latex"
	make -C "$(BUILDDIR)/latex" LATEXOPTS="-interaction nonstopmode"

	@echo "To view, run:"
	@echo "  "$(OPEN_CMD)" $(shell pwd)"/$(BUILDDIR)/latex/blender_manual.pdf"

readme: .FORCE
	rst2html5 readme.rst > ./build/readme.html

	@echo "Build finished. The HTML page is in $(BUILDDIR)/readme.html."
	@echo "To view, run:"
	@echo "  "$(OPEN_CMD)" $(shell pwd)"/$(BUILDDIR)/readme.html"

check_syntax: .FORCE
	- python3 tools_rst/rst_check_syntax.py --long > rst_check_syntax.log
	- @echo "Lines:" `cat rst_check_syntax.log | wc -l`
	- gvim --nofork -c "cfile rst_check_syntax.log" -c "cope" -c "clast"
	- rm rst_check_syntax.log

check_structure: .FORCE
	@python3 tools_rst/rst_check_images.py
	@python3 tools_rst/rst_check_locale.py

#	- python3 tools_rst/rst_check_structure.py --image > rst_check_structure.log
#	- @echo "Lines:" `cat rst_check.log  | wc -l`
#	- gvim --nofork -c "cfile rst_check_structure.log" -c "cope" -c "clast"
#	- rm rst_check_structure.log

check_spelling: .FORCE
	- python3 tools_rst/rst_check_spelling.py

check_links: .FORCE
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) $(BUILDDIR)/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

clean: .FORCE
	rm -rf $(BUILDDIR)/*

update_po: .FORCE
	- ./tools_maintenance/update_po.sh

report_po_progress: .FORCE
	- python3 tools_report/report_translation_progress.py --quiet \
	          `find locale/ -maxdepth 1 -mindepth 1 -type d -not -iwholename '*.svn*' -printf 'locale/%f\n' | sort`

gettext: .FORCE .SPHINXBUILD_EXISTS
	$(SPHINXBUILD) -t builder_html -b gettext $(I18NSPHINXOPTS) $(BUILDDIR)/locale
	@echo
	@echo "Build finished. The message catalogs are in $(BUILDDIR)/locale."



# -----------------------------------------------------------------------------
# Help for build targets
help:
	@echo ""
	@echo "Documentation"
	@echo "============="
	@echo ""
	@echo "Convenience targets provided for building docs"
	@echo "- html                 to make standalone HTML files (default)"
	@echo "- singlehtml           to make a single large HTML file"
	@echo "- pdf                  to make a PDF using LaTeX warning: this currently has some problems,"
	@echo "                       though the PDF generates, there are various unresolved issues	"
	@echo "- readme               to make a 'readme.html' file"
	@echo "- clean                to delete all old build files"
	@echo ""
	@echo "Chapters               to quickly build a single chapter"
	@$(foreach ch,$(CHAPTERS),echo "- "$(ch);)
	@echo ""
	@echo "Translations"
	@echo "============"
	@echo ""
	@echo "- gettext              to make PO message catalogs"
	@echo "- update_po            to update PO message catalogs"
	@echo "- report_po_progress   to check the progress/fuzzy strings"
	@echo ""
	@echo "Checking"
	@echo "========"
	@echo ""
	@echo "- check_structure      to check the structure of all .rst files"
	@echo "- check_syntax         to check the syntax of all .rst files"
	@echo "- check_links          to check all external links for integrity"
	@echo "- check_spelling       to check spelling for text in RST files"
	@echo ""

.FORCE:
