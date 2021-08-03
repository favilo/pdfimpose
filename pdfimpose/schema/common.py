# Copyright 2011-2021 Louis Paternault
#
# This file is part of pdfimpose.
#
# Pdfimpose is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pdfimpose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with pdfimpose.  If not, see <https://www.gnu.org/licenses/>.

"""Common classes and function to different imposition schemas.

Each submodule provides:

- a class :class:`SCHEMAImpositor`, where:

  - its :meth:`SCHEMAImpositor.__init__` method takes the schema arguments
    (which are more or less the same ones as the corresponding command line subcommand);
  - its :meth:`SCHEMAImpositor.impose` method take
    the source and destination file names as arguments, and performs the imposition;

- a function :func:`impose`, which is barely more than a wrapper to the aforementionned class.

:class:`Margins`
----------------

.. autoclass:: Margins

:class:`Page`
-------------

.. autoclass:: Page

:class:`Matrix`
---------------

.. autoclass:: Matrix

:class:`AbstractImpositor`
--------------------------

.. autoclass:: AbstractImpositor

"""

import argparse
import contextlib
import dataclasses
import math
import numbers
import pathlib
import os
import re

import papersize

from .. import pdf
from .. import UserError

BIND2ANGLE = {
    "left": 0,
    "top": 90,
    "right": 180,
    "bottom": 270,
}

RE_CREEP = re.compile(
    r"(?P<slope>-?\d*(.\d+)?)s(?P<yintercept>[+-]\d+(.\d+)?)?(?P<unit>[^\d]+)?"
)


def nocreep(s):
    """Dummy creep function, which always returns 0."""
    # pylint: disable=invalid-name, unused-argument
    return 0


def _type_length(text):
    return float(papersize.parse_length(text))


def _type_signature(text):
    """Check type of '--signature' argument."""
    try:
        if text.count("x") != 1:
            raise ValueError()
        left, right = map(int, text.split("x"))

        if left <= 0 or right <= 0:
            raise ValueError()

        return (left, right)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            """Argument must be "WIDTHxHEIGHT", """
            """where both WIDTH and HEIGHT are non-zero positive integers."""
        ) from error


def _type_papersize(text):
    return tuple(map(float, papersize.parse_papersize(text)))


def _type_creep(text):
    """Turn a linear function (as a string) into a linear Python function.

    >>> _type_creep("-2s+3")(5)
    -7.0
    >>> _type_creep("2.5s")(2)
    5.0
    >>> _type_creep("7")(9)
    7.0
    >>> _type_creep("2s-5pc")(3)
    12.0
    """
    if "s" in text:
        if match := RE_CREEP.match(text):
            try:
                groups = match.groupdict()
                if groups["slope"]:
                    slope = float(groups["slope"])
                else:
                    slope = 1
                if groups["yintercept"]:
                    yintercept = float(groups["yintercept"])
                else:
                    yintercept = 0
                if groups["unit"]:
                    unit = float(papersize.UNITS[groups["unit"]])
                else:
                    unit = 1
                return lambda s: (slope * s + yintercept) * unit
            except KeyError as error:
                raise argparse.ArgumentTypeError(
                    "Invalid creep function "
                    "(must be a linear function, with an optional unit, e.g. '2.3s-1mm')."
                ) from error
    return lambda s: _type_length(text)


def _type_positive_int(text):
    """Return ``int(text)`` iff ``text`` represents a positive integer."""
    try:
        if int(text) >= 0:
            return int(text)
        else:
            raise ValueError()
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "Argument must be a positive integer."
        ) from error


