#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright Louis Paternault 2014-2015
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 1

"""Perform imposition of a PDF file.

Basic example
-------------

The following example opens pdf file :file:`foo.pdf`, and writes as
:file:`foo-impose.pdf` its imposed version, made to be folded vertically then
horizontally.

.. code-block:: python

    from pdfimpose import impose, VERTICAL, HORIZONTAL

    impose(
        inname="foo.pdf",
        outname="foo-impose.pdf",
        fold=[VERTICAL, HORIZONTAL],
        bind="left",
        last=0,
        )

High level manipulation
-----------------------

This is the only function you will need to perform imposition. For more
fine-grained manipulation, see :ref:`low-level`.

.. autofunction:: impose

Direction
^^^^^^^^^

Fold direction is set using constants :data:`VERTICAL` and :data:`HORIZONTAL`,
instances of :class:`Direction`.

.. autodata:: VERTICAL
    :annotation:

.. autodata:: HORIZONTAL
    :annotation:

.. autoclass:: Direction
    :members:

.. _low-level:

Low level manipulation
----------------------

These objects will usually not be manipulated directly by user. They are used
internally may be manipulated if finer processing is performed. However, if you
do want to have control over what is going on, you can use them.

Orientation
^^^^^^^^^^^

:class:`Pages <ImpositionPage>` represented in the :class:`ImpositionMatrix`
are oriented toward north or south.

.. autodata:: NORTH
.. autodata:: SOUTH

.. autoclass:: Orientation
    :members:

Imposition objects
^^^^^^^^^^^^^^^^^^

Befor performing imposition, the way input pages will be placed on output pages
is computed and stored in the following objects.

.. autoclass:: Coordinates

.. autoclass:: ImpositionPage

.. autoclass:: ImpositionMatrix

Performing imposition
^^^^^^^^^^^^^^^^^^^^^

At last, imposition can be performed.

.. autofunction:: pypdf_impose

"""

from PyPDF2.generic import NameObject, createStringObject

try:
    from enum import Enum
except ImportError:
    # pylint: disable=import-error
    from enum34 import Enum

import PyPDF2
import logging
import math

VERSION = "0.1.1"
__AUTHOR__ = "Louis Paternault (spalax@gresille.org)"
__COPYRIGHT__ = "(C) 2014-2015 Louis Paternault. GNU GPL 3 or later."

LOGGER = logging.getLogger(__name__)

class Direction(Enum):
    """Direction (horizontal or vertical)"""
    # pylint: disable=too-few-public-methods

    vertical = False
    horizontal = True

    def __str__(self):
        return self.name[0].upper()

    @classmethod
    def from_char(cls, char):
        """Return :class:`Direction` object corresponding to `char`.

        Character can be one of ``h`` or ``v``, ignoring case.
        """
        if char.lower() == 'h':
            return cls.horizontal
        elif char.lower() == 'v':
            return cls.vertical
        else:
            raise ValueError(
                "{}: Argument '{}' is not recognised as a direction.".format(
                    cls.__name__,
                    char
                    )
                )

#: Vertical direction
VERTICAL = Direction.vertical

#: Horizontal direction
HORIZONTAL = Direction.horizontal

class Orientation(Enum):
    """Two dimensions orientation"""
    # pylint: disable=too-few-public-methods

    north = 90
    south = 270

    def __str__(self):
        return self.name[0].upper()

    def fold(self, rotate):
        """Return the symmetrical orientation, according to an horizontal axe.

        :param bool rotate: If true, object is also applied a 180° rotation.

        >>> Orientation(90).fold(False)
        <Orientation.north: 90>
        >>> Orientation(270).fold(False)
        <Orientation.south: 270>
        >>> Orientation(90).fold(True)
        <Orientation.south: 270>
        >>> Orientation(270).fold(True)
        <Orientation.north: 90>
        """
        if rotate:
            return Orientation((-self.value) % 360)
        else:
            return Orientation((180 - self.value) % 360)

#: North orientation
NORTH = Orientation.north

#: South orientation
SOUTH = Orientation.south

_ORIENTATION_MATRIX = {
    NORTH.value: [1, 0, 0, 1],
    SOUTH.value: [-1, 0, 0, -1],
    }

class Coordinates:
    """Two-dimensions coordinates."""
    # pylint: disable=too-few-public-methods

    x = 0
    y = 0

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Coordinates(
            self.x + other.x,
            self.y + other.y,
            )

    def __sub__(self, other):
        return Coordinates(
            self.x - other.x,
            self.y - other.y,
            )

    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    def __repr__(self):
        return "{}({}, {})".format(
            self.__class__.__name__,
            self.x,
            self.y,
            )

