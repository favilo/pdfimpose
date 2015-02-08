Welcome to `PdfImpose`'s documentation!
=======================================

`PdfImpose` is a library and a command line program to impose a Pdf document.
According to `Wikipedia <TODO>`_, "imposition consists in the arrangement
of the printed product's pages on the printer's sheet, in order to obtain
faster printing, simplify binding and reduce paper waste".

Contents
--------

.. toctree::
   :maxdepth: 1

   impose
   usage
   folding
   algorithm


Examples
--------

* :download:`2015 calendar <../examples/calendar2015-impose.pdf>` (:download:`source <../examples/calendar2015.pdf>`, see LaTeX source file in sources repository).
* :download:`64 pages file <../examples/dummy64-impose.pdf>` (:download:`source <../examples/dummy64.pdf>`, generated using `dummypdf <TODO>`_).

See also
--------

I am far from being the first person to implement such an algorithm. I am fond
of everything about pre-computer-era printing (roughly, from Gutemberg to the
Linotype). Being also a geek, I wondered how to compute how the pages would be
arranged on the printer's sheet, and here is the result.

Other implementation of imposition are:

- TODO


Download and install
--------------------

* Download: http://TODO/pdfimpose-TODO.tar.gz.
* Install (in a `virtualenv`, not to mess with your distribution installation system):

    * With `pip`:

        .. code-block:: shell

            pip install TODO/pdfimpose-TODO.tar.gz

    * Without `pip`: Download and unpack package, and run:

        .. code-block:: shell

            python3 setup.py install

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

