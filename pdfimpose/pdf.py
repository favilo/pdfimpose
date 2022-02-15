# Copyright 2021-2022 Louis Paternault
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

"""Read and write PDF files."""

import contextlib
import functools
import io
import logging
import sys

import fitz

from . import VERSION, UserError

_BLACK = fitz.utils.getColor("black")


def readpdf(file):
    """Read a PDF file.

    The argument can be:
    - a filename (type `str`);
    - a stream, as returnd with ``open("foo.pdf", mode="rb")`` (type `io.BytesIO`);
    - a `fitz.Document` object.
    """
    try:
        if isinstance(file, str):
            return fitz.Document(file)
        if isinstance(file, io.IOBase):
            if file.name:
                kwargs = {"filename": file.name}
            else:
                kwargs = {"filetype": "application/pdf"}
            return fitz.Document(stream=file.read(), **kwargs)
        if isinstance(file, fitz.Document):
            return file
    except Exception as error:
        raise UserError(f"Cannot open document '{file}': {error}.") from error
    raise TypeError


class Reader(contextlib.AbstractContextManager):
    """Read a PDF file."""

    def __init__(self, files):
        super().__init__()
        self._blank_number = 0
        self._blank_position = 0

        if not files:
            # Read from standard input
            self.files = [readpdf(sys.stdin.buffer)]
        else:
            self.files = [readpdf(name) for name in files]

        # There is at least one page
        if len(self) == 0:
            raise UserError("There is not a single page in the source documents.")

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
                "Pages of source files have different size. "
                "This is unsupported and will lead to unexpected results."
            )

    def set_final_blank_pages(self, number, position):
        """Set the position and number of blank pages to be inserted in the document.

        position: index of first blank page
        number: number of blank pages.
        """
        self._blank_number = number
        self._blank_position = position

    @property
    def size(self):
        """Return the size of an arbitrary page of the document.

        The size is returned as a tuple `(width, height)`.
        """
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

    def __getitem__(self, key):  # pylint: disable=inconsistent-return-statements
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
            if self.name is None:
                sys.stdout.buffer.write(self.doc.write())
            else:
                self.doc.save(self.name)
        self.doc.close()

    def new_page(self, width, height):
        """Create a new page, and return its page number."""
        # pylint: disable=no-member
        return self.doc.newPage(width=width, height=height).number

    def insert(self, number, source, topleft, rotate):
        """Insert a pdf page (source) into another pdf page (destination).

        :param int number: Destination page number.
        :param fitz.Page source: Source page to insert.
        :param fitz.Rect topleft: Position (on the dest page)
            of the topleft corner of the source page.
        :param int rotate: Angle of a rotation to apply to the source page (one of 0, 90, 180, 270).
        """
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

    def __getitem__(self, key):
        return self.doc[key]

    def draw_rectangle(self, page, rect):
        """Draw a black rectangle on the given page.

        :param int page: Page number
        :param tuple[tuple[Int, Int], tuple[Int, Int]] rect: Coordinates of the rectangles.
        """
        self.doc[page].draw_rect(fitz.Rect(*rect), color=_BLACK, fill=_BLACK)

    def set_metadata(self, source):
        """Read metadata from the input files, and (kind of) copy them to the output file."""
        metadata = {}
        for keyword in ("title", "author", "subject", "keywords"):
            metadata[keyword] = ", ".join(
                doc.metadata.get(keyword, ()) for doc in source.files
            )
        metadata[
            "creator"
        ] = "Created with PdfImpose — https://framagit.org/spalax/pdfimpose"
        metadata["producer"] = f"pdfimpose-{VERSION}"
        # pylint: disable=no-member
        self.doc.setMetadata(metadata)
