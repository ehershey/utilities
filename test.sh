#!/bin/bash
#
# Test a directory of files for correct syntax by examining #! header lines
# and file extensions.
#
# Skip files without clear validity criteria (unknown file types or text)
#
# Files aren't executed but are passed through a parser of their format
# to verify syntax.
#
# Types supported:
# Perl
# Python
# Javascript
# JSON
# Markdown
# Bourne Shell
#
# Usage:
# test.sh [ --quiet ] [ <filename glob pattern> ]
#
# Tests everything by default

set -o errexit
errors=0
filecount=0

if [ "$1" == "--quiet" ]
then
  quiet=1
  shift
else
  quiet=""
fi

if [ "$1" ]
then
  filelist="$(echo *$1*)"
else
  filelist="$(echo *)"
fi

loudecho() {
  if [[ ! "$quiet" ]]
  then
    echo "$@"
  fi
}

export PATH=$PATH:./node_modules/.bin

for file in $filelist
do
  let filecount=filecount+1
  loudecho "Examining directory entry: $file"
  if [ -d "$file" ]
  then
    loudecho Skipping directory
  elif [ "$file" = "gpgexport" ]
  then
    loudecho Skipping gpgexport
  elif echo "$file" | grep -q \\.as$
  then
    loudecho Skipping Applescript file
  elif echo "$file" | grep -q \\.html$
  then
    loudecho Skipping HTML file
  elif head -1 "$file" | grep -q bin/.\*sh || echo "$file" | grep -q \\.sh$ || echo "$file" | grep -q \\.env$
  then
    if ! bash -n "$file"
    then
      let errors=errors+1
      echo ERROR: syntax check failed "($file)"
    fi
  elif head -1 "$file" | grep -q perl || echo "$file" | grep -q \\.pl$
  then
    if ! perl -c "$file"
    then
      let errors=errors+1
      echo ERROR: syntax check failed "($file)"
      fi
  elif head -1 "$file" | grep -q python || echo "$file" | grep -q \\.py$
  then
    if ! python -m py_compile "$file"
    then
      let errors=errors+1
      echo ERROR: syntax check failed "($file)"
      fi
  elif echo "$file" | grep -q \\.json$
  then
    if ! cat "$file" | python -mjson.tool > /dev/null
    then
      let errors=errors+1
      echo ERROR: syntax check failed "($file)"
    fi
  elif echo "$file" | grep -q \\.html$
  then
    if ! tidy -error "$file"
    then
      let errors=errors+1
      echo ERROR: syntax check failed "($file)"
    fi

  elif echo "$file" | grep -q \\.md$
  then
    if ! cat "$file" | md2html > /dev/null
    then
      let errors=errors+1
      echo ERROR: syntax check failed "($file)"
    fi
  elif head -1 "$file" | grep -q node || echo "$file" | grep -q \\.js$
  then
    if ! tail -n +2 "$file" | uglifyjs > /dev/null
    then
      let errors=errors+1
      echo ERROR: syntax check failed "($file)"
    fi
  elif echo "$file" | grep -q \\.pyc$
  then
    loudecho Skipping compiled python file
  elif echo "$file" | grep -q \\.txt$
  then
    loudecho Skipping text file
  elif echo "$file" | grep -q \\.log$
  then
    loudecho Skipping log file
  else
    let errors=errors+1
    echo "ERROR: Unknown file type" "($file)"
  fi
done

echo "Examined $filecount filecount"
echo "Found $errors errors"
if [ $errors -gt 0 ]
then
  exit $errors
else
  exit 0
fi
