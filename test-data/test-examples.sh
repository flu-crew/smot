#!/usr/bin/env bash

set -e

while read -r example
do
    echo $example > /dev/stderr
    eval $example > /dev/null
done < <(grep "^      smot" ../smot/main.py)