class ArgumentParser(argparse.ArgumentParser):
    """A "pre-seeded" argument parser, with configuration common to several schemas."""

    def __init__(self, subcommand, options=None, **kwargs):
        if options is None:
            options = []

        if "prog" not in kwargs:
            kwargs["prog"] = f"pdfimpose {subcommand}"

        super().__init__(**kwargs)

        self.add_argument(
            "files",
            metavar="FILEs",
            help='PDF files to process. If "-", read from standard input.',
            nargs="*",
            type=str,
        )

        self.add_argument(
            "--output",
            "-o",
            metavar="FILE",
            help=(
                'Destination file. Default is "-impose" appended to first source file. '
                'If "-", print to standard output.'
            ),
            type=str,
        )

        if "imargin" in options:
            self.add_argument(
                "--imargin",
                "-m",
                help="Set margin added to input pages when imposed on the output page.",
                default=0,
                type=_type_length,
            )

        if "omargin" in options:
            self.add_argument(
                "--omargin",
                "-M",
                help="Set margin added to output pages.",
                default=0,
                type=_type_length,
            )

        if "creep" in options:
            self.add_argument(
                "--creep",
                "-c",
                help=(
                    "Set creep (space added at each fold). "
                    "This is a linear fonction of 's', the number of inner sheets "
                    "(e.g. '.1s+2mm')."
                ),
                type=_type_creep,
                default=nocreep,
            )

        if "last" in options:
            self.add_argument(
                "--last",
                "-l",
                help=(
                    "Number of pages to keep as last pages. "
                    "Useful to keep the back cover as a back cover."
                ),
                type=_type_positive_int,
                default=0,
            )

        if "bind" in options:
            self.add_argument(
                "--bind",
                "-b",
                help="Binding edge.",
                choices=["left", "right", "top", "bottom"],
                default="left",
            )

        if "mark" in options:
            self.add_argument(
                "--mark",
                "-k",
                help="List of marks to add (crop or bind). Can be given multiple times.",
                choices=["bind", "crop"],
                action="append",
                default=[],
            )

        if "signature" in options or "format" in options:
            group = self.add_mutually_exclusive_group()

        if "signature" in options:
            group.add_argument(
                "--signature",
                "-s",
                metavar="WIDTHxHEIGHT",
                type=_type_signature,
                help="Size of the destination pages (relative to the source page), e.g. 2x3.",
                default=None,
            )

        if "format" in options:
            group.add_argument(
                "--format",
                "-f",
                type=_type_papersize,
                help=(
                    "Put as much source pages into the destination page of the given format. "
                    "Note that margins are ignored when computing this; "
                    "if options --imargin and --omargin are set, "
                    "the resulting file might be larger than the required format."
                ),
                default=None,
            )

    def parse_args(self, *args, **kwargs):
        args = super().parse_args(*args, **kwargs)

        for i, path in enumerate(args.files):
            if (not os.path.exists(path)) and os.path.exists(f"{path}.pdf"):
                args.files[i] = f"{path}.pdf"

        if args.output is None or args.output == "-":
            if args.files:
                source = pathlib.Path(args.files[0])
                args.output = "{}-impose{}".format(
                    source.parent / source.stem, source.suffix
                )
            else:
                args.output = None

        return args


def compute_signature(source, dest):
    """Compute the signature to fit as many as possible sources in dest.

    :param tuple[float] source: Size of the source page.
    :param tuple[float] dest: Size of the destination page.

    Return a tuple ``(signature, rotated)``, where:
    - ``signature`` is a tuple of integers:
      ``(2, 3)`` means that the best fit is 2 source pages wide by 3 source
      pages tall on the destination page;
    - ``rotated`` is a boolean, indicating that the destination page has to be
      rotated to fit the signature.
    """
    notrotated = (
        math.floor(round(dest[0] / source[0], 6)),
        math.floor(round(dest[1] / source[1], 6)),
    )
    rotated = (
        math.floor(round(dest[1] / source[0], 6)),
        math.floor(round(dest[0] / source[1], 6)),
    )

    if 0 in notrotated and 0 in rotated:
        raise UserError("The source page is too big to fit in the destination page.")
    if notrotated[0] * notrotated[1] > rotated[0] * rotated[1]:
        return notrotated, False
    return rotated, True


@dataclasses.dataclass
class Margins:
    """Left, right, top, bottom margins.

    - If the constructor has only one argument, all four margins are equal to this value.
    - If the constructor has no argument, all four margins are 0.
    """

    left: float = 0
    right: float = None
    top: float = None
    bottom: float = None

    def __post_init__(self):
        if self.right is None:
            self.right = self.left
        if self.top is None:
            self.top = self.left
        if self.bottom is None:
            self.bottom = self.left


@dataclasses.dataclass
class Page:
    """A virtual page: a page number, a rotation, and margins."""

    number: int
    rotate: int = 0
    left: int = 0
    right: int = 0
    top: int = 0
    bottom: int = 0


