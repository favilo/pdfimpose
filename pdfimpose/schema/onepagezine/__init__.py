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

    imargin: float = 0
    bind: str = "left"
    mark: list[str] = dataclasses.field(default_factory=list)

    def blank_page_number(self, source):
        if source % 8 == 0:
            return 0
        return 8 - (source % 8)

    def base_matrix(self):
        yield Matrix(
            [
                [
                    Page(4, bottom=self.imargin / 2, rotate=180),
                    Page(5, top=self.imargin / 2),
                ],
                [
                    Page(
                        3, right=self.imargin / 2, bottom=self.imargin / 2, rotate=180
                    ),
                    Page(6, right=self.imargin / 2, top=self.imargin / 2),
                ],
                [
                    Page(2, left=self.imargin / 2, bottom=self.imargin / 2, rotate=180),
                    Page(7, left=self.imargin / 2, top=self.imargin / 2),
                ],
                [
                    Page(1, bottom=self.imargin / 2, rotate=180),
                    Page(0, top=self.imargin / 2),
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


def impose(files, output, *, imargin=0, omargin=0, last=0, mark=None, bind="left"):
    if mark is None:
        mark = []
    OnePageZineImpositor(
        imargin=imargin,
        omargin=omargin,
        last=last,
        mark=mark,
        bind=bind,
    ).impose(files, output)
