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

"""Print pages, to be cut, stacked, folded, and eventually bound.

You want to print and bind one single tiny A7 book.
This book is made with A6 sheets
(when you open the book, you get two A7 pages side-by-side, which is A6).
Since you can fit four A6 pages on an A4 page,
this means that you can print four A6 sheets on one A4 sheet.

To use this schema:

- print your imposed file, two-sided;
- cut the stack of paper, to get several stacks (four in the example above);
- stack the several stacks you got on top of each other
  (take care to keep the pages in the right order);
- fold and bind the stack of paper you got;
- voilà! You now have a shiny, tiny book.

Example:
    :download:`source <examples/cutstackfold.pdf>`,
    :download:`destination <examples/cutstackfold-impose.pdf>`.

:class:`CutStackFoldImpositor`
------------------------------

.. autoclass:: CutStackFoldImpositor

:func:`impose`
--------------

.. autofunction:: impose
"""

import dataclasses
import decimal
import itertools
import numbers
import typing

from .. import common
from ..common import Matrix, Page


@dataclasses.dataclass
class CutStackFoldImpositor(common.AbstractImpositor):
    """Perform imposition of source files, with the 'cutstackfold' schema."""

    bind: str = "left"
    creep: typing.Callable[[int], float] = dataclasses.field(default=common.nocreep)
    imargin: float = 0
    signature: tuple[int] = (0, 0)

    def blank_page_number(self, source):
        pagesperpage = 4 * self.signature[0] * self.signature[1]
        if source % pagesperpage == 0:
            return 0
        return pagesperpage - (source % pagesperpage)

    def margins(self, x, y):
        """Compute and return margin for page at coordinate (x, y)."""
        margins = {
            "top": self.omargin.top if y == 0 else self.imargin / 2,
            "bottom": self.omargin.bottom
            if y == self.signature[1] - 1
            else self.imargin / 2,
            "left": 0 if x % 2 == 1 else self.imargin / 2,
            "right": 0 if x % 2 == 0 else self.imargin / 2,
        }

        # Output margins
        if x == 0:
            margins["left"] = self.omargin.left
        if x == 2 * self.signature[0] - 1:
            margins["right"] = self.omargin.right

        return margins

    def base_matrix(self, total):
        """Yield a single matrix.

        This matrix contains the arrangement of source pages on the output pages.

        :param int total: Total number of source pages.
        """
        stack = total // (2 * self.signature[0] * self.signature[1])

        for inner in range(stack // 2):
            recto, verso = (
                [
                    [None for _ in range(self.signature[1])]
                    for _ in range(2 * self.signature[0])
                ]
                for _ in range(2)
            )

            for i, coord in enumerate(itertools.product(*map(range, self.signature))):
                x, y = coord
                recto[2 * x][y] = Page(
                    total - i * stack - 2 * inner - 1, **self.margins(2 * x, y)
                )
                recto[2 * x + 1][y] = Page(
                    i * stack + 2 * inner, **self.margins(2 * x + 1, y)
                )
                verso[2 * self.signature[0] - 2 * x - 1][y] = Page(
                    total - i * stack - 2 * inner - 2,
                    **self.margins(2 * self.signature[0] - 2 * x - 1, y),
                )
                verso[2 * self.signature[0] - 2 * x - 2][y] = Page(
                    i * stack + 2 * inner + 1,
                    **self.margins(2 * self.signature[0] - 2 * x - 2, y),
                )

            yield Matrix(recto, rotate=common.BIND2ANGLE[self.bind])
            yield Matrix(verso, rotate=common.BIND2ANGLE[self.bind])

    def _max_creep(self, total):
        """Return the maximum creep of the document.

        :param int total: Total number of source pages.
        """
        return max(self.creep(n) for n in range(total // 4))

    def matrixes(self, pages: int):
        assert pages % (4 * self.signature[0] * self.signature[1]) == 0

        # Compute maximum creep
        maxcreep = self._max_creep(pages)

        for number, matrix in enumerate(self.base_matrix(pages)):
            for x, y in matrix.coordinates():
                # Number of output sheets
                sheets = pages // (4 * self.signature[0] * self.signature[1])
                # Number of (output) sheets stacked on top in the current (output) sheet
                included = sheets - number // 2 - 1
                # Number of stacks included in the current page, once cut
                stacks = self.signature[1] * (1 - x // 2) + self.signature[0] - y
                creep = self.creep(included + stacks * sheets)

                if number % 2 == 1:
                    # Pages are reversed on the back of sheets (odd pages)
                    x = matrix.width - x - 1

                if x % 2 == 0:
                    matrix[x, y].left += (maxcreep - creep) / 2
                    matrix[x, y].right += creep / 2
                else:
                    matrix[x, y].left += creep / 2
                    matrix[x, y].right += (maxcreep - creep) / 2
            yield matrix

    def crop_marks(self, number, total, matrix, outputsize, inputsize):
        # pylint: disable=too-many-arguments
        left, right, top, bottom = self._crop_space()
        maxcreep = self._max_creep(total)

        for x in range(self.signature[0]):
            yield (
                (
                    self.omargin.left
                    + 2 * x * inputsize[0]
                    + x * (self.imargin + maxcreep),
                    0,
                ),
                (
                    self.omargin.left
                    + 2 * x * inputsize[0]
                    + x * (self.imargin + maxcreep),
                    self.omargin.top - top,
                ),
            )
            yield (
                (
                    self.omargin.left
                    + 2 * x * inputsize[0]
                    + x * (self.imargin + maxcreep),
                    outputsize[1],
                ),
                (
                    self.omargin.left
                    + 2 * x * inputsize[0]
                    + x * (self.imargin + maxcreep),
                    outputsize[1] - self.omargin.bottom + bottom,
                ),
            )
            yield (
                (
                    self.omargin.left
                    + 2 * (x + 1) * inputsize[0]
                    + x * self.imargin
                    + (x + 1) * maxcreep,
                    0,
                ),
                (
                    self.omargin.left
                    + 2 * (x + 1) * inputsize[0]
                    + x * self.imargin
                    + (x + 1) * maxcreep,
                    self.omargin.top - top,
                ),
            )
            yield (
                (
                    self.omargin.left
                    + 2 * (x + 1) * inputsize[0]
                    + x * self.imargin
                    + (x + 1) * maxcreep,
                    outputsize[1],
                ),
                (
                    self.omargin.left
                    + 2 * (x + 1) * inputsize[0]
                    + x * self.imargin
                    + (x + 1) * maxcreep,
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
    imargin=0,
    omargin=0,
    last=0,
    mark=None,
    signature=None,
    bind="left",
    creep=common.nocreep,
):
    """Perform imposition of source files into an output file, using the cut-stack-bind schema.

    :param list[str] files: List of source files (as strings or :class:`io.BytesIO` streams).
        If empty, reads from standard input.
    :param str output: List of output file.
    :param float omargin: Output margin, in pt. Can also be a :class:`Margins` object.
    :param float imargin: Input margin, in pt.
    :param int last: Number of last pages (of the source files) to keep at the
        end of the output document.  If blank pages were to be added to the
        source files, they would be added before those last pages.
    :param list[str] mark: List of marks to add.
        Only crop marks are supported (`mark=['crop']`); everything else is silently ignored.
    :param tuple[int] signature: Layout of source pages on output pages.
    :param str bind: Binding edge. Can be one of `left`, `right`, `top`, `bottom`.
    :param function creep: Function that takes the number of sheets in argument,
        and return the space to be left between two adjacent pages.
    """
    if mark is None:
        mark = []

    CutStackFoldImpositor(
        imargin=imargin,
        omargin=omargin,
        mark=mark,
        last=last,
        signature=signature,
        bind=bind,
        creep=creep,
    ).impose(files, output)
