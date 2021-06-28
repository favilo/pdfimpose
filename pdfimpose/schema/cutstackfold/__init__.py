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

"""Print pages, to be cut, stacked, folded, and eventually bound."""

import dataclasses
import decimal
import itertools
import numbers
import typing

from .. import common
from ..common import Page, Matrix


@dataclasses.dataclass
class CutStackFoldImpositor(common.AbstractImpositor):
    """Perform imposition of source files, with the 'cutstackfold' schema."""

    bind: str = "left"
    creep: typing.Callable[int, float] = dataclasses.field(default=lambda s: 0)
    imargin: float = 0
    signature: tuple[int] = (0, 0)

    def blank_page_number(self, source):
        pagesperpage = 4 * self.signature[0] * self.signature[1]
        if source % pagesperpage == 0:
            return 0
        return pagesperpage - (source % pagesperpage)

    def cutstackfold_base_matrix(self, total):
        """Yield a single matrix.

        This matrix contains the arrangement of source pages on the output pages.

        :param int total: Total number of source pages.
        """
        stack = total // (self.signature[0] * self.signature[1])

        def imargins(x, y):
            return {
                "top": 0 if y == 0 else self.imargin / 2,
                "bottom": 0 if y == self.signature[1] - 1 else self.imargin / 2,
                "left": 0 if x == 0 or x % 2 == 0 else self.imargin / 2,
                "right": 0
                if x == 2 * self.signature[0] - 1 or x % 2 == 1
                else self.imargin / 2,
            }

        for inner in range(stack // 4):
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
                    (i + 1) * stack - 1 - 2 * inner, **imargins(2 * x + 1, y)
                )
                recto[2 * x + 1][y] = Page(i * stack + 2 * inner, **imargins(2 * x, y))
                verso[2 * self.signature[0] - 2 * x - 1][y] = Page(
                    (i + 1) * stack - 2 * inner - 2,
                    **imargins(2 * self.signature[0] - 2 * x - 2, y),
                )
                verso[2 * self.signature[0] - 2 * x - 2][y] = Page(
                    i * stack + 2 * inner + 1,
                    **imargins(2 * self.signature[0] - 2 * x - 1, y),
                )

            yield Matrix(recto, rotate=common.BIND2ANGLE[self.bind])
            yield Matrix(verso, rotate=common.BIND2ANGLE[self.bind])

    def matrixes(self, pages: int):
        assert pages % (4 * self.signature[0] * self.signature[1]) == 0

        yield from self.cutstackfold_base_matrix(pages)

    def crop_marks(self, number, matrix, outputsize, inputsize):
        left, right, top, bottom = self._crop_space()

        for x in range(self.signature[0]):
            yield (
                (
                    self.omargin.left + 2 * x * inputsize[0] + x * self.imargin,
                    0,
                ),
                (
                    self.omargin.left + 2 * x * inputsize[0] + x * self.imargin,
                    self.omargin.top - top,
                ),
            )
            yield (
                (
                    self.omargin.left + 2 * (x + 1) * inputsize[0] + x * self.imargin,
                    0,
                ),
                (
                    self.omargin.left + 2 * (x + 1) * inputsize[0] + x * self.imargin,
                    self.omargin.top - top,
                ),
            )
            yield (
                (
                    self.omargin.left + 2 * x * inputsize[0] + x * self.imargin,
                    outputsize[1],
                ),
                (
                    self.omargin.left + 2 * x * inputsize[0] + x * self.imargin,
                    outputsize[1] - self.omargin.bottom + bottom,
                ),
            )
            yield (
                (
                    self.omargin.left + 2 * (x + 1) * inputsize[0] + x * self.imargin,
                    outputsize[1],
                ),
                (
                    self.omargin.left + 2 * (x + 1) * inputsize[0] + x * self.imargin,
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
    creep=lambda x: 0,
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
    :param function creep: TODO Document
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