@dataclasses.dataclass
class Matrix:
    """Imposition matrix.

    This matrix does not contain actual pages,
    but an array of which source page numbers should go where on one output page.
    """

    pages: list[list[Page]] = dataclasses.field(default_factory=lambda: [[]])
    rotate: dataclasses.InitVar[int] = 0

    def __post_init__(self, rotate):
        for x, y in self.coordinates():
            self[x, y].rotate = (self[x, y].rotate + rotate) % 360

    def copy(self):
        """Return a copy of this object.

        Changes can be applied.
        """
        return self.__class__(
            [
                [dataclasses.replace(self[x, y]) for y in range(self.height)]
                for x in range(self.width)
            ]
        )

    @property
    def signature(self):
        """Signature of output pages.

        For instance, if the output page fits 6 pages
        (as a matrix of 3 horizontal pages and 2 vertical pages),
        the signature is `(3, 2)`.
        """
        return (self.width, self.height)

    @property
    def width(self):
        """Horizontal number of source pages."""
        return len(self.pages)

    @property
    def height(self):
        """Vertical number of source pages."""
        return len(self.pages[0])

    def __getitem__(self, coord):
        return self.pages[coord[0]][coord[1]]

    def coordinates(self):
        """Iterate the list of coordinates of source pages."""
        # pylint: disable=consider-using-enumerate
        for x in range(len(self.pages)):
            for y in range(len(self.pages[x])):
                yield (x, y)

    def stack(self, number):
        """Return a copy of this matrix, where each page number is incremented by `number`."""
        return Matrix(
            [
                [
                    dataclasses.replace(self[x, y], number=self[x, y].number + number)
                    for y in range(self.height)
                ]
                for x in range(self.width)
            ],
        )

    def topleft(self, coord, size):
        """Compute and return the coordinates of the top left corner of a page.

        It answers the question:
        Given the imposition matrix of source pages of a given size,
        where should be the source page `(x, y)` placed on the output page?

        :param tuple[int, int] coord: Coordinate of the source page
            (relative to the output page signature): `coord = (0, 2)` means
            'the first page from the left, third from the top'.
        :param tuple[float, float] size: Size of source pages.
        """
        left = 0
        x, y = coord
        width, height = size
        for i in range(x):
            left += self[i, y].left + self[i, y].right
            if self[i, y].rotate in (90, 270):
                left += height
            else:
                left += width
        left += self[x, y].left

        top = 0
        for j in range(y):
            top += self[x, j].top + self[x, j].bottom
            if self[x, j].rotate in (90, 270):
                top += width
            else:
                top += height
        top += self[x, y].top

        return (left, top)

    def pagesize(self, size):
        """Compute and return the size of the output page.

        :param tuple[float, float] size: Size of the source pages.
        """
        lines = set()
        for y in range(self.height):
            line = 0
            for x in range(self.width):
                line += self[x, y].left + self[x, y].right
                if self[x, y].rotate in (90, 270):
                    line += size[1]
                else:
                    line += size[0]
            lines.add(line)

        rows = set()
        for x in range(self.width):
            row = 0
            for y in range(self.height):
                row += self[x, y].top + self[x, y].bottom
                if self[x, y].rotate in (90, 270):
                    row += size[0]
                else:
                    row += size[1]
            rows.add(row)

        return (max(lines), max(rows))


