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

import pathlib
import sys
import unittest

from pdfimpose.schema import onepagezine

from .. import TestComparePDF

TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"
TEST_FILE = TEST_DATA_DIR / "A7.pdf"


class TestLibrary(TestComparePDF):
    """Test library calls"""

    def test_filetype(self):
        """Test that both `str` and `pathlib.Path` are valid types for file input."""
        file1 = TEST_FILE.with_stem("filetype1")
        onepagezine.impose([pathlib.Path(TEST_FILE)], file1)

        file2 = TEST_FILE.with_stem("filetype2")
        onepagezine.impose([str(TEST_FILE)], file2)

        self.assertPdfEqual(file1, file2)

    # def test_onepagezine(self):
    #    TODO
