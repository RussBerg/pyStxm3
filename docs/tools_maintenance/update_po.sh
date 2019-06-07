#!/bin/bash
# Apache License, Version 2.0

# This script is to reduce tedious steps involved when updating PO files.
# It looks more complex then it really is, since we do multi-processing
# to update the PO files, to save some time.


# Trap on the ERR pseudo signal
# http://stackoverflow.com/a/4384381/432509
err_trap () {
    errcode=$? # save the exit code as the first thing done in the trap function
	echo "  Error($errcode) on line ${BASH_LINENO[0]}, in command:"
    echo "  $BASH_COMMAND"
    exit $errcode
}
trap err_trap ERR

# Python needs utf
export LANG="en_US.UTF8"

# Ensure we're in the repo's base:
BASEDIR=$(dirname $0)
cd $BASEDIR
cd ../


# Update the locale dir:
cd ./locale
svn cleanup .
svn up .
cd ../


# Create PO files:
rm -rf build/locale
make gettext


# Update PO files
#
# note, this can be slow so (multi-process)
for lang in `find locale/ -maxdepth 1 -mindepth 1 -type d -not -iwholename '*.svn*' -printf '%f\n' | sort`; do
	sphinx-intl update -p build/locale -l $lang &
done

FAIL=0
for job in `jobs -p`; do
echo $job
    wait $job || let "FAIL+=1"
done
if [ "$FAIL" != "0" ]; then
	echo "Error updating"
	exit 1
fi
unset FAIL


# Add newly created PO files:
cd locale/
NEW_FILES=`svn status . | grep -e "\.po$" | awk '/^[?]/{print $2}'`
if [ "$NEW_FILES" != "" ]; then
	svn add $NEW_FILES
fi
unset NEW_FILES

# note, the Python part filters only for directories
# there may be a cleaner way to do this in shell.
NEW_DIRS=`svn status . | grep -v -e "\.po$" | awk '/^[?]/{print $2}' | python -c "import sys, os; sys.stdout.write('\n'.join([f for f in sys.stdin.read().split('\n') if os.path.isdir(f)]))"`
if [ "$NEW_DIRS" != "" ]; then
	svn add $NEW_DIRS
fi
unset NEW_DIRS

cd -


# Notify on redundant PO files
python3 tools_rst/rst_check_locale.py

# Print Commit message:
REVISION=`svn info . | grep '^Revision:' | sed -e 's/^Revision: //'`
echo " cd locale; svn ci . -m \"Update r"$REVISION\""; cd .." 

