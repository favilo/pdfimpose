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

"""Tests"""

import unittest

from pdfimpose import ImpositionMatrix, ImpositionPage
from pdfimpose import NORTH, SOUTH, HORIZONTAL, VERTICAL

class ImpositionMatrixTest(unittest.TestCase):
    """Tests of imposition matrix"""

    def test_no_fold(self):
        """No fold"""
        self.assertListEqual(
            ImpositionMatrix([], "left").as_list(),
            [[ImpositionPage(1, NORTH)], [ImpositionPage(0, NORTH)]],
            )

    def test_horizontal(self):
        """A single horizontal fold"""
        self.assertListEqual(
            ImpositionMatrix([HORIZONTAL], "left").as_list(),
            [
                [ImpositionPage(1, NORTH)],
                [ImpositionPage(2, NORTH)],
                [ImpositionPage(3, NORTH)],
                [ImpositionPage(0, NORTH)],
                ],
            )

    def test_vertical(self):
        """A single vertical fold"""
        self.assertListEqual(
            ImpositionMatrix([VERTICAL], "left").as_list(),
            [
                [ImpositionPage(2, SOUTH), ImpositionPage(1, NORTH)],
                [ImpositionPage(3, SOUTH), ImpositionPage(0, NORTH)],
                ],
            )

    def test_mixed(self):
        """Mixed horizontal and vertical folds."""
        self.assertListEqual(
            ImpositionMatrix([HORIZONTAL, VERTICAL], "left").as_list(),
            [
                [ImpositionPage(6, SOUTH), ImpositionPage(1, NORTH)],
                [ImpositionPage(5, SOUTH), ImpositionPage(2, NORTH)],
                [ImpositionPage(4, SOUTH), ImpositionPage(3, NORTH)],
                [ImpositionPage(7, SOUTH), ImpositionPage(0, NORTH)],
                ],
            )

    def test_mixed_bind(self):
        """Mixed horizontal and vertical folds, with a different bind edge."""
        self.assertListEqual(
            ImpositionMatrix([HORIZONTAL, VERTICAL], "top").as_list(),
            [
                [ImpositionPage(0, NORTH), ImpositionPage(7, NORTH)],
                [ImpositionPage(3, SOUTH), ImpositionPage(4, SOUTH)],
                [ImpositionPage(2, NORTH), ImpositionPage(5, NORTH)],
                [ImpositionPage(1, SOUTH), ImpositionPage(6, SOUTH)],
                ],
            )
