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

"""Hardcover binding (done in books, like dictionaries)

Hardcover binding is the schema used to print *real* books (novels, dictionnaries, etc.):
several destination pages are printed on a single, big, sheet of paper,
which is folded, and cut.
Those booklets are stacked onto each other, and bound together, to make your book.

To use this schema (without option --group, or with --group=1):

- print your imposed PDF file, two-sided;
- separately fold each sheet of paper;
- stack them;
- bind them.

With option --group=3 (for instance), repeat the step above for every group of three sheets. You get several signatures, that you have to bind together to get a proper book.
"""  # pylint: disable=line-too-long

import dataclasses
import decimal
import itertools
import math
import numbers
import typing

import papersize

from ... import UserError, pdf
from .. import BIND2ANGLE, DEFAULT_PAPER_SIZE, AbstractImpositor, Margins, Matrix, Page


def evenodd2oddeven(number):
    """Convert an even or odd number to the other number with the quotient by 2.

    For instance, 12 // 2 == 6 and 13 // 2 == 6, so:
    >> evenodd2oddeven(12)
    13
    >> evenodd2oddeven(13)
    12
    """
    if number % 2 == 0:
        return number + 1
    return number - 1


@dataclasses.dataclass
class HardcoverImpositor(AbstractImpositor):
    """Perform imposition of source files, with the 'hardcover' schema."""

    __uninitialized: typing.ClassVar[str] = ""
    folds: str = dataclasses.field(
        default_factory=lambda: HardcoverImpositor.__uninitialized
    )
    imargin: float = 0
    bind: str = "left"
    group: int = 1

    def __post_init__(self):
        super().__post_init__()
        if self.folds is self.__uninitialized:
            raise TypeError("Argument 'folds' must be given a value.")
        self.signature = (
            2 ** self.folds.count("h"),
            2 ** self.folds.count("v"),
        )
        if isinstance(self.imargin, decimal.Decimal):
            self.imargin = float(self.imargin)
        elif isinstance(self.imargin, str):
            self.imargin = float(papersize.parse_length(self.imargin))

    def fix_group(self, pages):
        """If `self.group == 0` compute the right group value, depending of the number of pages."""
        if self.group == 0:
            return math.ceil(pages / (2 * self.signature[0] * self.signature[1]))
        return self.group

    def blank_page_number(self, source):
        pagesperpage = 2 * self.signature[0] * self.signature[1]
        if source % (pagesperpage * self.fix_group(source)) == 0:
            return 0
        return pagesperpage * self.fix_group(source) - (
            source % (pagesperpage * self.fix_group(source))
        )

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

    def base_matrix(self, total):
        """Yield two matrixes (recto and verso) corresponding to one folded sheet."""
        # pylint: disable=unused-argument

        def _rotate(y):
            if self.signature[1] == 1:
                return [0, 180][y % 2]
            return [180, 0][y % 2]

        recto: list[list[int | None]] = [[0]]
        total = 2
        for fold in self.folds:
            total *= 2
            if fold == "h":
                recto = (
                    recto[: len(recto) // 2]
                    + [[None] * len(column) for column in recto]
                    + recto[len(recto) // 2 :]
                )
                for x, _ in enumerate(recto):
                    for y, _ in enumerate(recto[x]):
                        if recto[x][y] is None:
                            opp_recto = recto[evenodd2oddeven(x)][y]
                            assert opp_recto is not None
                            recto[x][y] = total - opp_recto - 1
            if fold == "v":
                recto = [
                    column[: len(column) // 2]
                    + [None] * len(column)
                    + column[len(column) // 2 :]
                    for column in recto
                ]
                # pylint: disable=consider-using-enumerate
                for x in range(len(recto)):
                    for y in range(len(recto[x])):
                        if recto[x][y] is None:
                            opp_recto = recto[x][evenodd2oddeven(y)]
                            assert opp_recto is not None
                            recto[x][y] = total - opp_recto - 1
        yield Matrix(
            [
                [
                    Page(
                        typing.cast(int, recto[x][y]),
                        rotate=_rotate(y),
                        **vars(self._margins(x, y)),
                    )
                    for y in range(len(recto[x]))
                    if recto[x][y] is not None
                ]
                for x in range(len(recto))
            ],
            rotate=BIND2ANGLE[self.bind],
        )
        yield Matrix(
            [
                [
                    Page(
                        evenodd2oddeven(recto[len(recto) - x - 1][y]),
                        rotate=_rotate(y),
                        **vars(self._margins(x, y)),
                    )
                    for y in range(len(recto[x]))
                ]
                for x in range(len(recto))
            ],
            rotate=BIND2ANGLE[self.bind],
        )

    def group_matrixes(self, total):
        """Yield matrixes corresponding to a group of sheets.

        1. First, we compute the matrix corresponding to a single folded sheet
           (see :meth:`HardcoverImpositor.base_matrix`).

        2. Then, we compute the matrix corresponding to the outer sheet of the group.
           Note that:

           - The way the sheet is folded is irrelevant here:
             everything can be computed using only page numbers, regardless of their position.
           - One side of the sheet, when folded, faces the same sheet, or the outer world;
             the other side, when folded, faces other sheets of the same group.

           Here is an example.
           Let's consider a (output) sheet with 8 (input) pages per (output page):
           this sheet has 16 input pages on it, from 0 to 15.
           When folded, the original page numbers become (with different ``self.group`` values):

           Original sheets: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
           self.group == 1: 0  1  6  7  8  9 14 15 16 17 22 23 24 25 30 31
           self.group == 2: 0  1 10 11 12 13 22 23 24 25 34 35 36 37 46 47
           self.group == 3: 0  1 14 15 16 17 30 31 32 33 46 47 48 49 62 63

           To compute this yourself, take 1, 2, 3 (or more) sheets of paper,
           place (output) page numbers on the outer one, fold them,
           and watch the new page numbers you get.

           Note that the numbers are consecutives, exepted for gaps every 4 numbers,
           starting between 1 and 2. Each of these gaps is 4×(self.group-1).
           Thus, the formula used to compute `outer` (see code below).

        3. At last, we compute the matrix of the inner sheets.
           Those being adjacent to the inner sheets,
           we simply add or substract page numbers to them.
        """
        for g in range(self.fix_group(total)):  #  pylint: disable=invalid-name
            for matrix in self.base_matrix(total):
                grouped: list[list[Page | None]] = [
                    [None for y in range(matrix.height)] for x in range(matrix.width)
                ]
                for x, y in matrix.coordinates():
                    # `outer` is the matrix of the outer sheet. Matrixes of the inner sheets will be computed by adding or substracting pages from `outer`.
                    outer = matrix[x, y].number + math.floor(
                        (matrix[x, y].number + 2) / 4
                    ) * 4 * (self.fix_group(total) - 1)
                    if g == 0:
                        grouped[x][y] = dataclasses.replace(matrix[x, y], number=outer)
                    elif matrix[x, y].number % 4 <= 1:
                        grouped[x][y] = dataclasses.replace(
                            matrix[x, y], number=outer + 2 * g
                        )
                    else:
                        grouped[x][y] = dataclasses.replace(
                            matrix[x, y], number=outer - 2 * g
                        )
                yield Matrix(typing.cast(list[list[Page]], grouped))

    def matrixes(self, pages: int) -> typing.Iterable[Matrix]:
        pages_per_group = (
            2 * self.signature[0] * self.signature[1] * self.fix_group(pages)
        )
        assert pages % pages_per_group == 0

        yield from self.stack_matrixes(
            list(self.group_matrixes(pages)),
            repeat=pages // pages_per_group,
            step=pages_per_group,
        )

    def bind_marks(self, number, total, matrix, outputsize, inputsize):
        # pylint: disable=too-many-arguments
        if number % 2 == 1:
            return

        if self.bind in ["top", "bottom"]:
            inputsize = (inputsize[1], inputsize[0])

        height = min(
            28, inputsize[1] / (total // (2 * matrix.width * matrix.height) + 2)
        )

        yield (
            (
                outputsize[0] - self.omargin.right - inputsize[0] - 1,
                outputsize[1] - self.omargin.bottom - height * (number // 2 + 2),
            ),
            (
                outputsize[0] - self.omargin.right - inputsize[0] + 1,
                outputsize[1] - self.omargin.bottom - height * (number // 2 + 1),
            ),
        )

    def crop_marks(self, number, total, matrix, outputsize, inputsize):
        # pylint: disable=too-many-arguments
        left, right, top, bottom = self._crop_space()
        if self.bind in ["top", "bottom"]:
            inputsize = (inputsize[1], inputsize[0])

        for x in range(self.signature[0] // 2):
            yield (
                (self.omargin.left + x * (2 * inputsize[0] + self.imargin), 0),
                (
                    self.omargin.left + x * (2 * inputsize[0] + self.imargin),
                    self.omargin.top - top,
                ),
            )
            yield (
                (
                    self.omargin.left + x * (2 * inputsize[0] + self.imargin),
                    outputsize[1],
                ),
                (
                    self.omargin.left + x * (2 * inputsize[0] + self.imargin),
                    outputsize[1] - self.omargin.bottom + bottom,
                ),
            )
            yield (
                (self.omargin.left + (x + 1) * 2 * inputsize[0] + x * self.imargin, 0),
                (
                    self.omargin.left + (x + 1) * 2 * inputsize[0] + x * self.imargin,
                    self.omargin.top - top,
                ),
            )
            yield (
                (
                    self.omargin.left + (x + 1) * 2 * inputsize[0] + x * self.imargin,
                    outputsize[1],
                ),
                (
                    self.omargin.left + (x + 1) * 2 * inputsize[0] + x * self.imargin,
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
            yield (
                ((0, self.omargin.top + (y + 1) * inputsize[1] + y * self.imargin)),
                (
                    self.omargin.left - left,
                    self.omargin.top + (y + 1) * inputsize[1] + y * self.imargin,
                ),
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
                    (
                        outputsize[0],
                        self.omargin.top + (y + 1) * inputsize[1] + y * self.imargin,
                    )
                ),
                (
                    outputsize[0] - self.omargin.right + right,
                    self.omargin.top + (y + 1) * inputsize[1] + y * self.imargin,
                ),
            )


def _signature2folds(width: float, height: float) -> str:
    """Convert a signature into a list of folds."""
    if width > height:
        alternator = itertools.cycle("hv")
    else:
        alternator = itertools.cycle("vh")

    folds = ""
    while width * height != 1:
        fold = next(alternator)
        folds += fold
        if fold == "h":
            width /= 2
        else:
            height /= 2

    return folds


def _ispowerof2(number):
    """Return True iff the number is a power of two."""
    # Is there a cleaner way?
    return round(math.log2(number)) == math.log2(number)


def _any2folds(
    signature: tuple[float, ...] | None,
    outputsize: tuple[float, ...] | None,
    *,
    inputsize: tuple[float, ...],
) -> tuple[str, tuple[float, ...] | None]:
    """Convert signature or outputsize to a list of folds."""
    # We enforce that the last fold is horizontal (to make sure the bind edge is correct).
    # To do so, we consider that the source page is twice as wide,
    # and we will add an "artificial" horizontal fold later in this function.
    inputsize = (2 * inputsize[0], inputsize[1])
    if signature is None and outputsize is None:
        outputsize = tuple(map(float, papersize.parse_papersize(DEFAULT_PAPER_SIZE)))
    if signature is not None:
        if not (_ispowerof2(signature[0]) and _ispowerof2(signature[1])):
            raise UserError("Both numbers of signature must be powers of two.")
        return _signature2folds(*signature), outputsize
    else:
        # We are rounding the ratio of (dest/source) to
        # 0.00001, so that 0.99999 is rounded to 1:
        # in some cases, we *should* get 1, but due to
        # floating point arithmetic, we get 0.99999
        # instead. We want it to be 1.
        #
        # Let's compute the error: how long is such an error?
        #
        # log2(ratio)=10^(-5) => ratio=2^(10^(-5))=1.00000693
        #
        # The ratio error is about 1.00000693.
        # What does this represent on the big side of an A4 sheet of paper?
        #
        # 0.00000693×29.7cm = 0.00020582cm = 2.0582 nm
        #
        # We are talking about a 2 nanometers error. We do not care.
        assert outputsize is not None, "outputsize should be assigned as (float, float)"
        notrotated = (
            math.floor(math.log2(round(outputsize[0] / inputsize[0], 5))),
            math.floor(math.log2(round(outputsize[1] / inputsize[1], 5))),
        )
        rotated = (
            math.floor(math.log2(round(outputsize[1] / inputsize[0], 5))),
            math.floor(math.log2(round(outputsize[0] / inputsize[1], 5))),
        )
        if (rotated[0] < 0 or rotated[1] < 0) and (
            notrotated[0] < 0 or notrotated[1] < 0
        ):
            raise UserError(
                "Incompatible source size, outputsize, bind edge, or signature."
            )
        if rotated[0] + rotated[1] > notrotated[0] + notrotated[1]:
            return _signature2folds(2 ** (1 + rotated[0]), 2 ** rotated[1]), (
                outputsize[1],
                outputsize[0],
            )
        return (
            _signature2folds(2 ** (1 + notrotated[0]), 2 ** notrotated[1]),
            outputsize,
        )


def _folds2margins(outputsize, sourcesize, folds, imargin):
    """Return output margins."""
    leftright = (
        outputsize[0]
        - sourcesize[0] * 2 ** folds.count("h")
        - imargin * (2 ** folds.count("h") - 1)
    )
    topbottom = (
        outputsize[1]
        - sourcesize[1] * 2 ** folds.count("v")
        - imargin * (2 ** folds.count("v") - 1)
    )
    return Margins(top=topbottom, bottom=topbottom, left=leftright, right=leftright)


def impose(
    files: typing.Iterable[typing.Union[str, typing.BinaryIO]] | pdf.Reader,
    output: str,
    *,
    folds: str | None = None,
    signature: tuple[float, ...] | None = None,
    size: str | tuple[float, ...] | None = None,
    imargin: float = 0,
    omargin: Margins | str | numbers.Real | decimal.Decimal | int = 0,
    mark: list[str] | None = None,
    last: int = 0,
    bind: str = "left",
    group: int = 1,
):  # pylint: disable=too-many-arguments
    """Perform imposition of source files into an output file, to be bound using "hardcover binding".

    :param list[str] files: List of source files (as strings or :class:`io.BytesIO` streams).
        If empty, reads from standard input.
    :param str output: List of output file.
    :param float omargin: Output margin, in pt. Can also be a :class:`Margins` object.
    :param float imargin: Input margin, in pt.
    :param list[str] mark: List of marks to add.
        Only crop marks are supported (`mark=['crop']`); everything else is silently ignored.
    :param str folds: Sequence of folds, as a string of characters `h` and `v`. Incompatible with `size` and `signature`.
    :param str size: Size of the destination pages, as a string that is to be parsed by :func:`papersize.parse_papersize`.
        This option is incompatible with `signature` and `folds`.
    :param tuple[int] signature: Layout of source pages on output pages.
        For instance ``(2, 3)`` means: the printed sheets are to be cut in a matrix of
        2 horizontal sheets per 3 vertical sheets.
        This option is incompatible with `size` and `folds`.
    :param str bind: Binding edge. Can be one of `left`, `right`, `top`, `bottom`.
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
        folds, size = _any2folds(
            signature,
            typing.cast(tuple[float, float] | None, size),
            inputsize=sourcesize,
        )
        if size is not None and imargin == 0:
            omargin = _folds2margins(size, sourcesize, folds, imargin)

    HardcoverImpositor(
        omargin=omargin,
        imargin=imargin,
        mark=mark,
        last=last,
        bind=bind,
        folds=folds,
        group=group,
    ).impose(files, output)
