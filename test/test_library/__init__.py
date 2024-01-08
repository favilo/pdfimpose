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

import unittest
import sys
import pathlib

from pdfimpose.schema import onepagezine

TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"
TEST_FILE = TEST_DATA_DIR / "A7.pdf"

from wand.image import Image

class TestLibrary(unittest.TestCase):
    """Test library calls"""

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


    def test_filetype(self):
        file1 = TEST_FILE.with_stem("filetype1")
        onepagezine.impose([pathlib.Path(TEST_FILE)], file1)

        file2 = TEST_FILE.with_stem("filetype2")
        onepagezine.impose([str(TEST_FILE)], file2)

        self.assertPdfEqual(file1, file2)


    def test_onepagezine(self):
        TODO

    def _test_commandline(self, subtest):
        """Test binary, from command line to produced files."""
        for data in FIXTURES[subtest]:
            with self.subTest(**data):
                for command in data.get("before", ()):
                    subprocess.run(
                        command,
                        env=self.environ,
                        cwd=TEST_DATA_DIR / subtest,
                        check=True,
                    )
                completed = subprocess.run(  # pylint: disable=subprocess-run-check
                    EXECUTABLE + ["-m", "pdfimpose"] + data["command"],
                    env=self.environ,
                    cwd=TEST_DATA_DIR / subtest,
                    capture_output=True,
                    text=True,
                )

                for key in ["returncode", "stderr", "stdout"]:
                    if key in data:
                        self.assertEqual(getattr(completed, key), data.get(key))

                if "diff" in data:
                    self.assertPdfEqual(
                        *(
                            TEST_DATA_DIR / subtest / filename
                            for filename in data["diff"]
                        )
                    )
