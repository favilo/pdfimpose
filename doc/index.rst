Welcome to `Pdfimpose`'s documentation!
=======================================

`pdfimpose` is a library and a command line program to impose a PDF document.
According to `Wikipedia <http://en.wikipedia.org/wiki/Imposition>`_,
"imposition consists in the arrangement of the printed product's pages on the
printer's sheet, in order to obtain faster printing, simplify binding and
reduce paper waste".

.. note::

   *I do not know where to put this, so…*

   - When ``pdfimpose`` has to guess the size of the output paper,
     it uses the `A4 format <https://en.wikipedia.org/wiki/ISO_216#A_series A4>`_.
     This is an (arbitrary) implementation detail, and might change in future releases.

   - When printing an imposed PDF, it shall be printed two-sided,
     the binding edge on the left or right.

Contents
--------

.. toctree::
   :maxdepth: 1

   usage
   library


Examples
--------

* :download:`2022 calendar <examples/calendar2022-impose.pdf>` (:download:`source <examples/calendar2022.pdf>`, see LaTeX source file in sources repository).
* Imposition schemas (here are quick examples, more explanation can be found in :ref:`library`):

  * cards: :download:`examples/cards-impose.pdf` (:download:`source <examples/cards.pdf>`);
  * copycutfold: :download:`examples/copycutfold-impose.pdf` (:download:`source <examples/copycutfold.pdf>`);
  * cutstackfold: :download:`examples/cutstackfold-impose.pdf` (:download:`source <examples/cutstackfold.pdf>`);
  * onepagezine: :download:`examples/onepagezine-impose.pdf` (:download:`source <examples/onepagezine.pdf>`);
  * perfect: :download:`examples/perfect-impose.pdf` (:download:`source <examples/perfect.pdf>`);
  * saddle: :download:`examples/saddle-impose.pdf` (:download:`source <examples/saddle.pdf>`);
  * wire: :download:`examples/wire-impose.pdf` (:download:`source <examples/wire.pdf>`).

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
- `PDF::Imposition <https://metacpan.org/pod/PDF::Imposition>`_ (Perl module; I got the idea for some of the schemas from here)

What might make this software better than other is:

- it can perform on arbitrary paper size;
- it can perform several different imposition schemas, without any assumption on folds number.


Download and install
--------------------

See the `main project page <http://framagit.org/spalax/pdfimpose>`_ for
instructions, and `changelog
<https://framagit.org/spalax/pdfimpose/blob/main/CHANGELOG.md>`_.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

