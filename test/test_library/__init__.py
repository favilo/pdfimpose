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

from pdfimpose.schema import (
    Margins,
    cards,
    copycutfold,
    cutstackfold,
    hardcover,
    onepagezine,
    saddle,
    wire,
)

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

    def test_copycutfold(self):
        """Test types of :func:`pdfimpose.schema.copycutfold.impose`."""
        with self.subTest("margins"):
            files = self.outputfiles("copycutfold-margin", ("decimal", "float", "str"))
            copycutfold.impose(
                [TEST_FILE],
                files[0],
                signature=(2, 2),
                omargin=decimal.Decimal(papersize.parse_length("1cm")),
                imargin=decimal.Decimal(papersize.parse_length("1cm")),
            )
            copycutfold.impose(
                [TEST_FILE],
                files[1],
                signature=(2, 2),
                omargin=float(papersize.parse_length("1cm")),
                imargin=float(papersize.parse_length("1cm")),
            )
            copycutfold.impose(
                [TEST_FILE], files[2], signature=(2, 2), omargin="1cm", imargin="1cm"
            )
            self.assertPdfEqual(*files)

        with self.subTest("format"):
            files = self.outputfiles(
                "copycutfold-size", ("signature", "custom", "standard")
            )
            copycutfold.impose([TEST_FILE], files[0], signature=(2, 2))
            copycutfold.impose([TEST_FILE], files[1], size="A4")
            copycutfold.impose([TEST_FILE], files[2], size="21cmx29.7cm")
            self.assertPdfEqual(*files, threshold=40000)

    def test_cutstackfold(self):
        """Test types of :func:`pdfimpose.schema.cutstackfold.impose`."""
        with self.subTest("margins"):
            files = self.outputfiles("cutstackfold-margin", ("decimal", "float", "str"))
            cutstackfold.impose(
                [TEST_FILE],
                files[0],
                signature=(2, 2),
                omargin=decimal.Decimal(papersize.parse_length("1cm")),
                imargin=decimal.Decimal(papersize.parse_length("1cm")),
            )
            cutstackfold.impose(
                [TEST_FILE],
                files[1],
                signature=(2, 2),
                omargin=float(papersize.parse_length("1cm")),
                imargin=float(papersize.parse_length("1cm")),
            )
            cutstackfold.impose(
                [TEST_FILE], files[2], signature=(2, 2), omargin="1cm", imargin="1cm"
            )
            self.assertPdfEqual(*files)

        with self.subTest("format"):
            files = self.outputfiles(
                "cutstackfold-size", ("signature", "custom", "standard")
            )
            cutstackfold.impose([TEST_FILE], files[0], signature=(2, 2))
            cutstackfold.impose([TEST_FILE], files[1], size="A4")
            cutstackfold.impose([TEST_FILE], files[2], size="21cmx29.7cm")
            self.assertPdfEqual(*files, threshold=25000)

    def test_cards(self):
        """Test types of :func:`pdfimpose.schema.cards.impose`."""
        with self.subTest("margins"):
            files = self.outputfiles("cards-margin", ("decimal", "float", "str"))
            cards.impose(
                [TEST_FILE],
                files[0],
                signature=(2, 2),
                omargin=decimal.Decimal(papersize.parse_length("1cm")),
                imargin=decimal.Decimal(papersize.parse_length("1cm")),
            )
            cards.impose(
                [TEST_FILE],
                files[1],
                signature=(2, 2),
                omargin=float(papersize.parse_length("1cm")),
                imargin=float(papersize.parse_length("1cm")),
            )
            cards.impose(
                [TEST_FILE], files[2], signature=(2, 2), omargin="1cm", imargin="1cm"
            )
            self.assertPdfEqual(*files)

        with self.subTest("format"):
            files = self.outputfiles("cards-size", ("signature", "custom", "standard"))
            cards.impose([TEST_FILE], files[0], signature=(4, 2))
            cards.impose([TEST_FILE], files[1], size="A4")
            cards.impose([TEST_FILE], files[2], size="21cmx29.7cm")
            self.assertPdfEqual(*files, threshold=20000)

    def test_wire(self):
        """Test types of :func:`pdfimpose.schema.wire.impose`."""
        with self.subTest("margins"):
            files = self.outputfiles("wire-margin", ("decimal", "float", "str"))
            wire.impose(
                [TEST_FILE],
                files[0],
                signature=(2, 2),
                omargin=decimal.Decimal(papersize.parse_length("1cm")),
                imargin=decimal.Decimal(papersize.parse_length("1cm")),
            )
            wire.impose(
                [TEST_FILE],
                files[1],
                signature=(2, 2),
                omargin=float(papersize.parse_length("1cm")),
                imargin=float(papersize.parse_length("1cm")),
            )
            wire.impose(
                [TEST_FILE], files[2], signature=(2, 2), omargin="1cm", imargin="1cm"
            )
            self.assertPdfEqual(*files)

        with self.subTest("format"):
            files = self.outputfiles("wire-size", ("signature", "custom", "standard"))
            wire.impose([TEST_FILE], files[0], signature=(4, 2))
            wire.impose([TEST_FILE], files[1], size="A4")
            wire.impose([TEST_FILE], files[2], size="21cmx29.7cm")
            self.assertPdfEqual(*files, threshold=20000)

    def test_hardcover(self):
        """Test types of :func:`pdfimpose.schema.hardcover.impose`."""
        with self.subTest("margins"):
            files = self.outputfiles("hardcover-margin", ("decimal", "float", "str"))
            hardcover.impose(
                [TEST_FILE],
                files[0],
                folds="hv",
                omargin=decimal.Decimal(papersize.parse_length("1cm")),
                imargin=decimal.Decimal(papersize.parse_length("1cm")),
            )
            hardcover.impose(
                [TEST_FILE],
                files[1],
                folds="hv",
                omargin=float(papersize.parse_length("1cm")),
                imargin=float(papersize.parse_length("1cm")),
            )
            hardcover.impose(
                [TEST_FILE], files[2], folds="hv", omargin="1cm", imargin="1cm"
            )
            self.assertPdfEqual(*files)

        with self.subTest("format"):
            files = self.outputfiles(
                "hardcover-size", ("signature", "standard", "custom", "folds")
            )
            hardcover.impose([TEST_FILE], files[0], signature=(4, 2))
            hardcover.impose([TEST_FILE], files[1], size="A4")
            hardcover.impose([TEST_FILE], files[2], size="21cmx29.7cm")
            hardcover.impose([TEST_FILE], files[3], folds="hvh")
            self.assertPdfEqual(*files, threshold=40000)

    def test_saddle(self):
        """Test types of :func:`pdfimpose.schema.saddle.impose`."""
        with self.subTest("margins"):
            files = self.outputfiles("saddle-margin", ("decimal", "float", "str"))
            saddle.impose(
                [TEST_FILE],
                files[0],
                folds="hv",
                omargin=decimal.Decimal(papersize.parse_length("1cm")),
                imargin=decimal.Decimal(papersize.parse_length("1cm")),
            )
            saddle.impose(
                [TEST_FILE],
                files[1],
                folds="hv",
                omargin=float(papersize.parse_length("1cm")),
                imargin=float(papersize.parse_length("1cm")),
            )
            saddle.impose(
                [TEST_FILE], files[2], folds="hv", omargin="1cm", imargin="1cm"
            )
            self.assertPdfEqual(*files)

        with self.subTest("format"):
            files = self.outputfiles(
                "saddle-size", ("signature", "standard", "custom", "folds")
            )
            saddle.impose([TEST_FILE], files[0], signature=(4, 2))
            saddle.impose([TEST_FILE], files[1], size="A4")
            saddle.impose([TEST_FILE], files[2], size="21cmx29.7cm")
            saddle.impose([TEST_FILE], files[3], folds="hvh")
            self.assertPdfEqual(*files, threshold=40000)
