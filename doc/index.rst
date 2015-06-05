Welcome to `PdfImpose`'s documentation!
=======================================

`PdfImpose` is a library and a command line program to impose a Pdf document.
According to `Wikipedia <http://en.wikipedia.org/wiki/Imposition>`_,
"imposition consists in the arrangement of the printed product's pages on the
printer's sheet, in order to obtain faster printing, simplify binding and
reduce paper waste".

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

* :download:`2015 calendar <examples/calendar2015-impose.pdf>` (:download:`source <examples/calendar2015.pdf>`, see LaTeX source file in sources repository).
* :download:`64 pages file <examples/dummy64-impose.pdf>` (:download:`source <examples/dummy64.pdf>`, generated using `dummypdf <http://git.framasoft.org/spalax/dummypdf>`_).

See also
--------

I am far from being the first person to implement such an algorithm. I am fond
of everything about pre-computer-era printing (roughly, from Gutemberg to the
Linotype). Being also a geek, I wondered how to compute how the pages would be
arranged on the printer's sheet, and here is the result.

Some (free) other implementation of imposition are:

- Scribus have `a list <http://wiki.scribus.net/canvas/PDF,_PostScript_and_Imposition_tools>`_ of some of those tools
- `BookletImposer <http://kjo.herbesfolles.org/bookletimposer/>`_
- `Impose <http://multivalent.sourceforge.net/Tools/pdf/Impose.html>`_


Download and install
--------------------

See the `main project page <http://git.framasoft.org/spalax/pdfimpose>`_ for
instructions, and `changelog
<https://git.framasoft.org/spalax/pdfimpose/blob/master/CHANGELOG>`_.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

