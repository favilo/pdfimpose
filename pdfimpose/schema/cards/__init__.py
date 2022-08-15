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

"""Cut as flash cards (question on front, answer on back).

This schema can be used when you want to print flash cards:

- your source PDF is a list of (let's say) A6 pages:
  Question 1, Answer 1, Question 2, Answer 2, Question 3, Answer 3…
  Note that this behavior can be changed with option --back.
- you want to print those questions and answer on an A4 sheet of paper,
  and cut it to get your flash cards (questions on front, answers on back).
"""


import dataclasses
import decimal
import itertools
import numbers

from ... import pdf
from .. import AbstractImpositor, Matrix, Page


class PdfReader(pdf.Reader):
    """PDF Reader that read source files AND back files."""

    def __init__(self, files, *, back=""):
        if back:
            self.back = pdf.readpdf(back)
        else:
            self.back = None
        super().__init__(files)

    def __getitem__(self, key):
        if self.back and key // 2 < self.source_len:
            if key % 2 == 0:
                return super().__getitem__(key // 2)
            return self.back[(key // 2) % len(self.back)]
        return super().__getitem__(key)

    def __len__(self):
        if self.back:
            return 2 * self.source_len + self._blank_number
        else:
            return super().__len__()

    def __exit__(self, *args, **kwargs):
        if self.back:
            self.back.close()
        super().__exit__(*args, **kwargs)


@dataclasses.dataclass
class CardsImpositor(AbstractImpositor):
    """Perform imposition of source files, with the 'card' schema."""

    imargin: float = 0
    signature: tuple[int] = (0, 0)
    back: str = ""

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

    def open_pdf(self, files):  # pylint: disable=arguments-differ
        return PdfReader(files, back=self.back)


def impose(files, output, *, imargin=0, omargin=0, mark=None, signature=None, back=""):
    """Perform imposition of source files into an output file, to be cut as flash cards.

    :param list[str] files: List of source files (as strings or :class:`io.BytesIO` streams).
        If empty, reads from standard input.
    :param str output: List of output file.
    :param float omargin: Output margin, in pt.
        Can also be a :class:`pdfimpose.schema.Margins` object.
    :param float imargin: Input margin, in pt.
    :param list[str] mark: List of marks to add.
        Only crop marks are supported (``mark=['crop']``); everything else is silently ignored.
    :param tuple[int] signature: Layout of source pages on output pages.
        For instance, ``(2, 3)`` means that each output page will contain
        2 columns and 3 rows of source pages.
    :param Optional[str] back: Back sides of cards. See --back help for more information.
    """
    if mark is None:
        mark = []

    CardsImpositor(
        omargin=omargin,
        imargin=imargin,
        mark=mark,
        signature=signature,
        back=back,
    ).impose(files, output)
