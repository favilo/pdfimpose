# Copyright 2024 Louis Paternault
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

"""Tests"""

import decimal
import pathlib
import sys
import unittest

import papersize

from pdfimpose.schema import onepagezine, Margins

from .. import TestComparePDF

TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"
TEST_FILE = TEST_DATA_DIR / "A7.pdf"


class TestLibrary(TestComparePDF):
    """Test library calls"""

    @staticmethod
    def outputfiles(prefix, suffixes):
        """Return names for output files with given suffixes."""
        return tuple(
            TEST_FILE.with_stem(f"{TEST_FILE.stem}-{prefix}-{suffix}")
            for suffix in suffixes
        )

    def test_filetype(self):
        """Test that both `str` and `pathlib.Path` are valid types for file input."""
        file1, file2 = self.outputfiles("filetype", ("str", "pathlib"))
        onepagezine.impose([pathlib.Path(TEST_FILE)], file1)
        onepagezine.impose([str(TEST_FILE)], file2)
        self.assertPdfEqual(file1, file2)

    def test_onepagezine(self):
        """Test types of :func:`pdfimpose.schema.onepagezine.impose`."""
        files = self.outputfiles(
            "onepagezine-margin", ("decimal", "float", "Margins", "str")
        )
        onepagezine.impose(
            [TEST_FILE],
            files[0],
            omargin=decimal.Decimal(papersize.parse_length("1cm")),
        )
        onepagezine.impose(
            [TEST_FILE], files[1], omargin=float(papersize.parse_length("1cm"))
        )
        onepagezine.impose(
            [TEST_FILE], files[2], omargin=Margins(float(papersize.parse_length("1cm")))
        )
        onepagezine.impose([TEST_FILE], files[3], omargin="1cm")
        self.assertPdfEqual(*files)
