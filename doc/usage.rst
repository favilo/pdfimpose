Command line
============

This module includes a command line client: `pdfimpose`. It can be used to
impose a pdf document. For instance, the following command creates a
:file:`foo-impose.pdf` file, corresponding to the imposition of :file:`foo.pdf`
with the default options.::

    pdfimpose foo.pdf


Options
-------

Here are its command line options.

.. argparse::
    :module: pdfimpose.options
    :func: commandline_parser
    :prog: pdfimpose