class ImpositionPage:
    """Page, on an imposition matrix: a page number, and an orientation."""
    # pylint: disable=too-few-public-methods

    def __init__(self, number, orientation):
        self.orientation = orientation
        self.number = number

    def __str__(self):
        return "{: 3}{}".format(
            self.number,
            self.orientation,
            )

    def __eq__(self, other):
        return (
            other.number == self.number
            and
            other.orientation == self.orientation
            )

    def fold(self, page_max, rotate):
        """Return the symmetrical page to `self`.

        :arg bool orientation: Fold orientation.
        :arg int page_max: Maximum page number.
        """
        return ImpositionPage(
            page_max - self.number,
            self.orientation.fold(rotate),
            )

class ImpositionMatrix:
    """Matrix of an imposition: array of numbered, oriented pages.

        :param list folds: Sorted list of folds, as a list of :class:`Direction`
            instances.
        :param str bind: One of ``top``, ``bottom``, ``left``, ``right``: edge on
            which the final book is to be folded.
    """

    def __init__(self, folds, bind):
        size = Coordinates(
            2**folds.count(HORIZONTAL),
            2**folds.count(VERTICAL),
            )

        # Initialisation
        self.folds = []
        self.matrix = [
            [
                None
                for y
                in range(size.y)
                ]
            for x
            in range(2*size.x)
            ]
        self.bind = bind

        # First, fake, fold (corresponding to recto/verso)
        if bind in ["top", "right"]:
            self.matrix[0][0] = ImpositionPage(0, NORTH)
        else: # bind in ["bottom", "left"]:
            self.matrix[-1][-1] = ImpositionPage(0, NORTH)
        self.fold(HORIZONTAL, rotate=(bind in ["top", "bottom"]))

        # Actual folds
        for i in folds:
            self.fold(i)

    @property
    def vfolds(self):
        """Return the number of vertical folds"""
        return self.folds.count(VERTICAL)

    @property
    def hfolds(self):
        """Return the number of horizontal folds"""
        return self.folds.count(HORIZONTAL)

    @property
    def size(self):
        """Return the size of the matrix, as a :class:`Coordinates`."""
        return Coordinates(
            len(self.matrix),
            len(self.matrix[0]),
            )

    def fold(self, orientation, rotate=None):
        """Perform a fold according to `orientation`."""
        if rotate is None:
            if orientation == HORIZONTAL:
                rotate = (self.bind in ["top", "bottom"])
            else:
                rotate = (self.bind in ["left", "right"])
        virtualpage_size = Coordinates(
            self.size.x//2**self.hfolds,
            self.size.y//2**self.vfolds,
            )
        for x in range(0, self.size.x, virtualpage_size.x):
            for y in range(0, self.size.y, virtualpage_size.y):
                self._virtualpage_fold(
                    Coordinates(x, y),
                    virtualpage_size,
                    orientation,
                    rotate,
                    )
        self.folds.append(orientation)

    def __getitem__(self, item):
        if isinstance(item, Coordinates):
            return self.matrix[item.x][item.y] # pylint: disable=no-member
        elif isinstance(item, tuple) and len(item) == 2:
            if isinstance(item[0], int) and isinstance(item[1], int):
                return self.matrix[item[0]][item[1]]
        raise TypeError()

    def as_list(self):
        """Return ``self``, as a list of lists of :class:`ImpositionPage`."""
        return [
            [
                self[(x, y)]
                for y in range(self.size.y)
                ]
            for x in range(self.size.x)
            ]


    def __setitem__(self, item, value):
        if len(item) == 1:
            item = item[0]
            if isinstance(item, Coordinates):
                self.matrix[item.x][item.y] = value
                return
        elif len(item) == 2:
            if isinstance(item[0], int) and isinstance(item[1], int):
                self.matrix[item[0]][item[1]] = value
                return
        raise TypeError()

    def _virtualpage_find_page(self, corner, size):
        """Find the actual page on a virtual page.

        A virtual page should contain only one actual page. Return the coorditanes
        of this page (relative to the matrix).

        :arg Coordinates corner: Coordinates of the low left corner of the
            virtual page.
        :arg Coordinates size: Size of the virtual page.
        """
        for coordinates in [
                corner,
                corner + Coordinates(size.x-1, 0),
                corner + Coordinates(0, size.y-1),
                corner + size - Coordinates(1, 1),
            ]:
            if self[coordinates] is not None:
                return coordinates

    def _virtualpage_fold(self, corner, size, orientation, rotate):
        """Fold a virtual page

        :arg Coordinates corner: Low left corner of the virtual page.
        :arg Coordinates size: Size of the virtual page.
        :arg bool orientation: Fold orientation.
        :arg bool rotate: Should pages be rotated?
        """
        page = self._virtualpage_find_page(corner, size)
        if orientation == HORIZONTAL:
            self[
                2 * corner.x + size.x - page.x - 1, # Vertical symmetrical
                page.y,
                ] = self[page].fold(2**(len(self.folds)+1)-1, rotate)
        else:
            self[
                page.x,
                2 * corner.y + size.y - page.y - 1, # Horizontal symmetrical
                ] = self[page].fold(2**(len(self.folds)+1)-1, rotate)

    def __str__(self):
        return "\n".join([
            " ".join([
                str(page)
                for page
                in row
                ])
            for row
            in reversed(list(zip(*self.matrix)))
            ])

    @property
    def recto(self):
        """Return the recto of the matrix."""
        return self.matrix[len(self.matrix)//2:]

    @property
    def verso(self):
        """Return the verso of the matrix."""
        return self.matrix[:len(self.matrix)//2]


def _get_input_pages(pdfsize, sectionsize, section_number, last):
    """Return the input pages, with `None` added to fit `sectionsize`."""
    return (
        [i for i in range(pdfsize - last)] +
        [None for i in range(pdfsize, section_number * sectionsize)] +
        [i for i in range(pdfsize - last, pdfsize)]
        )

def _get_pdf_size(page):
    """Return the size (width x height) of page."""
    return (
        page.mediaBox.lowerRight[0] - page.mediaBox.lowerLeft[0],
        page.mediaBox.upperRight[1] - page.mediaBox.lowerRight[1],
        )

def _set_metadata(inpdf, outpdf):
    """Copy and set metadata from inpdf to outpdf.
    """
    #Source:
    #    http://two.pairlist.net/pipermail/reportlab-users/2009-November/009033.html
    try:
        # pylint: disable=protected-access
        # Since we are accessing to a protected membre, which can no longer exist
        # in a future version of PyPDF2, we prevent errors.
        infodict = outpdf._info.getObject()
        infodict.update(inpdf.getDocumentInfo())
        infodict.update({
            NameObject('/Creator'): createStringObject(
                'PdfImpose, using the PyPDF2 library — http://git.framasoft.org/spalax/pdfimpose'
                )
        })
    except AttributeError:
        LOGGER.warning("Could not copy metadata from source document.")

def pypdf_impose(matrix, pdf, last, callback=None):
    """Return the pdf object corresponding to imposition of ``pdf``.

    :param ImpositionMatrix matrix: Imposition is performed according to this matrix.
    :param PyPDF2.PdfFileReader pdf: Input file, to be imposed.
    :param int last: Number of pages to keep as last pages (same meaning as
        same argument in :func:`impose`).
    :param function callback: Callback function (exactly the same meaning as
        same argument in :func:`impose`).
    :rtype: PyPDF2.PdfFileWriter
    """
    # pylint: disable=too-many-locals

    if callback is None:
        callback = lambda x, y: None
    width, height = _get_pdf_size(pdf.getPage(0))
    output = PyPDF2.PdfFileWriter()

    sectionsize = matrix.size.x * matrix.size.y
    section_number = int(math.ceil(pdf.numPages / sectionsize))
    inputpages = _get_input_pages(pdf.numPages, sectionsize, section_number, last)
    rectoverso = [matrix.verso, matrix.recto]
    pagecount = 0
    for outpagenumber in range(2 * section_number):
        currentoutputpage = output.addBlankPage(
            matrix.size.x * width // 2,
            matrix.size.y * height,
            )
        for x in range(len(rectoverso[outpagenumber%2])):
            for y in range(len(rectoverso[outpagenumber%2][x])):
                pagenumber = (
                    (outpagenumber//2)*sectionsize
                    + rectoverso[outpagenumber%2][x][y].number
                    )
                if inputpages[pagenumber] is not None:
                    if rectoverso[outpagenumber%2][x][y].orientation == NORTH:
                        currentoutputpage.mergeTransformedPage(
                            pdf.getPage(inputpages[pagenumber]),
                            _ORIENTATION_MATRIX[NORTH.value] + [x*width, y*height],
                            )
                    else:
                        currentoutputpage.mergeTransformedPage(
                            pdf.getPage(inputpages[pagenumber]),
                            _ORIENTATION_MATRIX[SOUTH.value] + [(x+1)*width, (y+1)*height],
                            )
                    pagecount += 1
                    callback(pagecount, pdf.numPages)

    _set_metadata(pdf, output)
    return output

def impose(inname, outname, fold, bind, last, callback=None):
    """Perform imposition on a pdf file.

    :param str inname: Name of input file.
    :param str outname: Name of output file.
    :param list fold: List of folds to perform, as a list of :class:`Direction`
        constants.
    :param int last: Number of pages to keep last. If necessary, blank pages
        are added at the end of the pdf file. If this argument is non zero,
        those blank pages are added, while keeping some pages at the end. This
        may be useful to keep the back-cover at the end of the file, for
        instance.
    :param function callback: Callback function, to provide user feedback. This
        functions is called each time one page (of the input file) has been
        processed, with the page number and total page numbers as arguments. It
        should return immediatly. This argument can be ``None`` to disable
        this.
    """
    # pylint: disable=too-many-arguments
    pypdf_impose(
        matrix=ImpositionMatrix(fold, bind),
        pdf=PyPDF2.PdfFileReader(inname),
        last=last,
        callback=callback,
        ).write(outname)

