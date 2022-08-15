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

"""Saddle stitch (like in newpapers or magazines)

This schema is used in newspapers or magazines: the sheets are inserted into each other.

To use this schema (with --group=1, or without --group):

- print your imposed PDF file, two-sided;
- if there is two source pages on each destination page:
    - fold all your sheets at once;
    - otherwise, separately fold each sheet of paper, and insert them into each other;
- bind.

With option --group=3 (for instance), repeat the step above for every group of three sheets. You get several signatures, that you have to bind together to get a proper book.
"""  # pylint: disable=line-too-long

import dataclasses
import decimal
import itertools
import math
import numbers
import typing

from .. import Margins, Matrix, Page, nocreep, perfect


@dataclasses.dataclass
class SaddleImpositor(perfect.PerfectImpositor):
    """Perform imposition of source files, with the 'saddle' schema."""

    creep: typing.Callable[[int], float] = dataclasses.field(default=nocreep)

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

    def matrixes(self, pages: int):
        if self.group == 0:
            group = math.ceil(pages / (2 * self.signature[0] * self.signature[1]))
        else:
            group = self.group

        pages_per_group = group * self.signature[0] * self.signature[1]
        assert pages % pages_per_group == 0

        matrixes = list(self.group_matrixes(pages))
        for i in range(pages // (2 * pages_per_group)):
            yield from self.insert_sheets(
                (matrix.copy() for matrix in matrixes), i, pages, pages_per_group
            )

    def bind_marks(self, number, total, matrix, outputsize, inputsize):
        # pylint: disable=too-many-arguments
        yield from []


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
    creep=nocreep,
    group=1,
):
    """Perform imposition of source files into an output file, to be bound using "saddle stitch".

    :param list[str] files: List of source files (as strings or :class:`io.BytesIO` streams).
        If empty, reads from standard input.
    :param str output: List of output file.
    :param float omargin: Output margin, in pt. Can also be a :class:`Margins` object.
    :param float imargin: Input margin, in pt.
    :param list[str] mark: List of marks to add.
        Only crop marks are supported (`mark=['crop']`); everything else is silently ignored.
    :param str folds: Sequence of folds, as a string of characters `h` and `v`.
    :param str bind: Binding edge. Can be one of `left`, `right`, `top`, `bottom`.
    :param function creep: Function that takes the number of sheets in argument,
        and return the space to be left between two adjacent pages.
    :param int last: Number of last pages (of the source files) to keep at the
        end of the output document.  If blank pages were to be added to the
        source files, they would be added before those last pages.
    :param int group: Group sheets before folding them.
        See help of command line --group option for more information.
    """
    if mark is None:
        mark = []

    SaddleImpositor(
        omargin=omargin,
        imargin=imargin,
        mark=mark,
        last=last,
        bind=bind,
        folds=folds,
        creep=creep,
        group=group,
    ).impose(files, output)
