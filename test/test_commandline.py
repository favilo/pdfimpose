# -*- coding: utf-8 -*-

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


if "COVERAGE_PROCESS_START" in os.environ:
    EXECUTABLE = ["coverage", "run"]
else:
    EXECUTABLE = [sys.executable]

TEST_DATA_DIR = pkg_resources.resource_filename(__name__, "test_commandline-data")

FIXTURES = [
    {"command": [], "returncode": 1},
    {
        "command": [
            "onepagezine",
            "8a6-portrait.pdf",
            "-o",
            "8a6-onepagezine-right.pdf",
            "-b",
            "right",
        ],
        "returncode": 0,
        "diff": ("8a6-onepagezine-right.pdf", "8a6-onepagezine-right-control.pdf"),
    },
    {
        "command": [
            "onepagezine",
            "8a6-portrait.pdf",
            "-o",
            "8a6-onepagezine-top.pdf",
            "-b",
            "top",
        ],
        "returncode": 0,
        "diff": ("8a6-onepagezine-top.pdf", "8a6-onepagezine-top-control.pdf"),
    },
    {
        "command": [
            "onepagezine",
            "8a6-portrait.pdf",
            "-o",
            "8a6-onepagezine-bottom.pdf",
            "-b",
            "bottom",
        ],
        "returncode": 0,
        "diff": ("8a6-onepagezine-bottom.pdf", "8a6-onepagezine-bottom-control.pdf"),
    },
    {
        "command": [
            "onepagezine",
            "8a6-portrait.pdf",
            "-o",
            "8a6-onepagezine-left.pdf",
            "-b",
            "left",
        ],
        "returncode": 0,
        "diff": ("8a6-onepagezine-left.pdf", "8a6-onepagezine-left-control.pdf"),
    },
    {
        "command": [
            "onepagezine",
            "onepagesize-8a6",
            "onepagesize-5a6.pdf",
            "--last",
            "1",
            "--imargin",
            "10mm",
            "--omargin",
            "20mm",
        ],
        "returncode": 0,
        "diff": ("onepagesize-8a6-impose.pdf", "onepagesize-8a6-impose-control.pdf"),
    },
    # {
    #    "command": [os.path.join(TEST_DATA_DIR, "malformed.pdf")],
    #    "returncode": 1,
    #    "stderr": "Error: Could not read file '{}': EOF marker not found.\n".format(
    #        os.path.join(TEST_DATA_DIR, "malformed.pdf")
    #    ),  # pylint: disable=line-too-long
    # },
    # {
    #    "command": [os.path.join(TEST_DATA_DIR, "zero.pdf")],
    #    "returncode": 1,
    #    "stderr": "Error: Not a single page to process.\n",
    # },
    # {
    #    "before": [["rm", os.path.join(TEST_DATA_DIR, "absent.pdf")]],
    #    "command": [os.path.join(TEST_DATA_DIR, "absent.pdf")],
    #    "returncode": 1,
    #    "stderr": "Error: Could not read file '{filename}': [Errno 2] No such file or directory: '{filename}'.\n".format(  # pylint: disable=line-too-long
    #        filename=os.path.join(TEST_DATA_DIR, "absent.pdf")
    #    ),
    # },
    # {"command": [os.path.join(TEST_DATA_DIR, "nometadata.pdf")], "returncode": 0},
]

WDEVNULL = open(os.devnull, "w")
RDEVNULL = open(os.devnull, "r")


def run(arguments):
    """Kind-of backport of subprocess.run() function from python3.4.

    Run "pdfimpose" with the arguments `arguments['command']` (feeding it
    `arguments['stdin']` as standard input if it exists).

    Return a dictionary with keys `stdout`, `stderr` (standard output and
    error, as strings), and `returncode` (as an integer).

    # TODO: Update to python3.8
    """
    completed = {}

    for command in arguments.get("before", []):
        subprocess.Popen(
            command, stdout=WDEVNULL, stderr=WDEVNULL, stdin=RDEVNULL, cwd=TEST_DATA_DIR
        )
    process = subprocess.Popen(
        EXECUTABLE + ["-m", "pdfimpose"] + arguments["command"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        universal_newlines=True,
        cwd=TEST_DATA_DIR,
    )
    completed["stdout"], completed["stderr"] = process.communicate(
        arguments.get("stdin", None)
    )
    completed["returncode"] = process.returncode
    return completed


class TestCommandLine(unittest.TestCase):
    """Run binary, and check produced files."""

    maxDiff = None

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

    def test_commandline(self):
        """Test binary, from command line to produced files."""
        for data in FIXTURES:
            with self.subTest(**data):
                completed = run(data)

                for key in ["returncode", "stderr", "stdout"]:
                    if key in data:
                        self.assertEqual(completed.get(key), data.get(key))

                if "diff" in data:
                    self.assertPdfEqual(
                        *(
                            os.path.join(TEST_DATA_DIR, filename)
                            for filename in data["diff"]
                        )
                    )
