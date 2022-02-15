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

"""Cut as flash cards (question on front, answer on back).

This schema can be used when you want to print flash cards:

- your source PDF is a list of (let's say) A6 pages:
  Question 1, Answer 1, Question 2, Answer 2, Question 3, Answer 3…
- you want to print those questions and answer on an A4 sheet of paper,
  and cut it to get your flash cards (questions on front, answers on back).

:class:`CardsImpositor`
-----------------------

.. autoclass:: CardsImpositor

:func:`impose`
--------------

.. autofunction:: impose
"""


import dataclasses
import decimal
import itertools
import numbers

from .. import common
from ..common import Matrix, Page


@dataclasses.dataclass
class CardsImpositor(common.AbstractImpositor):
    """Perform imposition of source files, with the 'card' schema."""

    imargin: float = 0
    signature: tuple[int] = (0, 0)

    def blank_page_number(self, source):
        pagesperpage = 2 * self.signature[0] * self.signature[1]
        if source % pagesperpage == 0:
            return 0
        return pagesperpage - (source % pagesperpage)

    def base_matrix(self, total):
        """Yield a single matrix.

        This matrix contains the arrangement of source pages on the output pages.
        """
        # pylint: disable=unused-argument
        recto, verso = (
            [[None for _ in range(self.signature[1])] for _ in range(self.signature[0])]
            for _ in range(2)
        )
        for i, coord in enumerate(itertools.product(*map(range, self.signature))):
            x, y = coord
            recto[x][y] = Page(
                2 * i,
                left=self.omargin.left if x == 0 else self.imargin / 2,
                right=self.omargin.right
                if x == self.signature[0] - 1
                else self.imargin / 2,
                top=self.omargin.top if y == 0 else self.imargin / 2,
                bottom=self.omargin.bottom
                if y == self.signature[1] - 1
                else self.imargin / 2,
            )
            verso[self.signature[0] - x - 1][y] = Page(
                2 * i + 1,
                left=self.omargin.left
                if x == self.signature[0] - 1
                else self.imargin / 2,
                right=self.omargin.right if x == 0 else self.imargin / 2,
                top=self.omargin.top if y == 0 else self.imargin / 2,
                bottom=self.omargin.bottom
                if y == self.signature[1] - 1
                else self.imargin / 2,
            )
        yield Matrix(recto)
        yield Matrix(verso)

    def matrixes(self, pages: int):
        step = 2 * self.signature[0] * self.signature[1]

        assert pages % step == 0

        yield from self.stack_matrixes(
            list(self.base_matrix(pages)),
            repeat=pages // step,
            step=step,
        )

    def crop_marks(self, number, total, matrix, outputsize, inputsize):
        # pylint: disable=too-many-arguments
        left, right, top, bottom = self._crop_space()

        for x in range(self.signature[0]):
            yield (
                (self.omargin.left + x * (inputsize[0] + self.imargin), 0),
                (
                    self.omargin.left + x * (inputsize[0] + self.imargin),
                    self.omargin.top - top,
                ),
            )
            yield (
                (self.omargin.left + (x + 1) * inputsize[0] + x * self.imargin, 0),
                (
                    self.omargin.left + (x + 1) * inputsize[0] + x * self.imargin,
                    self.omargin.top - top,
                ),
            )
            yield (
                (self.omargin.left + x * (inputsize[0] + self.imargin), outputsize[1]),
                (
                    self.omargin.left + x * (inputsize[0] + self.imargin),
                    outputsize[1] - self.omargin.bottom + bottom,
                ),
            )
            yield (
                (
                    self.omargin.left + (x + 1) * inputsize[0] + x * self.imargin,
                    outputsize[1],
                ),
                (
                    self.omargin.left + (x + 1) * inputsize[0] + x * self.imargin,
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


def impose(files, output, *, imargin=0, omargin=0, mark=None, signature=None):
    """Perform imposition of source files into an output file, to be cut as flash cards.

    :param list[str] files: List of source files (as strings or :class:`io.BytesIO` streams).
        If empty, reads from standard input.
    :param str output: List of output file.
    :param float omargin: Output margin, in pt.
        Can also be a :class:`pdfimpose.schema.common.Margins` object.
    :param float imargin: Input margin, in pt.
    :param list[str] mark: List of marks to add.
        Only crop marks are supported (``mark=['crop']``); everything else is silently ignored.
    :param tuple[int] signature: Layout of source pages on output pages.
    """
    if mark is None:
        mark = []

    CardsImpositor(
        omargin=omargin,
        imargin=imargin,
        mark=mark,
        signature=signature,
    ).impose(files, output)
