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

import logging
import sys

from pdfimpose import errors, options, imposition

LOGGER = logging.getLogger(__name__)

def print_progress(progress, maximum):
    """Display progress to user"""
    LOGGER.info("{}/{}".format(progress, maximum))

def main():
    """Main function"""
    try:
        arguments = options.process_options(sys.argv[1:])

        imposition.impose(
            imposition.imposition_matrix(
                arguments['fold'],
                arguments['bind'],
                ),
            arguments['file'],
            arguments['last'],
            print_progress,
            ).write(arguments['output'])
    except KeyboardInterrupt:
        print()
        sys.exit(1)
    except errors.PdfImposeError as error:
        LOGGER.error(error)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
