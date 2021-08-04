pdfimpose 📕 Perform imposition of a PDF file
=============================================

Imposition consists in the arrangement of the printed product’s pages on
the printer’s sheet, in order to obtain faster printing, simplify binding
and reduce paper waste (source: http://en.wikipedia.org/wiki/Imposition).

This software can perform imposition on PDF files of arbitrary size.
It handles several imposition schemas: perfect binding, saddle stitch, one page zine, etc.
See `documentation <https://pdfimpose.rtfd.io>`__ for more details.


Examples
--------

* `2022 calendar <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/calendar2022-impose.pdf?inline=false>`_ (`source <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/calendar2022.pdf?inline=false>`__, see LaTeX source file in sources repository).
* `Flash cards <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/cards-impose.pdf>`_ (`source <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/cards.pdf>`__);
* `Copy, cut, fold <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/copycutfold-impose.pdf>`_ (`source <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/copycutfold.pdf>`__);
* `Cut, stack, fold <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/cutstackfold-impose.pdf>`_ (`source <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/cutstackfold.pdf>`__);
* `One-page-zine <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/onepagezine-impose.pdf>`_ (`source <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/onepagezine.pdf>`__);
* `Perfect binding <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/perfect-impose.pdf>`_ (`source <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/perfect.pdf>`__);
* `Saddle stitch <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/saddle-impose.pdf>`_ (`source <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/saddle.pdf>`__);
* `Wire binding <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/wire-impose.pdf>`_ (`source <https://framagit.org/spalax/pdfimpose/-/raw/main/doc/examples/wire.pdf>`__).

What's new?
-----------

See `changelog <https://git.framasoft.org/spalax/pdfimpose/blob/main/CHANGELOG.md>`_.

Download and install
--------------------

See the end of list for a (quick and dirty) Debian package.

* From sources:

  * Download: https://pypi.python.org/pypi/pdfimpose
  * Install (in a `virtualenv`, if you do not want to mess with your distribution installation system)::

        python setup.py install

* From pip::

    pip install pdfimpose

* Quick and dirty Debian (and Ubuntu?) package

  This requires `stdeb <https://github.com/astraw/stdeb>`_ to be installed::

      python setup.py --command-packages=stdeb.command bdist_deb
      sudo dpkg -i deb_dist/python<PYVERSION>-pdfimpose_<VERSION>_all.deb

Documentation
-------------

* The compiled documentation is available on `readthedocs <http://pdfimpose.readthedocs.io>`_

* To compile it from source, download and run::

      cd doc && make html
