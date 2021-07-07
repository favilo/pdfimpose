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

import os
import unittest

import pdfimpose


def suite():
    """Return a :class:`TestSuite` object, testing all module :mod:`pdfimpose`."""
    return unittest.defaultTestLoader.discover(
        os.path.abspath(os.path.join(pdfimpose.__path__[0], ".."))
    )


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())
