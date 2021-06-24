# Copyright 2011-2021 Louis Paternault
#
# Pdfimpose is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pdfimpose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with pdfimpose.  If not, see <http://www.gnu.org/licenses/>.

"""Common classes and function to different imposition schemas."""

import argparse
import contextlib
import dataclasses
import decimal
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
    r"(?P<slope>-?\d+(.\d+)?)x(?P<yintercept>[+-]\d+(.\d+)?)?(?P<unit>[^\d]+)?"
)


def _type_length(text):
    return float(papersize.parse_length(text))


def _type_creep(text):
    """Turn a linear function (as a string) into a linear Python function.

    >>> _type_creep("-2x+3")(5)
    -7
    >>> _type_creep("2.5x")(2)
    5.0
    >>> _type_creep("7")(9)
    7
    >>> _type_creep("2x-5pc")(3)
    12
    """
    if "x" in text:
        if match := RE_CREEP.match(text):
            try:
                groups = match.groupdict()
                slope = decimal.Decimal(groups["slope"])
                if groups["yintercept"]:
                    yintercept = decimal.Decimal(groups["yintercept"])
                else:
                    yintercept = 0
                if groups["unit"]:
                    unit = papersize.UNITS[groups["unit"]]
                else:
                    unit = 1
                return lambda x: (slope * x + yintercept) * unit
            except KeyError as error:
                raise argparse.ArgumentTypeError(
                    "Invalid creep function "
                    "(must be a linear function, with an optional unit, e.g. '2.3x-1mm')."
                ) from error
    return lambda x: _type_length(text)


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
            "files", metavar="FILEs", help="PDF files to process", nargs="*", type=str
        )

        self.add_argument(
            "--output",
            "-o",
            metavar="FILE",
            help='Destination file. Default is "-impose" appended to first source file.',
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
                    "This is a linear fonction of 'x', the number of folds "
                    "(e.g. '.1x+2mm')."
                ),
                type=_type_creep,
                default=lambda x: 0,
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

    def parse_args(self, *args, **kwargs):
        args = super().parse_args(*args, **kwargs)

        for i, path in enumerate(args.files):
            if (not os.path.exists(path)) and os.path.exists(f"{path}.pdf"):
                args.files[i] = f"{path}.pdf"

        if args.output is None:
            source = pathlib.Path(args.files[0])
            args.output = "{}-impose{}".format(
                source.parent / source.stem, source.suffix
            )

        return args


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
    omargin: float = 0
    rotate: dataclasses.InitVar[int] = 0

    def __post_init__(self, rotate):
        for x, y in self.coordinates():
            self[x, y].rotate = (self[x, y].rotate + rotate) % 360

    @property
    def signature(self):
        """Signature of output pages.

        For instance, if the output page fits 6 pages
        (as a matrix of 3 horizontal pages and 2 vertical pages),
        the signature is `(3, 2)`.
        """
        return (len(self.pages), len(self.pages[0]))

    def __getitem__(self, coord):
        return self.pages[coord[0]][coord[1]]

    def coordinates(self):
        """Iterate the list of coordinates of source pages."""
        for x in range(len(self.pages)):
            for y in range(len(self.pages[x])):
                yield (x, y)

    def stack(self, number):
        """Return a copy of this matrix, where each page number is incremented by `number`."""
        return Matrix(
            [
                [
                    dataclasses.replace(self[x, y], number=self[x, y].number + number)
                    for y in range(self.signature[1])
                ]
                for x in range(self.signature[0])
            ],
            omargin=self.omargin,
        )