@dataclasses.dataclass
class AbstractImpositor:
    """Perform imposition of source files onto output file.

    This is an abstract method, with common methods,
    to be inherited by imposition schemas.
    """

    last: int = 0
    omargin: Margins = Margins()
    mark: list[str] = dataclasses.field(default_factory=list)
    creep = nocreep

    def __post_init__(self):
        if isinstance(self.omargin, numbers.Real):
            self.omargin = Margins(self.omargin)

    def blank_page_number(self, source):
        """Return the number of blank pages to insert.

        For instance, if the source document has 13 pages,
        and the output document fits 8 source pages per destination pages,
        3 source blank pages have to be inserted.
        """
        raise NotImplementedError()

    def matrixes(self, pages: int):
        """Yield the list of all imposition matrixes."""
        raise NotImplementedError()

    def _crop_space(self):
        left = right = bottom = top = 20
        if top > self.omargin.top:
            top = self.omargin.top / 2
        if bottom > self.omargin.bottom:
            bottom = self.omargin.bottom / 2
        if left > self.omargin.left:
            left = self.omargin.left / 2
        if right > self.omargin.right:
            right = self.omargin.right / 2
        return left, right, bottom, top

    def crop_marks(self, number, total, matrix, outputsize, inputsize):
        """Yield coordinates of crop marks."""
        # pylint: disable=unused-argument, no-self-use, too-many-arguments
        yield from []

    def bind_marks(self, number, total, matrix, outputsize, inputsize):
        """Yield coordinates of bind marks."""
        # pylint: disable=unused-argument, no-self-use, too-many-arguments
        yield from []

    @contextlib.contextmanager
    def read(self, files):
        """Context manager to read a list of files.

        Return an object that can be processed as a list of pages
        (regardless of the original files).

        At the end of this function, the return value has exactly the right
        number of pages to fit on a dest page.

        Note that `files` can be either a list of file, or a :class:`pdfimpose.pdf.Reader` object,
        but only the list of files (names or io.BytesIO streams) is supported:
        the other type is an implementation detail.
        """
        if isinstance(files, pdf.Reader):
            opener = files
        else:
            opener = pdf.Reader(files)

        with opener as reader:
            if len(reader) == 0:
                raise UserError("Input files do not have any page.")
            reader.set_final_blank_pages(
                self.blank_page_number(len(reader)), len(reader) - self.last
            )
            yield reader

    @staticmethod
    @contextlib.contextmanager
    def write(output):
        """Write output file to disk."""
        with pdf.Writer(output) as writer:
            yield writer

    def stack_matrixes(self, matrixes, step: int, repeat: int):
        """Iterate over copies of the matrixes, incrementing pages numbers by ``step``.

        :param list[Matrix] matrix: A list of matrixes.
        :param int repeat: Number of repetitions of the matrixes given in argument.
        :param int step: At each repetition, is page is increased by this number.

        For instance, given a single matrix containing pages from 1 to 8,
        with `repeat=3` and `step=8`, this method will yield:
        - one matrix with pages from 1 to 8;
        - one matrix with pages from 9 to 16;
        - one matrix with pages from 17 to 24.

        This method is an alternative to :meth:`Impositor.insert_matrixes`.
        """
        # pylint: disable=no-self-use
        for i in range(repeat):
            for matrix in matrixes:
                yield matrix.stack(i * step)

    def insert_sheets(self, matrixes, sheets, pages, pagespersheet):
        """Iterates over "copies" of matrixes that can be inserted into each other.

        For instance, if `matrixes` is the single matrix 1|2,
        a set of sheets that can be inserted into each other (as in magazines, for instance),
        is: 1|8 2|7 3|6 4|5.

        :param matrixes: Matrixes to copy and insert into each other.
        :param int sheets: Number of inserted sheets.
        :param int pages: Total number of pages in the source document.
        :param int pagespersheet: Nomber of source pages per output sheets.
        """
        for matrix in matrixes:
            for x, y in matrix.coordinates():
                # Add creep
                if x % 2 == 0:
                    matrix[x, y].right = self.creep(sheets) / 2
                else:
                    matrix[x, y].left = self.creep(sheets) / 2

                # Change page numbers
                if matrix[x, y].number < pagespersheet:
                    matrix[x, y].number += pagespersheet * sheets
                else:
                    matrix[x, y].number = (
                        pages - (sheets + 2) * pagespersheet + matrix[x, y].number
                    )

            yield matrix

    def impose(self, files, output):
        """Perform imposition.

        :param list files: List of files (as names or io.BytesIO tream) to impose.
        :param str output: Name of the output file.

        Warning: You might have noticed that `files` can also be a list of
        :class:`fitz.Document` or a :class:`pdfimpose.pdf.Reader` object.
        This is an implementation detail, and can change without notice in the future.
        Use at your own risk.
        """
        with self.read(files) as reader, self.write(output) as writer:
            for matrix in self.matrixes(len(reader)):
                destpage_size = matrix.pagesize(reader.size)
                destpage = writer.new_page(*destpage_size)
                for x, y in matrix.coordinates():
                    if reader[matrix[x, y].number] is None:
                        # Blank page
                        continue

                    sourcepage = reader[matrix[x, y].number]
                    writer.insert(
                        destpage,
                        sourcepage,
                        topleft=matrix.topleft((x, y), reader.size),
                        rotate=matrix[x, y].rotate,
                    )

                if "crop" in self.mark:
                    for point1, point2 in self.crop_marks(
                        destpage, len(reader), matrix, destpage_size, reader.size
                    ):
                        writer[destpage].draw_line(point1, point2)
                if "bind" in self.mark:
                    for rect in self.bind_marks(
                        destpage, len(reader), matrix, destpage_size, reader.size
                    ):
                        writer.draw_rectangle(destpage, rect)
            writer.set_metadata(reader)
