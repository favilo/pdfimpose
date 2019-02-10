Command line
============

This module includes a command line client: `pdfimpose`. It can be used to
impose a pdf document. For instance, the following command creates a
:file:`foo-impose.pdf` file, corresponding to the imposition of :file:`foo.pdf`
with the default options.::

    pdfimpose foo.pdf


.. contents:: Contents
   :local:
   :depth: 1


Options
-------

Here are its command line options.

.. argparse::
    :module: pdfimpose.options
    :func: commandline_parser
    :prog: pdfimpose

Layout
------

The ``[--fold FOLD | --size WIDTHxHEIGHT | --paper PAPER | --sheets SHEETS]`` are used to define the layout of the output pages. They are exclusive.

Let's say I have a :download:`PDF file of 32 A6 pages <usage/a6.pdf>`, that I want to impose on A3 paper.
The :download:`resulting file <usage/a6-impose.pdf>` is to be printed on two A3 sheets of paper, the first one being:

.. table:: Recto
   :widths: auto

   == === === ==
   2  15  14  3
   7* 10* 11* 6*
   == === === ==

.. table:: Verso
   :widths: auto

   == === == ==
   4  13  16 1
   5* 12* 9* 8*
   == === == ==

To generate this, I could use any of those commands.

- ``pdfimpose --fold hvh file.pdf`` means "Impose 'file.pdf' so that I will have to fold the resulting paper sheets horizontally, then vertically, then horizontally again."
- ``pdfimpose --size 4x2 file.pdf`` means "Impose 'file.pdf' so that on the resulting paper sheets, I will have 4 columns and 2 rows of source pages."
- ``pdfimpose --paper A3 file.pdf`` means "Impose 'file.pdf' so that it can be printed on A3 paper."
- ``pdfimpose --sheets 2 file.pdf`` means "Impose 'file.pdf' so that it can be printed on two paper sheets."