@dataclasses.dataclass
class AbstractImpositor:
    """Perform imposition of source files onto output file.

    This is an abstract method, with common methods,
    to be inherited by imposition schemas.
    """

    last: int = 0
    omargin: float = 0
    mark: list[str] = dataclasses.field(default_factory=list)

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

    def crop_marks(self, number, matrix, outputsize, inputsize):
        """Yield coordinates of crop marks."""
        # pylint: disable=unused-argument, no-self-use
        yield from []

    def bind_marks(self, number, matrix):
        """Yield coordinates of bind marks."""
        # pylint: disable=unused-argument, no-self-use
        yield from []

    @contextlib.contextmanager
    def read(self, files):
        """TODO

        At the end of this function, the return value has exactly the right
        number of pages to fit on a dest page.
        """
        with pdf.Reader(files) as reader:
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

    def stack_matrixes(self, sheet, repeat: int):
        """Repeat a given matrix, so that resulting sheets can be stacked on top of each others.

        :param list[Matrix] sheet: A list of matrixes.
        :param int repeat: Number of repetitions of the matrixes given in argument.

        For instance, given a single matrix containing pages from 1 to 8,
        with `repeat=3`, this method will yield:
        - one matrix with pages from 1 to 8;
        - one matrix with pages from 9 to 16;
        - one matrix with pages from 17 to 24.

        This method is an alternative to :meth:`Impositor.insert_matrixes`.
        """
        # pylint: disable=no-self-use
        # We assume that every page is the same size
        assert len(set(page.signature for page in sheet)) == 1

        size = len(sheet) * sheet[0].signature[0] * sheet[0].signature[1]
        for i in range(repeat):
            for page in sheet:
                yield page.stack(i * size)

    def topleft(self, matrix, coord, size):
        """Compute and return the coordinates of the top left corner of a page.

        It answers the question:
        Given the imposition matrix of source pages of a given size,
        where should be the source page `(x, y)` placed on the output page?

        :param Matrix matrix: Imposition matrix.
        :param tuple coord: Coordinate of the source page
            (relative to the output page signature): `coord = (0, 2)` means
            'the first page from the left, third from the top'.
        """
        left = self.omargin
        x, y = coord
        width, height = size
        for i in range(x):
            left += matrix[i, y].left + matrix[i, y].right
            if matrix[i, y].rotate in (90, 270):
                left += height
            else:
                left += width
        left += matrix[x, y].left

        top = self.omargin
        for j in range(y):
            top += matrix[x, j].top + matrix[x, j].bottom
            if matrix[x, j].rotate in (90, 270):
                top += width
            else:
                top += height
        top += matrix[x, y].top

        return (left, top)

    def pagesize(self, matrix, sourcesize):
        """Compute and return the size of the output page.

        :param Matrix matrix: Imposition matrix.
        :param tuple sourcesize: Size of the source pages.
        """
        lines = set()
        for y in range(matrix.signature[1]):
            line = 2 * self.omargin
            for x in range(matrix.signature[0]):
                line += matrix[x, y].left + matrix[x, y].right
                if matrix[x, y].rotate in (90, 270):
                    line += sourcesize[1]
                else:
                    line += sourcesize[0]
            lines.add(line)

        rows = set()
        for x in range(matrix.signature[0]):
            row = 2 * self.omargin
            for y in range(matrix.signature[1]):
                row += matrix[x, y].top + matrix[x, y].bottom
                if matrix[x, y].rotate in (90, 270):
                    row += sourcesize[0]
                else:
                    row += sourcesize[1]
            rows.add(row)

        return (max(lines), max(rows))

    def impose(self, files, output):
        """Perform imposition.

        :param list files: List of files (as names) to impose.
        :param str output: Name of the output file.
        """
        with self.read(files) as reader, self.write(output) as writer:
            for matrix in self.matrixes(len(reader)):
                destpage_size = self.pagesize(matrix, reader.size)
                destpage = writer.new_page(*destpage_size)
                for x, y in matrix.coordinates():
                    if reader[matrix[x, y].number] is None:
                        # Blank page
                        continue

                    sourcepage = reader[matrix[x, y].number]
                    writer.insert(
                        destpage,
                        sourcepage,
                        topleft=self.topleft(matrix, (x, y), reader.size),
                        rotate=matrix[x, y].rotate,
                    )

                if "crop" in self.mark:
                    for point1, point2 in self.crop_marks(
                        destpage, matrix, destpage_size, reader.size
                    ):
                        writer[destpage].draw_line(point1, point2)
                if "bind" in self.mark:
                    for rect, color in self.bind_marks(destpage, matrix):
                        writer[destpage].draw_rect(rect, color=color, fill=color)
