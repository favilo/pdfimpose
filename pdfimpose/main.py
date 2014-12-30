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

"""Main function for the command."""

import PyPDF2
import logging
import os
import sys

from pdfimpose import errors, options, imposition

LOGGER = logging.getLogger(__name__)

def callback(x, m):
    print("{}/{}".format(x, m)) # TODO

def main():
    """Main function"""
    arguments = options.process_options(sys.argv[1:])

    try:
        matrix = imposition.imposition_matrix(
                arguments['fold'],
                arguments['bind'],
                )
        print(matrix)
        output = imposition.impose(matrix, arguments['file'], arguments['last'], callback)
        output.write(arguments['output'])
    except KeyboardInterrupt:
        print()
        sys.exit(1)
    except errors.PdfImposeError as error:
        LOGGER.error(error)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
