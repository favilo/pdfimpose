# Copyright 2017-2021 Louis Paternault
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

import os
import subprocess
import sys
import textwrap
import unittest

from wand.image import Image
import pkg_resources


if "COVERAGE_PROCESS_START" in os.environ:
    EXECUTABLE = ["coverage", "run"]
else:
    EXECUTABLE = [sys.executable]

TEST_DATA_DIR = pkg_resources.resource_filename(__name__, "test_commandline-data")
ROOT_DIR = os.path.abspath(os.path.join(TEST_DATA_DIR, "..", ".."))

# pylint: disable=line-too-long
FIXTURES = {
    "errors": (
        {"command": [], "returncode": 2},
        {
            "command": ["perfect", "malformed.pdf"],
            "returncode": 1,
        },
        {
            "command": ["saddle", "zero.pdf"],
            "returncode": 1,
            "stderr": "ERROR:root:There is not a single page in the source documents.\n",
        },
        {
            "command": ["cards", "A3.pdf"],
            "returncode": 1,
            "stderr": "ERROR:root:The source page is too big to fit in the destination page.\n",
        },
        {
            "before": [["rm", "-f", "absent.pdf"]],
            "command": ["wire", "absent.pdf"],
            "returncode": 1,
            "stderr": textwrap.dedent(
                """\
                mupdf: cannot open absent.pdf: No such file or directory
                ERROR:root:Cannot open document 'absent.pdf': cannot open absent.pdf: No such file or directory.
                """
            ),
        },
        {"command": ["cutstackfold", "nometadata.pdf"], "returncode": 0},
    ),
    "perfect": (
        {
            "command": [
                "perfect",
                "small.pdf",
                "--signature",
                "4x4",
                "--mark",
                "crop",
                "-k",
                "bind",
                "--bind",
                "top",
                "-m",
                "2cm",
                "-M",
                "1cm",
            ],
            "returncode": 0,
            "diff": (
                "small-impose.pdf",
                "small-control.pdf",
            ),
        },
    ),
    "cards": (
        {
            "command": [
                "cards",
                "cards-9x9.pdf",
                "-o",
                "cards-9x9-impose.pdf",
                "--mark",
                "crop",
            ],
            "returncode": 0,
            "diff": (
                "cards-9x9-impose.pdf",
                "cards-9x9-control.pdf",
            ),
        },
    ),
    "wire": (
        {
            "command": [
                "wire",
                "wire-9x9.pdf",
                "-o",
                "wire-9x9-impose.pdf",
                "--format",
                "A4",
                "--mark",
                "crop",
            ],
            "returncode": 0,
            "diff": (
                "wire-9x9-impose.pdf",
                "wire-9x9-control.pdf",
            ),
        },
        {
            "command": [
                "wire",
                "wire.pdf",
                "-o",
                "wire-impose.pdf",
                "--signature",
                "3x2",
                "--imargin",
                "2mm",
                "--omargin",
                "5mm",
                "--mark",
                "crop",
            ],
            "returncode": 0,
            "diff": (
                "wire-impose.pdf",
                "wire-control.pdf",
            ),
        },
    ),
    "onepagezine": (
        {
            "command": [
                "onepagezine",
                "8a6-portrait.pdf",
                "-o",
                "8a6-onepagezine-right-impose.pdf",
                "-b",
                "right",
            ],
            "returncode": 0,
            "diff": (
                "8a6-onepagezine-right-impose.pdf",
                "8a6-onepagezine-right-control.pdf",
            ),
        },
        {
            "command": [
                "onepagezine",
                "8a6-landscape.pdf",
                "-o",
                "8a6-onepagezine-top-impose.pdf",
                "-b",
                "top",
            ],
            "returncode": 0,
            "diff": (
                "8a6-onepagezine-top-impose.pdf",
                "8a6-onepagezine-top-control.pdf",
            ),
        },
        {
            "command": [
                "onepagezine",
                "8a6-landscape.pdf",
                "-o",
                "8a6-onepagezine-bottom-impose.pdf",
                "-b",
                "bottom",
            ],
            "returncode": 0,
            "diff": (
                "8a6-onepagezine-bottom-impose.pdf",
                "8a6-onepagezine-bottom-control.pdf",
            ),
        },
        {
            "command": [
                "onepagezine",
                "8a6-portrait.pdf",
                "-o",
                "8a6-onepagezine-left-impose.pdf",
                "-b",
                "left",
            ],
            "returncode": 0,
            "diff": (
                "8a6-onepagezine-left-impose.pdf",
                "8a6-onepagezine-left-control.pdf",
            ),
        },
        {
            "command": [
                "onepagezine",
                "onepagezine-8a6",
                "onepagezine-5a6.pdf",
                "--last",
                "1",
                "--omargin",
                "20mm",
                "--mark",
                "crop",
            ],
            "returncode": 0,
            "diff": (
                "onepagezine-8a6-impose.pdf",
                "onepagezine-8a6-impose-control.pdf",
            ),
        },
    ),
    "cutstackfold": (
        {
            "command": [
                "cutstackfold",
                "cutstackfold.pdf",
                "-m",
                "1cm",
                "-M",
                "2cm",
                "-c",
                "5s",
                "-k",
                "crop",
            ],
            "returncode": 0,
            "diff": (
                "cutstackfold-impose.pdf",
                "cutstackfold-control.pdf",
            ),
        },
    ),
    "saddle": (
        {
            "command": [
                "saddle",
                "saddle.pdf",
                "--last",
                "1",
                "--format",
                "A7",
                "--bind",
                "left",
            ],
            "returncode": 0,
            "diff": (
                "saddle-impose.pdf",
                "saddle-control.pdf",
            ),
        },
    ),
    "copycutfold": (
        {
            "command": [
                "copycutfold",
                "copycutfold.pdf",
                "-l1",
                "-fa4",
                "-m1cm",
                "-M.5cm",
                "-c1s",
                "-kcrop",
            ],
            "returncode": 0,
            "diff": (
                "copycutfold-impose.pdf",
                "copycutfold-control.pdf",
            ),
        },
    ),
    "apply": (
        {
            "command": [
                "apply",
            ],
            "returncode": 0,
            "diff": (
                "foo-control.pdf",
                "foo-impose.pdf",
            ),
        },
    ),
}


