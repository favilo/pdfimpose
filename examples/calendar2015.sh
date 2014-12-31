#!/bin/sh
NAME=$(basename $0 .sh)
pdflatex $NAME
pdfimpose --bind top --size 2x4 $NAME.pdf

