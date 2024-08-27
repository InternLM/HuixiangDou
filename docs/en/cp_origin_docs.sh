#!/usr/bin/env bash

# Copy *.md files from docs/ if it doesn't have a Chinese translation

for filename in $(find ../zh/ -name '*.md' -printf "%P\n");
do
    mkdir -p $(dirname $filename)
    cp -n ../zh/$filename ./$filename
    cp -n ../../README.md ./copy_quickstart.md
    cp -n ../../evaluation/README.md ./copy_precision.md
done
