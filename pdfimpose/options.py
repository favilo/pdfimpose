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

"""Manage options"""

import argparse
import textwrap

from pdfimpose import VERSION

def commandline_parser():
    """Return a command line parser."""

    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
            TODO
            """),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""
            TODO
            """),
        )

    parser.add_argument(
        '--version',
        help='Show version',
        action='version',
        version='%(prog)s ' + VERSION
        )

    parser.add_argument(
        'file',
        metavar="FILE",
        help='PDF file to process',
        nargs=1,
        type=str,
        )

    parser.add_argument(
        '--output', '-o',
        help=(
            'Destination file. Default is "-impose" appended to first source file.'
            ),
        type=str,
        )

    parser.add_argument(
        '--interactive', '-i',
        help='Ask before overwriting destination file if it exists.',
        default=False,
        action='store_true',
        )

    # TODO

    return parser

def destination_name(output, source):
    """Return the name of the destination file.

    :param str output: Filename, given in command line options. May be
        ``None`` if it was not provided.
    :param str source: Name of the first source file.
    """
    if output is None:
        return "{}-impose.pdf".format(".".join(source.split('.')[:-1]))
    return output

def process_options(argv):
    """Make some more checks on options."""
    processed = {}
    options = commandline_parser().parse_args(argv)

    return processed
