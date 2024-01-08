# Copyright 2015-2024 Louis Paternault
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

import doctest
import importlib
import pkgutil

import pdfimpose


def load_tests(__loader, tests, __pattern):
    """Load tests (unittests and doctests)."""
    # Iterate over all modules, and load doctests from them
    for _loader, name, _ispkg in pkgutil.walk_packages(
        pdfimpose.__path__, prefix="pdfimpose."
    ):
        tests.addTests(doctest.DocTestSuite(importlib.import_module(name)))
    return tests
