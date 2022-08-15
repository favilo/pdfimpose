# Copyright 2011-2022 Louis Paternault
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

"""Perfect binding (done in books, like dictionaries)

Perfect binding is the schema used to print *real* books (novels, dictionnaries, etc.):
several destination pages are printed on a single, big, sheet of paper,
which is folded, and cut.
Those booklets are stacked onto each other, and bound together, to make your book.

To use this schema (without option --group, or with --group=1):

- print your imposed PDF file, two-sided;
- separately fold each sheet of paper;
- stack them;
- bind them.

With option --group=3 (for instance), repeat the step above for every group of three sheets. You get several signatures, that you have to bind together to get a proper book.
"""  # pylint: disable=line-too-long

import dataclasses
import decimal
import itertools
import math
import numbers
import typing

from .. import BIND2ANGLE, AbstractImpositor, Margins, Matrix, Page


def evenodd2oddeven(number):
    """Convert an even or odd number to the other number with the quotient by 2.

    For instance, 12 // 2 == 6 and 13 // 2 == 6, so:
    >> evenodd2oddeven(12)
    13
    >> evenodd2oddeven(13)
    12
    """
    if number % 2 == 0:
        return number + 1
    return number - 1


@dataclasses.dataclass
class PerfectImpositor(AbstractImpositor):
    """Perform imposition of source files, with the 'perfect' schema."""

    folds: str = None
    imargin: float = 0
    bind: str = "left"
    group: int = 1

    def __post_init__(self):
        super().__post_init__()
        if self.folds is None:
            raise TypeError("Argument 'folds' must be given a value.")
        self.signature = (
            2 ** self.folds.count("h"),
            2 ** self.folds.count("v"),
        )

    def blank_page_number(self, source):
        pagesperpage = 2 * self.signature[0] * self.signature[1]
        if source % pagesperpage == 0:
            return 0
        return pagesperpage - (source % pagesperpage)

    def _margins(self, x, y):
        """Compute and return margin for page at coordinate (x, y)."""
        margins = Margins(
            top=self.omargin.top if y == 0 else self.imargin / 2,
            bottom=self.omargin.bottom
            if y == self.signature[1] - 1
            else self.imargin / 2,
            left=0 if x % 2 == 1 else self.imargin / 2,
            right=0 if x % 2 == 0 else self.imargin / 2,
        )

        # Output margins
        if x == 0:
            margins.left = self.omargin.left
        if x == self.signature[0] - 1:
            margins.right = self.omargin.right

        return margins

    def base_matrix(self, total):
        """Yield two matrixes (recto and verso) corresponding to one folded sheet."""
        # pylint: disable=unused-argument

        def _rotate(y):
            if self.signature[1] == 1:
                return [0, 180][y % 2]
            return [180, 0][y % 2]

        recto = [[0]]
        total = 2
        for fold in self.folds:
            total *= 2
            if fold == "h":
                recto = (
                    recto[: len(recto) // 2]
                    + [[None] * len(column) for column in recto]
                    + recto[len(recto) // 2 :]
                )
                # pylint: disable=consider-using-enumerate
                for x in range(len(recto)):
                    for y in range(len(recto[x])):
                        if recto[x][y] is None:
                            recto[x][y] = total - recto[evenodd2oddeven(x)][y] - 1
            if fold == "v":
                recto = [
                    column[: len(column) // 2]
                    + [None] * len(column)
                    + column[len(column) // 2 :]
                    for column in recto
                ]
                # pylint: disable=consider-using-enumerate
                for x in range(len(recto)):
                    for y in range(len(recto[x])):
                        if recto[x][y] is None:
                            recto[x][y] = total - recto[x][evenodd2oddeven(y)] - 1
        yield Matrix(
            [
                [
                    Page(
                        recto[x][y],
                        rotate=_rotate(y),
                        **vars(self._margins(x, y)),
                    )
                    for y in range(len(recto[x]))
                ]
                for x in range(len(recto))
            ],
            rotate=BIND2ANGLE[self.bind],
        )
        yield Matrix(
            [
                [
                    Page(
                        evenodd2oddeven(recto[len(recto) - x - 1][y]),
                        rotate=_rotate(y),
                        **vars(self._margins(x, y)),
                    )
                    for y in range(len(recto[x]))
                ]
                for x in range(len(recto))
            ],
            rotate=BIND2ANGLE[self.bind],
        )

    def group_matrixes(self, total):
        """Yield matrixes corresponding to a group of sheets.

        1. First, we compute the matrix corresponding to a single folded sheet
           (see :meth:`PerfectImpositor.base_matrix`).

        2. Then, we compute the matrix corresponding to the outer sheet of the group.
           Note that:

           - The way the sheet is folded is irrelevant here:
             everything can be computed using only page numbers, regardless of their position.
           - One side of the sheet, when folded, faces the same sheet, or the outer world;
             the other side, when folded, faces other sheets of the same group.

           Here is an example.
           Let's consider a (output) sheet with 8 (input) pages per (output page):
           this sheet has 16 input pages on it, from 0 to 15.
           When folded, the original page numbers become (with different ``self.group`` values):

           Original sheets: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
           self.group == 1: 0  1  6  7  8  9 14 15 16 17 22 23 24 25 30 31
           self.group == 2: 0  1 10 11 12 13 22 23 24 25 34 35 36 37 46 47
           self.group == 3: 0  1 14 15 16 17 30 31 32 33 46 47 48 49 62 63

           To compute this yourself, take 1, 2, 3 (or more) sheets of paper,
           place (output) page numbers on the outer one, fold them,
           and watch the new page numbers you get.

           Note that the numbers are consecutives, exepted for gaps every 4 numbers,
           starting between 1 and 2. Each of these gaps is 4×(self.group-1).
           Thus, the formula used to compute `outer` (see code below).

        3. At last, we compute the matrix of the inner sheets.
           Those being adjacent to the inner sheets,
           we simply add or substract page numbers to them.
        """
        if self.group == 0:
            group = math.ceil(total / (2 * self.signature[0] * self.signature[1]))
        else:
            group = self.group

        for g in range(group):  #  pylint: disable=invalid-name
            for matrix in self.base_matrix(total):
                grouped = [
                    [None for y in range(matrix.height)] for x in range(matrix.width)
                ]
                for x, y in matrix.coordinates():
                    # `outer` is the matrix of the outer sheet. Matrixes of the inner sheets will be computed by adding or substracting pages from `outer`.
                    outer = matrix[x, y].number + math.floor(
                        (matrix[x, y].number + 2) / 4
                    ) * 4 * (group - 1)
                    if g == 0:
                        grouped[x][y] = dataclasses.replace(matrix[x, y], number=outer)
                    elif matrix[x, y].number % 4 <= 1:
                        grouped[x][y] = dataclasses.replace(
                            matrix[x, y], number=outer + 2 * g
                        )
                    else:
                        grouped[x][y] = dataclasses.replace(
                            matrix[x, y], number=outer - 2 * g
                        )
                yield Matrix(grouped)

    def matrixes(self, pages: int):
        if self.group == 0:
            group = math.ceil(pages / (2 * self.signature[0] * self.signature[1]))
        else:
            group = self.group

        pages_per_group = 2 * self.signature[0] * self.signature[1] * group
        assert pages % pages_per_group == 0

        yield from self.stack_matrixes(
            list(self.group_matrixes(pages)),
            repeat=pages // pages_per_group,
            step=pages_per_group,
        )

    def bind_marks(self, number, total, matrix, outputsize, inputsize):
        # pylint: disable=too-many-arguments
        if number % 2 == 1:
            return

        if self.bind in ["top", "bottom"]:
            inputsize = (inputsize[1], inputsize[0])

        height = min(
            28, inputsize[1] / (total // (2 * matrix.width * matrix.height) + 2)
        )

        yield (
            (
                outputsize[0] - self.omargin.right - inputsize[0] - 1,
                outputsize[1] - self.omargin.bottom - height * (number // 2 + 2),
            ),
            (
                outputsize[0] - self.omargin.right - inputsize[0] + 1,
                outputsize[1] - self.omargin.bottom - height * (number // 2 + 1),
            ),
        )

    def crop_marks(self, number, total, matrix, outputsize, inputsize):
        # pylint: disable=too-many-arguments
        left, right, top, bottom = self._crop_space()
        if self.bind in ["top", "bottom"]:
            inputsize = (inputsize[1], inputsize[0])

        for x in range(self.signature[0] // 2):
            yield (
                (self.omargin.left + x * (2 * inputsize[0] + self.imargin), 0),
                (
                    self.omargin.left + x * (2 * inputsize[0] + self.imargin),
                    self.omargin.top - top,
                ),
            )
            yield (
                (
                    self.omargin.left + x * (2 * inputsize[0] + self.imargin),
                    outputsize[1],
                ),
                (
                    self.omargin.left + x * (2 * inputsize[0] + self.imargin),
                    outputsize[1] - self.omargin.bottom + bottom,
                ),
            )
            yield (
                (self.omargin.left + (x + 1) * 2 * inputsize[0] + x * self.imargin, 0),
                (
                    self.omargin.left + (x + 1) * 2 * inputsize[0] + x * self.imargin,
                    self.omargin.top - top,
                ),
            )
            yield (
                (
                    self.omargin.left + (x + 1) * 2 * inputsize[0] + x * self.imargin,
                    outputsize[1],
                ),
                (
                    self.omargin.left + (x + 1) * 2 * inputsize[0] + x * self.imargin,
                    outputsize[1] - self.omargin.bottom + bottom,
                ),
            )

        for y in range(self.signature[1]):
            yield (
                (0, self.omargin.top + y * (inputsize[1] + self.imargin)),
                (
                    self.omargin.left - left,
                    self.omargin.top + y * (inputsize[1] + self.imargin),
                ),
            )
            yield ((0, self.omargin.top + (y + 1) * inputsize[1] + y * self.imargin)), (
                self.omargin.left - left,
                self.omargin.top + (y + 1) * inputsize[1] + y * self.imargin,
            )
            yield (
                (outputsize[0], self.omargin.top + y * (inputsize[1] + self.imargin)),
                (
                    outputsize[0] - self.omargin.right + right,
                    self.omargin.top + y * (inputsize[1] + self.imargin),
                ),
            )
            yield (
                (
                    outputsize[0],
                    self.omargin.top + (y + 1) * inputsize[1] + y * self.imargin,
                )
            ), (
                outputsize[0] - self.omargin.right + right,
                self.omargin.top + (y + 1) * inputsize[1] + y * self.imargin,
            )


def impose(
    files,
    output,
    *,
    folds,
    imargin=0,
    omargin=0,
    mark=None,
    last=0,
    bind="left",
    group=1,
):
    """Perform imposition of source files into an output file, to be bound using "perfect binding".

    :param list[str] files: List of source files (as strings or :class:`io.BytesIO` streams).
        If empty, reads from standard input.
    :param str output: List of output file.
    :param float omargin: Output margin, in pt. Can also be a :class:`Margins` object.
    :param float imargin: Input margin, in pt.
    :param list[str] mark: List of marks to add.
        Only crop marks are supported (`mark=['crop']`); everything else is silently ignored.
    :param str folds: Sequence of folds, as a string of characters `h` and `v`.
    :param str bind: Binding edge. Can be one of `left`, `right`, `top`, `bottom`.
    :param int last: Number of last pages (of the source files) to keep at the
        end of the output document.  If blank pages were to be added to the
        source files, they would be added before those last pages.
    :param int group: Group sheets before folding them.
        See help of command line --group option for more information.
    """
    if mark is None:
        mark = []

    PerfectImpositor(
        omargin=omargin,
        imargin=imargin,
        mark=mark,
        last=last,
        bind=bind,
        folds=folds,
        group=group,
    ).impose(files, output)
