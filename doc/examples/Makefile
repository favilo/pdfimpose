SCHEMAS=cards copycutfold cutstackfold onepagezine perfect saddle wire
EXAMPLES=$(SCHEMAS:%=%-impose.pdf)

all: calendar2022-impose.pdf $(EXAMPLES)

# Calendar

calendar2022-impose.pdf: calendar2022.pdf
	pdfimpose perfect --bind top --format A4 --last 1 $<

calendar2022.pdf: calendar2022.tex
	pdflatex $<

# Schemas

%-impose.pdf: %.pdf
	pdfimpose $$(echo $@ | cut -d- -f1) $<
