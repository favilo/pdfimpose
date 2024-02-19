# Copyright 2011-2024 Louis Paternault
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
import itertools
import math
import numbers
import typing

import papersize

from ... import pdf
from .. import Margins, Matrix, Page, hardcover, nocreep
from ..hardcover import _any2folds, _folds2margins


@dataclasses.dataclass
class SaddleImpositor(hardcover.HardcoverImpositor):
    """Perform imposition of source files, with the 'saddle' schema."""

    creep: typing.Callable[[int], float] = dataclasses.field(default=nocreep)

    def _margins(self, x, y):
        """Compute and return margin for page at coordinate (x, y)."""
        margins = Margins(
            top=self.omargin.top if y == 0 else self.imargin / 2,
            bottom=(
                self.omargin.bottom if y == self.signature[1] - 1 else self.imargin / 2
            ),
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
        pages_per_group = self.fix_group(pages) * self.signature[0] * self.signature[1]
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
    folds=None,
    signature=None,
    size=None,
    imargin=0,
    omargin=0,
    mark=None,
    last=0,
    bind="left",
    creep=nocreep,
    group=1,
):  # pylint: disable=too-many-arguments
    """Perform imposition of source files into an output file, to be bound using "saddle stitch".

    :param list[str] files: List of source files (as strings or :class:`io.BytesIO` streams).
        If empty, reads from standard input.
    :param str output: List of output file.
    :param float omargin: Output margin, in pt. Can also be a :class:`Margins` object.
    :param float imargin: Input margin, in pt.
    :param list[str] mark: List of marks to add.
        Only crop marks are supported (`mark=['crop']`); everything else is silently ignored.
    :param str folds: Sequence of folds, as a string of characters `h` and `v`.
    :param str size: Size of the destination pages, as a string that is to be parsed by :func:`papersize.parse_papersize`.
        This option is incompatible with `signature` and `folds`.
    :param tuple[int] signature: Layout of source pages on output pages.
        For instance ``(2, 3)`` means: the printed sheets are to be cut in a matrix of
        2 horizontal sheets per 3 vertical sheets.
        This option is incompatible with `size` and `folds`.
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

    if (signature, size, folds).count(None) <= 1:
        raise ValueError(
            "Only one of `size`, `folds` and `signature` arguments can be other than `None`."
        )
    if folds is None:
        files = pdf.Reader(files)
        if bind in ("top", "bottom"):
            sourcesize = (files.size[1], files.size[0])
        else:
            sourcesize = (files.size[0], files.size[1])

        # Compute folds (from signature and format), and remove signature and format
        if isinstance(size, str):
            size = tuple(float(dim) for dim in papersize.parse_papersize(size))
        folds, size = _any2folds(signature, size, inputsize=sourcesize)
        if (
            size is not None
            and imargin == 0
            and creep == nocreep  # pylint: disable=comparison-with-callable
        ):
            omargin = _folds2margins(size, sourcesize, folds, imargin)

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
