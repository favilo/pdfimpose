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

"""Cut as flash cards (question on front, answer on back)."""

import dataclasses
import decimal
import itertools
import numbers

from .. import common
from ..common import Page, Matrix


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

    def base_matrix(self):
        """Yield a single matrix.

        This matrix contains the arrangement of source pages on the output pages.
        """
        recto, verso = (
            [[None for _ in range(self.signature[1])] for _ in range(self.signature[0])]
            for _ in range(2)
        )
        for i, coord in enumerate(itertools.product(*map(range, self.signature))):
            x, y = coord
            recto[x][y] = Page(
                2 * i,
                left=0 if x == 0 else self.imargin / 2,
                right=0 if x == self.signature[0] - 1 else self.imargin / 2,
                top=0 if y == 0 else self.imargin / 2,
                bottom=0 if y == self.signature[1] - 1 else self.imargin / 2,
            )
            verso[self.signature[0] - x - 1][y] = Page(
                2 * i + 1,
                left=0 if x == self.signature[0] - 1 else self.imargin / 2,
                right=0 if x == 0 else self.imargin / 2,
                top=0 if y == 0 else self.imargin / 2,
                bottom=0 if y == self.signature[1] - 1 else self.imargin / 2,
            )
        yield Matrix(recto)
        yield Matrix(verso)

    def matrixes(self, pages: int):
        step = 2 * self.signature[0] * self.signature[1]

        assert pages % step == 0

        yield from self.stack_matrixes(
            list(self.base_matrix()),
            repeat=pages // step,
            step=step,
        )

    def crop_marks(self, number, matrix, outputsize, inputsize):
        left, right, top, bottom = self._crop_space()

        for x in range(self.signature[0]):
            yield (
                (self.omarginleft + x * (inputsize[0] + self.imargin), 0),
                (
                    self.omarginleft + x * (inputsize[0] + self.imargin),
                    self.omargintop - top,
                ),
            )
            yield (
                (self.omarginleft + (x + 1) * inputsize[0] + x * self.imargin, 0),
                (
                    self.omarginleft + (x + 1) * inputsize[0] + x * self.imargin,
                    self.omargintop - top,
                ),
            )
            yield (
                (self.omarginleft + x * (inputsize[0] + self.imargin), outputsize[1]),
                (
                    self.omarginleft + x * (inputsize[0] + self.imargin),
                    outputsize[1] - self.omarginbottom + bottom,
                ),
            )
            yield (
                (
                    self.omarginleft + (x + 1) * inputsize[0] + x * self.imargin,
                    outputsize[1],
                ),
                (
                    self.omarginleft + (x + 1) * inputsize[0] + x * self.imargin,
                    outputsize[1] - self.omarginbottom + bottom,
                ),
            )

        for y in range(self.signature[1]):
            yield (
                (0, self.omargintop + y * (inputsize[1] + self.imargin)),
                (
                    self.omarginleft - left,
                    self.omargintop + y * (inputsize[1] + self.imargin),
                ),
            )
            yield ((0, self.omargintop + (y + 1) * inputsize[1] + y * self.imargin)), (
                self.omarginleft - left,
                self.omargintop + (y + 1) * inputsize[1] + y * self.imargin,
            )
            yield (
                (outputsize[0], self.omargintop + y * (inputsize[1] + self.imargin)),
                (
                    outputsize[0] - self.omarginright + right,
                    self.omargintop + y * (inputsize[1] + self.imargin),
                ),
            )
            yield (
                (
                    outputsize[0],
                    self.omargintop + (y + 1) * inputsize[1] + y * self.imargin,
                )
            ), (
                outputsize[0] - self.omarginright + right,
                self.omargintop + (y + 1) * inputsize[1] + y * self.imargin,
            )


def impose(files, output, *, imargin=0, omargin=0, mark=None, signature=None):
    """Perform imposition of source files into an output file, to be cut as flash cards.

    :param list[str] files: List of source files (as strings or :class:`io.BytesIO` streams).
        If empty, reads from standard input.
    :param str output: List of output file.
    :param float omargin: Output margin, in pt
        (or a tuple of four margins: ``(top, right, bottom, left)``).
    :param float imargin: Input margin, in pt.
    :param list[str] mark: List of marks to add.
        Only crop marks are supported (`mark=['crop']`); everything else is silently ignored.
    :param tuple[int] signature: Layout of source pages on output pages.
    """
    if mark is None:
        mark = []
    if isinstance(omargin, numbers.Real):
        omargin = (omargin, omargin, omargin, omargin)

    CardsImpositor(
        omargintop=omargin[0],
        omarginright=omargin[1],
        omarginbottom=omargin[2],
        omarginleft=omargin[3],
        imargin=imargin,
        mark=mark,
        signature=signature,
    ).impose(files, output)
