#!/bin/sh
cd $(dirname $0)
NAME=$(basename $0 .sh)
pdflatex $NAME
pdfimpose --bind top --size 2x4 $NAME.pdf
