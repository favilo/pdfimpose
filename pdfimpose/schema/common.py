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
            except KeyError:
                raise argparse.ArgumentTypeError(
                    "Invalid creep function (must be a linear function, with an optional unit, e.g. '2.3x-1mm')."
                )
    return lambda x: _type_length(text)


def _type_positive_int(text):
    """Return ``int(text)`` iff ``text`` represents a positive integer."""
    try:
        if int(text) >= 0:
            return int(text)
        else:
            raise ValueError()
    except ValueError:
        raise argparse.ArgumentTypeError("Argument must be a positive integer.")


class ArgumentParser(argparse.ArgumentParser):
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
                help="Set creep (space added at each fold). This is a linear fonction of 'x', the number of folds.",
                type=_type_creep,
                default=lambda x: 0,
            )

        if "last" in options:
            self.add_argument(
                "--last",
                "-l",
                help="Number of pages to keep as last pages. Useful to keep the back cover as a back cover.",
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
    number: int
    rotate: int = 0
    left: int = 0
    right: int = 0
    top: int = 0
    bottom: int = 0


@dataclasses.dataclass
class Matrix:

    pages: list[list[Page]] = dataclasses.field(default_factory=lambda: [[]])
    omargin: float = 0
    rotate: dataclasses.InitVar[int] = 0

    def __post_init__(self, rotate):
        for x, y in self.coordinates():
            self[x, y].rotate = (self[x, y].rotate + rotate) % 360

    @property
    def signature(self):
        return (len(self.pages), len(self.pages[0]))

    def __getitem__(self, coord):
        return self.pages[coord[0]][coord[1]]

    def coordinates(self):
        for x in range(len(self.pages)):
            for y in range(len(self.pages[x])):
                yield (x, y)

    def stack(self, number):
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

    last: int = 0
    omargin: float = 0

    def blank_page_number(self, source):
        raise NotImplementedError()

    def matrixes(self):
        raise NotImplementedError()

    @contextlib.contextmanager
    def read(self, files):
        """TODO

        At the end of this function, the return value has exactly the right number of pages to fit on a dest page.
        """
        with pdf.Reader(files) as reader:
            if len(reader) == 0:
                raise UserError("Input files do not have any page.")
            reader.set_final_blank_pages(
                self.blank_page_number(len(reader)), len(reader) - self.last
            )
            yield reader

    @contextlib.contextmanager
    def write(self, output):
        with pdf.Writer(output) as writer:
            yield writer

    def stack_matrixes(self, sheet, repeat: int):
        # We assume that every page is the same size
        assert len(set(page.signature for page in sheet)) == 1

        size = len(sheet) * sheet[0].signature[0] * sheet[0].signature[1]
        for i in range(repeat):
            for page in sheet:
                yield page.stack(i * size)

    def topleft(self, matrix, x, y, width, height):
        # TODO Center page
        left = self.omargin
        for xx in range(x):
            left += matrix[xx, y].left + matrix[xx, y].right
            if matrix[xx, y].rotate in (90, 270):
                left += height
            else:
                left += width
        left += matrix[x, y].left

        top = self.omargin
        for yy in range(y):
            top += matrix[x, yy].top + matrix[x, yy].bottom
            if matrix[x, yy].rotate in (90, 270):
                top += width
            else:
                top += height
        top += matrix[x, y].top

        return (left, top)

    def pagesize(self, matrix, sourcesize):
        # TODO Center page
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
        with self.read(files) as reader, self.write(output) as writer:
            for matrix in self.matrixes(len(reader)):
                destpage = writer.new_page(*self.pagesize(matrix, reader.size))
                for x, y in matrix.coordinates():
                    if reader[matrix[x, y].number] is None:
                        # Blank page
                        continue

                    sourcepage = reader[matrix[x, y].number]
                    writer.insert(
                        destpage,
                        sourcepage,
                        topleft=self.topleft(matrix, x, y, *reader.size),
                        rotate=matrix[x, y].rotate,
                    )
