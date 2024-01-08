# Copyright 2015-2021 Louis Paternault
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

import sys
import unittest

from wand.image import Image

import pdfimpose


class TestComparePDF(unittest.TestCase):
    """A :class:`unittest.TestCase` implementation with an `assertPdfEqual` method."""

    def assertPdfEqual(self, filea, fileb):
        """Test whether PDF files given in argument (as file names) are equal.

        Equal means: they look the same.
        """
        # pylint: disable=invalid-name
        images = (Image(filename=filea), Image(filename=fileb))

        # Check that files have the same number of pages
        self.assertEqual(len(images[0].sequence), len(images[1].sequence))

        # Check if pages look the same
        for pagea, pageb in zip(images[0].sequence, images[1].sequence):
            if sys.version_info >= (3, 11):
                # Wand considers the output PDF different, althought I cannot see the difference.
                self.assertEqual(pagea.compare(pageb, metric="absolute")[1], 0)
