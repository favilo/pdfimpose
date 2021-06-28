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

"""Cut as invidual pages, stack and wire bind."""

import dataclasses
import decimal
import itertools
import numbers

from .. import cards, common
from ..common import Page, Matrix


@dataclasses.dataclass
class WireImpositor(cards.CardsImpositor):
    """Perform imposition of source files, with the 'wire' schema."""

    def wire_base_matrix(self, repeat):
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
                2 * i * repeat,
                top=0 if y == 0 else self.imargin / 2,
                bottom=0 if y == self.signature[1] - 1 else self.imargin / 2,
                left=0 if x == 0 else self.imargin / 2,
                right=0 if x == self.signature[0] - 1 else self.imargin / 2,
            )
            verso[self.signature[0] - x - 1][y] = Page(
                2 * i * repeat + 1,
                top=0 if y == 0 else self.imargin / 2,
                bottom=0 if y == self.signature[1] - 1 else self.imargin / 2,
                left=0 if x == self.signature[0] - 1 else self.imargin / 2,
                right=0 if x == 0 else self.imargin / 2,
            )
        yield Matrix(recto)
        yield Matrix(verso)

    def matrixes(self, pages: int):
        assert pages % (2 * self.signature[0] * self.signature[1]) == 0

        repeat = pages // (2 * self.signature[0] * self.signature[1])
        yield from self.stack_matrixes(
            list(self.wire_base_matrix(repeat)),
            repeat=repeat,
            step=2,
        )


def impose(files, output, *, imargin=0, omargin=0, last=0, mark=None, signature=None):
    """Perform imposition of source files into an output file, to be cut and "wire bound".

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
    """
    if mark is None:
        mark = []

    WireImpositor(
        imargin=imargin,
        omargin=omargin,
        last=last,
        mark=mark,
        signature=signature,
    ).impose(files, output)
