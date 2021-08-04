Command line
============

This module includes a command line client: `pdfimpose`, which can be used to
impose a PDF document, using one of the :ref:`imposition schemas <library>`.

.. contents:: Contents
   :local:
   :depth: 1

Schemas
-------

You can impose file using any schemas with the following command line::

    pdfimpose SCHEMA foo.pdf

For instance, to impress your A5 document using *saddle stitch* (like in magazines), use::

    pdfimpose saddle foo.pdf

Each schema have different options. Use ``pdfimpose SCHEME --help`` for more information.

Configuration file
------------------

Subcommand ``apply`` can be used to store options in a configuration file::

    pdfimpose apply [-h] [--schema SCHEMA] [CONF] [PDF ...]

- ``CONF`` is a configuration file, in *yaml* format (see below);
- ``PDF`` is the file(s) to process;
- ``SCHEMA`` is the imposition schema to use.

Those three arguments are optional: ``pdfimpose apply`` is a valid command line:

- If ``CONF`` is missing, a configuration file is searched:
  - ``pdfimpose.cfg`` or ``.pdfimpose.cfg``, in the current working directory;
  - the same files, in the parent directory, or grand-parent directory, or…;
  - the same files, in ``~/.config``;
  - the same files, in the home directory;
  - ``/etc/pdfimpose.cfg`` (depending on the operating system).
- If ``PDF`` is missing, it is read from the configuration file (section ``general``, option ``files``).
- If ``SCHEMA`` is missing, it is read from the configuration file (section ``general``, option ``schema``).

For instance, calling ``pdfimpose apply foo.cfg``, where ``foo.cfg`` contains:

.. code-block:: cfg

    [general]
    schema = perfect
    files = foo.pdf bar.pdf

    [perfect]
    imargin = 1cm
    omargin = .5cm

is equivalent to the following command line::

    pdfimpose perfect --imargin 1cm --omargin .5cm foo.pdf bar.pdf
