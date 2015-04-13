#!/usr/bin python
# -*- coding: utf-8 -*-

# Copyright 2015 Louis Paternault
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

"""Command line tests

Unfortunately, those tests only check that program works without exception; it
does not check the resulting file.
"""

import contextlib
import os
import sys
import unittest

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from pdfimpose.main import main

@contextlib.contextmanager
def capture():
    """Context to capture (and disable) standard output and error.
    """
    oldout, olderr = sys.stdout, sys.stderr
    try:
        out = [StringIO(), StringIO()]
        sys.stdout, sys.stderr = out
        yield out
    finally:
        sys.stdout, sys.stderr = oldout, olderr
        out[0] = out[0].getvalue()
        out[1] = out[1].getvalue()

def datadir(*args):
    """Return the path corresponding to the argument, as a subpath of test data directory.
    """
    return os.path.join(
        os.path.dirname(__file__),
        "data",
        *args
        )

class TestCommandLine(unittest.TestCase):
    """Command line tests."""

    def assertExit(self, code, function, *args, **kwargs): # pylint: disable=invalid-name
        """Assert that function exits (SystemExit) with the right code."""
        with self.assertRaises(SystemExit) as exception:
            with capture():
                function(*args, **kwargs)
        self.assertEqual(exception.exception.code, code)

    def test_empty(self):
        """Test if no argument is given"""
        self.assertExit(
            2,
            main,
            [],
            )

    def test_file(self):
        """Test if a single file is given as argument."""
        self.assertExit(
            0,
            main,
            [datadir("dummy2.pdf")],
            )
        self.assertExit(
            0,
            main,
            [datadir("dummy64.pdf")],
            )
