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

import PyPDF2
import argparse
import math
import re
import textwrap

from pdfimpose import VERSION
from pdfimpose import imposition
from pdfimpose.imposition import Coordinates
from pdfimpose.imposition import VERTICAL, HORIZONTAL

def positive_int(text):
    try:
        if int(text) >= 0:
            return int(text)
        else:
            raise ValueError()
    except ValueError:
        raise argparse.ArgumentTypeError("Argument must be a positive integer.")

SIZE_RE = r"^(?P<number>\w+)(?P<unit>[lfs])$"

def size_type(text):
    if text is None:
        return None
    if re.compile(SIZE_RE).match(text):
        return text
    raise argparse.ArgumentTypeError(textwrap.dedent("""
        Argument must be a number, followed by 'l', 'f' or 's'.
    """))

def fold_type(text):
    if re.compile(r"^[vh]*$").match(text):
        return [
                imposition.VH(char)
                for char
                in text
                ]
    raise argparse.ArgumentTypeError(textwrap.dedent("""
        Argument must be a sequence of letters 'v' and 'h'.
        """))

def commandline_parser():
    """Return a command line parser."""

    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""
            Perform an imposition on the PDF file given in argument.
            """),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""
            # Imposition

            TODO

            # Section size

            - If option '--size' is set, then, if the argument ends with:
                - l: set the number of leaves per section (must be a power of
                  2). For instance, use '--size=4l' for 4 leaves per section.
                - f: set the number of folds. For instance, use '--size=4f' for
                  4 folds, or 16 leaves per section.
                - s: set the number of sections. For instance, use '--size=4s'
                  on a 30 pages document to get 4 sections, or 8 pages per
                  section, or 4 leaves per section (blank pages are added if
                  necessary).
            - If option '--size' is not set, but '--fold' is set, use this
              information as the number of folds.
            - Otherwise, default is '16l'.

            # How to

            ## Print

            The resulting document should be printed on both sides, binding
            left (or right).

            ## Fold

            Place the printed paper, such that you see the first page of the
            document. Then, fold it following the order you gave (TODO by
            default), always keeping the first page at sight.
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
        type=PyPDF2.PdfFileReader,
        )

    parser.add_argument(
        '--output', '-o',
        help=(
            'Destination file. Default is "-impose" appended to first source file.'
            ),
        type=str,
        )

    parser.add_argument(
        '--bind', '-b',
        help='Binding vertex.', # TODO check vocabulary
        default="top",
        choices=["top", "left", "right", "left"],
        )

    parser.add_argument(
        '--fold', '-f',
        help=textwrap.dedent("""
            Sequence of fold orientations, as letters 'v' and 'h'. If it is too
            short regarding to option "--bind", this sequence is repeated; if
            it is too long, it is truncated.
        """),
        default="",
        type=fold_type,
        )

    parser.add_argument(
        '--last', '-l',
        help=textwrap.dedent("""
            Number of pages to keep as last pages. Useful, for instance, to
            keep the back cover as a back cover.
            """),
        type=positive_int,
        default=0,
        )

    parser.add_argument(
        '--size', '-s',
        help=textwrap.dedent("""
            Size of sections. Must be a number followed by 'l', 'f' or 's'. See
            section "Section size" for more information.
        """),
        type=size_type,
        default=None,
        )

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

    for name in [
            'file',
            'last',
            'bind',
            'output',
            ]:
        processed.update(dict([(name, getattr(options, name))]))

    # TODO options.size options.fold
    processed["size"] = Coordinates(3,2)
    processed["fold"] = [imposition.VH("V"), imposition.VH("H"), imposition.VH("V"), imposition.VH("H"), imposition.VH("H")]
    #if options.size is not None:
    #    match = re.compile(SIZE_RE).match(options.size).groupdict()
    #    if match['unit'] == 's':
    #        match['number'] = math.ceil(
    #            options.file[0].numPages / (2**math.ceil(math.log2(int(match['number']))))
    #            )
    #        match['unit'] = 'l'
    #        print(match)
    #    if match['unit'] == 'l':
    #        number = math.ceil(math.log2(int(match['number'])))
    #        processed['size'] = Coordinates(
    #            number // 2,
    #            math.ceil(number/2),
    #            )
    #    else: # match['unit'] == 'f':
    #        processed['size'] = Coordinates(
    #                TODO
    #                )
    #elif options.fold:
    #    processed['size'] = Coordinates(
    #            2**options.fold.count(HORIZONTAL),
    #            2**options.fold.count(VERTICAL),
    #            )
    #else:
    #    processed['size'] = Coordinates(
    #            2**2,
    #            2**2,
    #            )
    #print(options.fold)

    # TODO fold

#- format : 
#  4l : nombre de feuilles par cahier (défaut : 16)
#  5f : nombre de pliages
#  6s : nombre de cahiers
#  défaut : si --fold : on prend le nombre de pliages
#            sinon, 16l





    return processed
