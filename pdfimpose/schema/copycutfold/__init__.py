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

"""Print pages, to be cut and folded, and eventually bound, to produce multiple books."""

import dataclasses
import decimal
import itertools
import numbers
import typing

from .. import common, cutstackfold
from ..common import Page, Matrix


@dataclasses.dataclass
class CopyCutFoldImpositor(cutstackfold.CutStackFoldImpositor):
    """Perform imposition of source files, with the 'copycutfold' schema."""

    def blank_page_number(self, source):
        if source % 4 == 0:
            return 0
        return 4 - (source % 4)

    def base_matrix(self, total):
        """Yield the first matrix.

        This matrix contains the arrangement of source pages on the output pages.

        :param int total: Total number of source pages.
        """

        recto, verso = (
            [
                [None for _ in range(self.signature[1])]
                for _ in range(2 * self.signature[0])
            ]
            for _ in range(2)
        )

        for x, y in itertools.product(*map(range, self.signature)):
            recto[x][y] = Page(3, **self.margins(x, y))
            recto[x + 1][y] = Page(0, **self.margins(x + 1, y))
            verso[x][y] = Page(1, **self.margins(x, y))
            verso[x + 1][y] = Page(2, **self.margins(x + 1, y))

        yield Matrix(recto, rotate=common.BIND2ANGLE[self.bind])
        yield Matrix(verso, rotate=common.BIND2ANGLE[self.bind])

    def matrixes(self, pages: int):
        assert pages % 4 == 0

        matrixes = list(self.base_matrix(pages))
        for i in range((pages - 1) // 4 + 1):
            yield from self.insert_sheets(
                (matrix.copy() for matrix in matrixes), i, pages, 2
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

    CopyCutFoldImpositor(
        imargin=imargin,
        omargin=omargin,
        mark=mark,
        last=last,
        signature=signature,
        bind=bind,
        creep=creep,
    ).impose(files, output)
