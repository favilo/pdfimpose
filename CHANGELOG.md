* pdfimpose 1.1.0 (2019-02-12)

    * Python support

      * Add python3.7 support.
      * Drop python3.4 support.

    * Features and Bugs

      * Fix an orientation error with option --sheets.
      * Fix a bug in `--paper` option, which, with ``--paper=A3``, would make a A5 paper be imposed on A4 paper instead of A3 paper (closes #16).

    * Minor improvements to:

      * documentation;
      * setup;
      * continuous integration;
      * examples.

    -- Louis Paternault <spalax+python@gresille.org>

* pdfimpose 1.0.0 (2017-12-28)

    * Add python3.6 support.
    * Several files can be given in argument. They are concatenated, then imposed (closes #10).
    * No longer crash when using pdfimpose on file without any metadata (closes #12).
    * Warn user if all pages do not have the same dimension (closes #11).
    * Display nicer messages with several input-file related errors (absent, unreadable, malformed, etc. file).
    * Add options `--paper` and `--sheets`, to define how document is folded more easily (closes #7).
    * Horizontal and vertical folds are alternated as much as possible (closes #8).

    -- Louis Paternault <spalax+python@gresille.org>

* pdfimpose 0.1.1 (2015-06-13)

    * Python3.5 support
    * Several minor improvements to setup, test and documentation.
    * [doc] Wrote missing parts

    -- Louis Paternault <spalax+python@gresille.org>

* pdfimpose 0.1.0 (2015-04-15)

    * Initial release.

    -- Louis Paternault <spalax+python@gresille.org>
