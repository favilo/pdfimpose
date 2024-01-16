.. _library:

Library
=======

Most of the classes and function of ``pdfimpose`` are not *private* (their name do not start with and underscore),
but the only ones being maintained are the following ones.
Use the others at your own risk!

.. note::

   The description of each imposition schemas would be a lot more understandable with a nice drawing or video.
   I cannot do any of those. If you can, and you have some time to spare, it would be very welcome!

.. toctree::
   :maxdepth: 1

   lib/schema
   lib/cards
   lib/copycutfold
   lib/cutstackfold
   lib/onepagezine
   lib/hardcover
   lib/saddle
   lib/wire

.. deprecated:: 2.5.0

   A ``perfect`` imposition schema did exist before version 2.5.0, when it has been renamed to ``hardcover``. It can still be used for backward compatibility, but will be removed in some later version.

