#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright Louis Paternault 2011-2015
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 1

"""Manage options"""

import argparse
import logging
import math
import re
import textwrap

from pdfimpose import Direction, HORIZONTAL, VERTICAL
from pdfimpose import VERSION
from pdfimpose import errors
import pdfimpose

LOGGER = logging.getLogger(pdfimpose.__name__)

def _positive_int(text):
    """Return ``True`` iff ``text`` represents a positive integer."""
    try:
        if int(text) >= 0:
            return int(text)
        else:
            raise ValueError()
    except ValueError:
        raise argparse.ArgumentTypeError("Argument must be a positive integer.")

SIZE_RE = r"^(?P<width>\w+)x(?P<height>\w+)$"

def _is_power_of_two(number):
    """Return ``True`` iff `number` is a power of two."""
    return math.trunc(math.log2(int(number))) == math.log2(int(number))

BIND = [
    'top',
    'bottom',
    'left',
    'right',
    ]

def _bind_type(text):
    """Check type of '--bind' argument."""
    if not text:
        raise argparse.ArgumentTypeError(
            """Non-empty argument required."""
            )
    for bind in BIND:
        if bind.startswith(text):
            return bind
    raise argparse.ArgumentTypeError(
        """Argument must be one of {} (or one of their prefixes).""".format(
            ",".join(["'{}'".format(bind) for bind in BIND])
            )
        )


def _size_type(text):
    """Check type of '--size' argument."""
    if text is None:
        return None
    if re.compile(SIZE_RE).match(text):
        match = re.compile(SIZE_RE).match(text).groupdict()
        if _is_power_of_two(match['width']) and _is_power_of_two(match['height']):
            if int(match['width']) != 1 or int(match['height']) != 1:
                return [match['width'], match['height']]
    raise argparse.ArgumentTypeError(textwrap.dedent("""
        Argument must be "WIDTHxHEIGHT", where both WIDTH and HEIGHT are powers of two, and at least one of them is not 1.
    """))

def _fold_type(text):
    """Check type of '--fold' argument."""
    if re.compile(r"^[vh]*$").match(text):
        return [
            Direction.from_char(char)
            for char
            in text
            ]
    raise argparse.ArgumentTypeError(textwrap.dedent("""
        Argument must be a sequence of letters 'v' and 'h'.
        """))

def _process_size_fold_bind(options):
    """Process arguments '--size', '--fold', '--bind'."""
    # pylint: disable=too-many-branches
    processed = {}

    if options.size:
        width, height = [int(num) for num in options.size]
        if (
                options.bind in ["left", "right"] and width == 1
            ) or (
                options.bind in ["top", "bottom"] and height == 1
            ):
            raise errors.IncompatibleBindSize(options.bind, options.size)
        if options.bind is None:
            if width >= height:
                processed["bind"] = "left"
            else:
                processed["bind"] = "top"
        else:
            processed["bind"] = options.bind

        processed["fold"] = []
        if processed["bind"] in ["left", "right"]:
            processed["fold"].append(HORIZONTAL)
            width //= 2
        else:
            processed["fold"].append(VERTICAL)
            height //= 2
        while width != 1 or height != 1:
            if width > height:
                processed["fold"].append(HORIZONTAL)
                width //= 2
            else:
                processed["fold"].append(VERTICAL)
                height //= 2
        processed["fold"].reverse()
    elif options.fold:
        processed["fold"] = options.fold
        if options.bind is None:
            if processed["fold"][-1] == VERTICAL:
                processed["bind"] = "top"
            else:
                processed["bind"] = "right"
        else:
            processed["bind"] = options.bind
            if (
                    processed["fold"][-1] == VERTICAL
                    and options.bind not in ["top", "bottom"]
                ) or (
                    processed["fold"][-1] == HORIZONTAL
                    and options.bind not in ["left", "right"]
                ):
                raise errors.IncompatibleBindFold(options.bind, options.fold)
    else:
        if options.bind is None:
            options.bind = "left"
        processed["bind"] = options.bind
        if processed["bind"] in ["top", "bottom"]:
            processed["fold"] = [HORIZONTAL, VERTICAL, HORIZONTAL, VERTICAL]
        else:
            processed["fold"] = [VERTICAL, HORIZONTAL, VERTICAL, HORIZONTAL]

    return processed

def _process_output(text, source):
    """Process the `output` argument."""
    if text is None:
        text = "{}-impose.pdf".format(".".join(source.split('.')[:-1]))
    return open(text, 'wb')

def commandline_parser():
    """Return a command line parser."""

    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
            Perform an imposition on the PDF file given in argument.
            """),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""
            # Imposition

            Imposition consists in the arrangement of the printed product’s
            pages on the printer’s sheet, in order to obtain faster printing,
            simplify binding and reduce paper waste (source:
            http://en.wikipedia.org/wiki/Imposition).

            # How to

            ## Print

            The resulting document should be printed on both sides, binding
            left (or right).

            ## Fold

            Fold the document such that each page is placed against the
            previous one, beginning with the first page. More information on
            http://pdfimpose.readthedocs.org/en/latest/folding/
            """),
        )

    parser.add_argument(
        '--version',
        help='Show version',
        action='version',
        version='%(prog)s ' + VERSION
        )

    parser.add_argument(
        '-v', '--verbose',
        help='Verbose mode.',
        action='store_true',
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
        metavar='FILE',
        help=(
            'Destination file. Default is "-impose" appended to first source file.'
            ),
        type=str,
        )

    parser.add_argument(
        '--bind', '-b',
        help=textwrap.dedent("""
            Binding edge. Default is left or top, depending on arguments
            '--fold' and '--size'. If neither '--size' nor '--fold' is set,
            default is 'left'. Note that any prefix of accepted choices is also
            accepted.
            """),
        metavar="{{{}}}".format(",".join(BIND)),
        default=None,
        type=_bind_type,
        )

    parser.add_argument(
        '--last', '-l',
        metavar='N',
        help=textwrap.dedent("""
            Number of pages to keep as last pages. Useful, for instance, to
            keep the back cover as a back cover.
            """),
        type=_positive_int,
        default=0,
        )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        '--fold', '-f',
        help=textwrap.dedent("""
            Sequence of fold orientations, as letters 'v' and 'h'. Default is
            alternating, as much as possible, horizontal and vertical folds, to
            match the argument of '--size'.
        """),
        default=None,
        metavar='SEQUENCE',
        type=_fold_type,
        )

    group.add_argument(
        '--size', '-s',
        metavar="WIDTHxHEIGHT",
        help=textwrap.dedent("""
            Size of sections. Both width and height must be powers of two (1,
            2, 4, 8, 16...). If neither this nor '--fold' is set, '--size' is
            '4x4'.
        """),
        type=_size_type,
        default=None,
        )

    return parser

def process_options(argv):
    """Make some more checks on options."""

    processed = {}
    options = commandline_parser().parse_args(argv)

    if options.verbose:
        LOGGER.setLevel(logging.INFO)

    try:
        processed['last'] = options.last
        processed['output'] = _process_output(options.output, options.file[0])
        processed["file"] = options.file[0]

        processed.update(_process_size_fold_bind(options))
    except FileNotFoundError as error:
        raise errors.ArgumentError(str(error))

    return processed
