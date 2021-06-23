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

"""A one-page fanzine, with a poster on the back."""

import collections.abc
import dataclasses
import decimal

from .. import common
from ..common import Page, Matrix


@dataclasses.dataclass
class OnePageZineImpositor(common.AbstractImpositor):

    bind: str = "left"

    def blank_page_number(self, source):
        if source % 8 == 0:
            return 0
        return 8 - (source % 8)

    def base_matrix(self):
        yield Matrix(
            [
                [
                    Page(4, rotate=180),
                    Page(5),
                ],
                [
                    Page(3, rotate=180),
                    Page(6),
                ],
                [
                    Page(2, rotate=180),
                    Page(7),
                ],
                [
                    Page(1, rotate=180),
                    Page(0),
                ],
            ],
            rotate=common.BIND2ANGLE[self.bind],
        )

    def matrixes(self, pages: int):
        assert pages % 8 == 0
        yield from self.stack_matrixes(
            list(self.base_matrix()),
            pages // 8,
        )

    def crop_marks(self, number, matrix, outputsize, inputsize):
        if self.omargin == 0:
            return

        SPACE = 20
        if SPACE > self.omargin:
            SPACE = self.omargin / 2

        yield ((0, self.omargin), (self.omargin - SPACE, self.omargin))
        yield ((self.omargin, 0), (self.omargin, self.omargin - SPACE))
        yield (
            (outputsize[0], self.omargin),
            (outputsize[0] - self.omargin + SPACE, self.omargin),
        )
        yield (
            (outputsize[0] - self.omargin, 0),
            (outputsize[0] - self.omargin, self.omargin - SPACE),
        )
        yield (
            (0, outputsize[1] - self.omargin),
            (self.omargin - SPACE, outputsize[1] - self.omargin),
        )
        yield (
            (self.omargin, outputsize[1]),
            (self.omargin, outputsize[1] - self.omargin + SPACE),
        )
        yield (
            (outputsize[0], outputsize[1] - self.omargin),
            (outputsize[0] - self.omargin + SPACE, outputsize[1] - self.omargin),
        )
        yield (
            (outputsize[0] - self.omargin, outputsize[1]),
            (outputsize[0] - self.omargin, outputsize[1] - self.omargin + SPACE),
        )


def impose(files, output, *, omargin=0, last=0, mark=None, bind="left"):
    if mark is None:
        mark = []
    OnePageZineImpositor(
        omargin=omargin,
        last=last,
        mark=mark,
        bind=bind,
    ).impose(files, output)
