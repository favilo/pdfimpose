SCHEMAS=cards copycutfold cutstackfold onepagezine hardcover saddle wire
EXAMPLES=$(SCHEMAS:%=%-impose.pdf)

all: calendar2024-impose.pdf $(EXAMPLES)

# Calendar

calendar2024.pdf: calendar2024.tex
	pdflatex $<

calendar2024-impose.pdf: calendar2024.pdf
	pdftk $< cat 1-r2 r1south output - | ../../bin/pdfimpose hardcover --bind top --format A4 --last 1 --output $@

# Schemas

%-impose.pdf: %.pdf
	../../bin/pdfimpose $$(echo $@ | cut -d- -f1) $<
