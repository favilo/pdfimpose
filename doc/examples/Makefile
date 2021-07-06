SCHEMAS=cards copycutfold cutstackfold onepagezine perfect saddle wire
DUMMY64=$(SCHEMAS:%=dummy64-%.pdf)

all: calendar2022-impose.pdf $(DUMMY64)

# Calendar

calendar2022-impose.pdf: calendar2022.pdf
	pdfimpose perfect --bind top --format A4 --last 1 $<

calendar2022.pdf: calendar2022.tex
	pdflatex $<

# Dummy

.ONESHELL:
dummy64-%.pdf: dummy64.pdf
	schema=$$(echo $@ | cut -d- -f2 | cut -d. -f1)
	pdfimpose $$schema -o $@ $<
