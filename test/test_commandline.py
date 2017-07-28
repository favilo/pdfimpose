# Copyright 2017 Louis Paternault
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests"""

import os
import subprocess
import sys
import unittest

from wand.image import Image
import pkg_resources


if 'COVERAGE_PROCESS_START' in os.environ:
    EXECUTABLE = ["coverage", "run"]
else:
    EXECUTABLE = [sys.executable]

TEST_DATA_DIR = pkg_resources.resource_filename(__name__, "test_commandline-data")

FIXTURES = [
    {
        "command": [],
        "returncode": 2,
    },
    {
        "command": [
            "-f", "hv",
            os.path.join(TEST_DATA_DIR, "eight.pdf"),
            ],
        "returncode": 0,
        "diff": ("eight-impose.pdf", "eight-control.pdf")
    },
    {
        "command": [
            os.path.join(TEST_DATA_DIR, "malformed.pdf"),
            ],
        "returncode": 1,
        "stderr": "Error: Could not read file 'malformed.pdf'. Is it a valid PDF file?",
    },
    {
        "command": [
            os.path.join(TEST_DATA_DIR, "zero.pdf"),
            ],
        "returncode": 1,
        "stderr": "Error: Not a single page to process.",
    },
    {
        "before": [
            ["rm", os.path.join(TEST_DATA_DIR, "absent.pdf")],
            ],
        "command": [
            os.path.join(TEST_DATA_DIR, "absent.pdf"),
            ],
        "returncode": 1,
        "stderr": 'IO Error: Could not read "absent.pdf". TODO More info?',
    },
    {
        "before": [
            ["rm", os.path.join(TEST_DATA_DIR, "permission.pdf")],
            ["touch", os.path.join(TEST_DATA_DIR, "permission.pdf")],
            ["chmod", "-r", os.path.join(TEST_DATA_DIR, "permission.pdf")],
            ],
        "command": [
            os.path.join(TEST_DATA_DIR, "permission.pdf"),
            ],
        "returncode": 1,
        "stderr": 'IO Error: Could not read "permission.pdf". TODO More info?',
    },
]

WDEVNULL = open(os.devnull, 'w')
RDEVNULL = open(os.devnull, 'r')

def run(arguments):
    """Kind-of backport of subprocess.run() function from python3.4.

    Run "pdfimpose" with the arguments `arguments['command']` (feeding it
    `arguments['stdin']` as standard input if it exists).

    Return a dictionary with keys `stdout`, `stderr` (standard output and
    error, as strings), and `returncode` (as an integer).
    """
    completed = {}

    for command in arguments.get('before', []):
        subprocess.Popen(
            command,
            stdout=WDEVNULL,
            stderr=WDEVNULL,
            stdin=RDEVNULL,
            )
    process = subprocess.Popen(
        EXECUTABLE + ["-m", "pdfimpose"] + arguments['command'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        universal_newlines=True,
        )
    completed['stdout'], completed['stderr'] = process.communicate(arguments.get('stdin', None))
    completed['returncode'] = process.returncode
    return completed

class TestCommandLine(unittest.TestCase):
    """Run binary, and check produced files."""

    def assertPdfEqual(self, filea, fileb):
        """Test whether PDF files given in argument (as file names) are equal.

        Equal means: they look the same.
        """
        # pylint: disable=invalid-name
        images = (
            Image(filename=filea),
            Image(filename=fileb),
            )

        # Check that files have the same number of pages
        self.assertEqual(
            len(images[0].sequence),
            len(images[1].sequence),
            )

        # Check if pages look the same
        for (pagea, pageb) in zip(images[0].sequence, images[1].sequence):
            self.assertEqual(
                pagea.compare(pageb, metric="absolute")[1],
                0,
                )

    @unittest.skipIf(sys.version_info < (3, 5), "Tests require python version 3.5 or higher.")
    def test_commandline(self):
        """Test binary, from command line to produced files."""
        for data in FIXTURES:
            with self.subTest(**data):
                completed = run(data)

                for key in ["returncode", "stderr", "stdout"]:
                    if key in data:
                        self.assertEqual(
                            completed.get(key),
                            data.get(key),
                            )

                if "diff" in data:
                    self.assertPdfEqual(*(
                        os.path.join(TEST_DATA_DIR, filename)
                        for filename in data['diff']
                        ))
