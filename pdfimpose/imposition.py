#!/usr/bin/env python3

# Copyright Louis Paternault 2011-2014
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 1

"""Imposition utilities."""

_HORIZONTAL = True
_VERTICAL = False

class VH:
    # TODO Make it an enum type

    def __init__(self, value):

        self.value = None
        if isinstance(value, str):
            if value.lower() == 'h':
                self.value = _HORIZONTAL
            if value.lower() == 'v':
                self.value = _VERTICAL
        if self.value is None:
            raise ValueError()

    def __eq__(self, other):
        return self.value == other.value

    def __str__(self):
        if self.value == _HORIZONTAL:
            return "H"
        else:
            return "V"

    def __repr__(self):
        return "{}({})".format(
                self.__class__.__name__,
                str(self),
                )

HORIZONTAL = VH('h')
VERTICAL = VH('v')

class Orientation:
    """Two dimensions orientation"""
    # TODO Make it an enum type
    angle = 0
    STR = {
        0: "E",
        90: "N",
        180: "W",
        270: "S",
        }

    def __init__(self, angle):
        self.angle = angle % 360
        if self.angle not in [0, 90, 180, 270]:
            raise ValueError()

    def __str__(self):
        return self.STR[self.angle]

    def symmetry(self, fold):
        """Return the symmetrical orientation.

        :param bool fold: Orientation of fold.
        """
        if fold == VERTICAL:
            return Orientation(-self.angle)
        else:
            return Orientation(180 - self.angle)


EAST = Orientation(0)
NORTH = Orientation(90)
WEST = Orientation(180)
SOUTH = Orientation(270)

class Coordinates:
    """Two-dimensions coordinates."""
    x = 0
    y = 0

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Coordinates(
            self.x + other.x,
            self.y + other.y,
            )

    def __sub__(self, other):
        return Coordinates(
            self.x - other.x,
            self.y - other.y,
            )

    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    def __repr__(self):
        return "{}({}, {})".format(
            self.__class__.__name__,
            self.x,
            self.y,
            )

class ImpositionPage:
    """Page, on an imposition matrix: a page number, and an orientation."""
    def __init__(self, number, orientation):
        self.orientation = orientation
        self.number = number

    def __str__(self):
        return "{: 3}{}".format(
            self.number,
            self.orientation,
            )

    def symmetry(self, orientation, page_max):
        """Return the symmetrical page to `self`.

        :arg bool orientation: Fold orientation.
        :arg int page_max: Maximum page number.
        """
        return ImpositionPage(
            page_max - self.number,
            self.orientation.symmetry(orientation),
            )

class ImpositionMatrix:
    """Matrix of an imposition: array of numbered, oriented pages."""
    folds = []

    def __init__(self, size, bind):
        self.matrix = [
            [
                None
                for y
                in range(size.y)
                ]
            for x
            in range(2*size.x)
            ]
        if bind in ["top", "right"]:
            self.matrix[0][0] = ImpositionPage(0, NORTH)
        else: # bind in ["bottom", "left"]:
            self.matrix[-1][-1] = ImpositionPage(0, NORTH)
        self.fold(HORIZONTAL)

    @property
    def vfolds(self):
        """Return the number of vertical folds"""
        return self.folds.count(VERTICAL)

    @property
    def hfolds(self):
        """Return the number of horizontal folds"""
        return self.folds.count(HORIZONTAL)

    @property
    def size(self):
        """Return the size of the matrix, as a :class:`Coordinates`."""
        return Coordinates(
            len(self.matrix),
            len(self.matrix[0]),
            )

    def fold(self, orientation):
        """Perform a fold according to `orientation`."""
        metapage_size = Coordinates(
            self.size.x//2**self.hfolds,
            self.size.y//2**self.vfolds,
            )
        for x in range(0, self.size.x, metapage_size.x):
            for y in range(0, self.size.y, metapage_size.y):
                self._metapage_fold(
                    Coordinates(x, y),
                    metapage_size,
                    orientation,
                    )
        self.folds.append(orientation)

    def __getitem__(self, *item):
        if len(item) == 1:
            item = item[0]
            if isinstance(item, Coordinates):
                return self.matrix[item.x][item.y]
        elif len(item) == 2:
            if isinstance(item[0], int) and isinstance(item[1], int):
                return self.matrix[item[0]][item[1]]
        raise TypeError()

    def __setitem__(self, item, value):
        if len(item) == 1:
            item = item[0]
            if isinstance(item, Coordinates):
                self.matrix[item.x][item.y] = value
                return
        elif len(item) == 2:
            if isinstance(item[0], int) and isinstance(item[1], int):
                self.matrix[item[0]][item[1]] = value
                return
        raise TypeError()

    def _metapage_find_page(self, corner, size):
        """Find the actual page on a metapage.

        A metapage should contain only one actual page. Return the coorditanes
        of this page (relative to the matrix).

        :arg Coordinates corner: Coordinates of the low left corner of the
            metapage.
        :arg Coordinates size: Size of the metapage.
        """
        for coordinates in [
                corner,
                corner + Coordinates(size.x-1, 0),
                corner + Coordinates(0, size.y-1),
                corner + size - Coordinates(1, 1),
            ]:
            if self[coordinates] is not None:
                return coordinates

    def _metapage_fold(self, corner, size, orientation):
        """Fold a metapage

        :arg Coordinates corner: Low left corner of the metapage.
        :arg Coordinates size: Size of the metapage.
        :arg bool orientation: Fold orientation.
        """
        page = self._metapage_find_page(corner, size)
        if orientation == HORIZONTAL:
            self[
                2 * corner.x + size.x - page.x - 1, # Vertical symmetrical
                page.y,
                ] = self[page].symmetry(orientation, 2**(len(self.folds)+1)-1)
        else:
            self[
                page.x,
                2 * corner.y + size.y - page.y - 1, # Horizontal symmetrical
                ] = self[page].symmetry(orientation, 2**(len(self.folds)+1)-1)

    def __str__(self):
        return "\n".join([
            " ".join([
                str(page)
                for page
                in row
                ])
            for row
            in reversed(list(zip(*self.matrix)))
            ])

    @property
    def verso(self):
        # TODO
        pass

    @property
    def recto(self):
        # TODO
        pass