class TestCommandLine(unittest.TestCase):
    """Run binary, and check produced files."""

    maxDiff = None

    def setUp(self):
        self.environ = os.environ.copy()
        self.environ["PYTHONPATH"] = f"{ROOT_DIR}:self.environ['PYTHONPATH']"

    def assertPdfEqual(self, filea, fileb):
        """Test whether PDF files given in argument (as file names) are equal.

        Equal means: they look the same.
        """
        # pylint: disable=invalid-name
        images = (Image(filename=filea), Image(filename=fileb))

        # Check that files have the same number of pages
        self.assertEqual(len(images[0].sequence), len(images[1].sequence))

        # Check if pages look the same
        for (pagea, pageb) in zip(images[0].sequence, images[1].sequence):
            self.assertEqual(pagea.compare(pageb, metric="absolute")[1], 0)

    def _test_commandline(self, subtest):
        """Test binary, from command line to produced files."""
        for data in FIXTURES[subtest]:
            with self.subTest(**data):
                for command in data.get("before", ()):
                    subprocess.run(
                        command,
                        env=self.environ,
                        cwd=os.path.join(TEST_DATA_DIR, subtest),
                        check=True,
                    )
                completed = subprocess.run(  # pylint: disable=subprocess-run-check
                    EXECUTABLE + ["-m", "pdfimpose"] + data["command"],
                    env=self.environ,
                    cwd=os.path.join(TEST_DATA_DIR, subtest),
                    capture_output=True,
                    text=True,
                )

                for key in ["returncode", "stderr", "stdout"]:
                    if key in data:
                        self.assertEqual(getattr(completed, key), data.get(key))

                if "diff" in data:
                    self.assertPdfEqual(
                        *(
                            os.path.join(TEST_DATA_DIR, subtest, filename)
                            for filename in data["diff"]
                        )
                    )

    def test_errors(self):
        """Test of commands that raise errors."""
        return self._test_commandline("errors")

    def test_onepagezine(self):
        """Test of the one-page-zine schema."""
        return self._test_commandline("onepagezine")

    def test_cards(self):
        """Test of the cards schema."""
        return self._test_commandline("cards")

    def test_wire(self):
        """Test of the wire schema."""
        return self._test_commandline("wire")

    def test_cutstackfold(self):
        """Test of the cut-stack-fold schema."""
        return self._test_commandline("cutstackfold")

    def test_perfect(self):
        """Test of the perfect-bind schema."""
        return self._test_commandline("perfect")

    def test_saddle(self):
        """Test of the saddle-stitch schema."""
        return self._test_commandline("saddle")

    def test_copycutfold(self):
        """Test of the copy-cut-fold schema."""
        return self._test_commandline("copycutfold")

    def test_apply(self):
        """Test of the "apply" subcommand."""
        return self._test_commandline("apply")
