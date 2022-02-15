# Copyright 2015-2022 Louis Paternault
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
import pkgutil
import sys

import pdfimpose


def load_tests(__loader, tests, __pattern):
    """Load tests (doctests)."""
    # Loading doctests
    tests.addTests(doctest.DocTestSuite(pdfimpose))
    for module_finder, name, __is_pkg in pkgutil.walk_packages(
        pdfimpose.__path__, prefix=f"{pdfimpose.__name__}."
    ):
        if name in sys.modules:
            module = sys.modules[name]
        else:
            try:
                module = module_finder.find_spec(name).loader.load_module()
            except ImportError:
                continue
        try:
            tests.addTests(doctest.DocTestSuite(module))
        except ValueError:
            # No docstring, or no doctests in the docstrings
            pass

    return tests
