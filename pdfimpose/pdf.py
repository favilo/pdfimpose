# Copyright 2021 Louis Paternault
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

import contextlib
import functools
import io
import logging

import fitz


class Reader(contextlib.AbstractContextManager):
    """Read a PDF file."""

    def __init__(self, files):
        super().__init__()
        self._blank_number = 0
        self._blank_position = 0

        if not files:
            # Read from standard input
            self.files = [
                fitz.Document(
                    stream=io.BytesIO(sys.stdin.buffer.read()),
                    filetype="application/pdf",
                )
            ]
        else:
            self.files = [fitz.Document(name) for name in files]

        # All pages have the same size
        if (
            len(
                set(
                    tuple(map(functools.partial(round, ndigits=5), page.cropbox))
                    for page in self
                )
            )
            != 1
        ):
            logging.warning(
                "Pages of source files have different size. This is unsupported and will lead to unexpected results."
            )

    def set_final_blank_pages(self, number, position):
        """TODO

        position: index of first blank page
        number: number of blank pages.
        """
        self._blank_number = number
        self._blank_position = position

    @property
    def size(self):
        # Either first or last page is not empty
        if self[0] is None:
            page = self[len(self) - 1]
        else:
            page = self[0]
        return (
            page.cropbox.width,
            page.cropbox.height,
        )

    def __len__(self):
        return sum(len(file) for file in self.files) + self._blank_number

    def __iter__(self):
        for number in range(len(self)):
            yield self[number]

    def __getitem__(self, key):
        if self._blank_position <= key < self._blank_position + self._blank_number:
            # Return a blank page
            return None
        if key >= self._blank_position + self._blank_number:
            key -= self._blank_number

        cumulative = 0
        for file in self.files:
            if key < cumulative + len(file):
                return file[key - cumulative]
            cumulative += len(file)

    def __exit__(self, *args, **kwargs):
        super().__exit__(*args, **kwargs)
        for file in self.files:
            file.close()


class Writer(contextlib.AbstractContextManager):
    """Write a PDF file."""

    def __init__(self, output):
        super().__init__()
        self.name = output
        self.doc = fitz.Document()

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is None:
            self.doc.save(self.name)
        self.doc.close()

    def new_page(self, width, height):
        return self.doc.newPage(width=width, height=height).number

    def insert(self, number, source, topleft, rotate):
        if rotate in (90, 270):
            rect = fitz.Rect(
                topleft,
                fitz.Point(topleft)
                + fitz.Point(source.cropbox.height, source.cropbox.width),
            )
        else:
            rect = fitz.Rect(
                topleft,
                fitz.Point(topleft)
                + fitz.Point(source.cropbox.width, source.cropbox.height),
            )
        self.doc[number].show_pdf_page(
            rect, source.parent, source.number, rotate=rotate
        )
