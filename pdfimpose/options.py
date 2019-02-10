# -*- coding: utf-8 -*-

# Copyright Louis Paternault 2011-2019
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

import papersize

from pdfimpose import Direction, HORIZONTAL, VERTICAL
from pdfimpose import VERSION
from pdfimpose.errors import PdfImposeError
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
    return math.trunc(math.log(int(number), 2)) == math.log(int(number), 2)


BIND = ["top", "bottom", "left", "right"]


def _bind_type(text):
    """Check type of '--bind' argument."""
    if not text:
        raise argparse.ArgumentTypeError("""Non-empty argument required.""")
    for bind in BIND:
        if bind.startswith(text):
            return bind
    raise argparse.ArgumentTypeError(
        """Argument must be one of {} (or one of their prefixes).""".format(
            ",".join(["'{}'".format(bind) for bind in BIND])
        )
    )


def _papersize(text):
    """Parse the argument, and return the dimensions."""
    try:
        return papersize.parse_papersize(text)
    except papersize.CouldNotParse as error:
        raise argparse.ArgumentTypeError(error)


def _size_type(text):
    """Check type of '--size' argument."""
    if text is None:
        return None
    if re.compile(SIZE_RE).match(text):
        match = re.compile(SIZE_RE).match(text).groupdict()
        if _is_power_of_two(match["width"]) and _is_power_of_two(match["height"]):
            if int(match["width"]) != 1 or int(match["height"]) != 1:
                return [match["width"], match["height"]]
    raise argparse.ArgumentTypeError(
        """Argument must be "WIDTHxHEIGHT", where both WIDTH and HEIGHT are powers of two, and at least one of them is not 1."""  # pylint: disable=line-too-long
    )


def _fold_type(text):
    """Check type of '--fold' argument."""
    if re.compile(r"^[vh]*$").match(text):
        return [Direction.from_char(char) for char in text]
    raise argparse.ArgumentTypeError(
        textwrap.dedent(
            """
        Argument must be a sequence of letters 'v' and 'h'.
        """
        )
    )


def _process_size_fold_bind(options, pages):
    """Process arguments '--size', '--fold', '--bind'."""
    # pylint: disable=too-many-branches, too-many-statements
    processed = {}

    if (
        options.fold is None
        and options.size is None
        and options.sheets is None
        and options.paper is None
    ):
        options.paper = papersize.parse_papersize("A4")
    if options.fold:
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
                raise PdfImposeError(
                    "Cannot bind on '{}' with fold '{}'".format(
                        options.bind, "".join([str(item) for item in options.fold])
                    )
                )

    else:
        if options.size is not None:
            horizontal, vertical = [int(math.log(int(num), 2)) for num in options.size]
            if (options.bind in ["left", "right"] and horizontal == 0) or (
                options.bind in ["top", "bottom"] and vertical == 0
            ):
                raise PdfImposeError(
                    "Cannot bind on '{}' with size '{}x{}'".format(
                        options.bind, options.size[0], options.size[1]
                    )
                )
        elif options.sheets is not None:
            try:
                source = pdfimpose.pdf_page_size(pages[0])
            except IndexError:
                raise PdfImposeError("Error: Not a single page to process.")
            fold_number = max(
                0, math.ceil(math.log(len(pages) / (2 * options.sheets), 2))
            )
            horizontal = fold_number // 2
            vertical = fold_number - horizontal
            if source[0] < source[1]:
                horizontal, vertical = vertical, horizontal
        else:  # options.paper is not None:
            dest = options.paper
            try:
                source = pdfimpose.pdf_page_size(pages[0])
            except IndexError:
                raise PdfImposeError("Error: Not a single page to process.")

            try:
                # We are rounding the ratio of (dest/source) to
                # 0.000001, so that 0.999999 is rounded to 1:
                # in some cases, we *should* get 1, but due to
                # floating point arithmetic, we get 0.999999
                # instead. We want it to be 1.
                #
                # Let's compute the error: how long is such an error?
                #
                # log2(ratio)=10^(-6) => ratio=2^(10^(-6))=1.000000693
                #
                # The ratio error is about 1.000000693.
                # What does this represent on the big side of an A4 sheet of paper?
                #
                # 0.000000693×29.7cm = 0.000020582cm = 0.20582 nm
                #
                # We are talking about a 0.2 nanometers error. We do not care.
                horizontal, vertical = max(
                    (
                        # The more folds, the better
                        sum(candidate),
                        # We want the number of horizontal and vertical folds as close as possible
                        -abs(candidate[0] - candidate[1]),
                        candidate,
                    )
                    for candidate in (
                        (  # Not rotated
                            max(
                                -1,
                                math.floor(round(math.log(dest[0] / source[0], 2), 6)),
                            ),
                            max(
                                -1,
                                math.floor(round(math.log(dest[1] / source[1], 2), 6)),
                            ),
                        ),
                        (  # Rotated
                            max(
                                -1,
                                math.floor(round(math.log(dest[1] / source[0], 2), 6)),
                            ),
                            max(
                                -1,
                                math.floor(round(math.log(dest[0] / source[1], 2), 6)),
                            ),
                        ),
                    )
                    if -1 not in candidate  # Source page is too big for paper format
                )[2]
            except ValueError:
                raise PdfImposeError(
                    "Error: Source file is too big for requested paper format."
                )

        if options.bind is None:
            if horizontal >= vertical:
                processed["bind"] = "left"
            else:
                processed["bind"] = "top"
        else:
            processed["bind"] = options.bind

        processed["fold"] = []

        # First fold (corresponding to two-side printing)
        if horizontal > 0 and vertical > 0:
            if processed["bind"] in ["left", "right"]:
                processed["fold"].append(HORIZONTAL)
                horizontal -= 1
            else:
                processed["fold"].append(VERTICAL)
                vertical -= 1

        # Alternating folds
        if horizontal > 0 and vertical > 0:
            alternate = min(horizontal, vertical)
            if processed["fold"][0] == HORIZONTAL:
                processed["fold"].extend([VERTICAL, HORIZONTAL] * alternate)
            else:
                processed["fold"].extend([HORIZONTAL, VERTICAL] * alternate)
            horizontal -= alternate
            vertical -= alternate

        # Remaning, identical, folds. One of vertical or horizontal is zero.
        processed["fold"].extend([HORIZONTAL] * horizontal)
        processed["fold"].extend([VERTICAL] * vertical)

        processed["fold"].reverse()

    return processed


def _process_output(outname, source):
    """Process the `output` argument."""
    if outname is None:
        outname = "{}-impose.pdf".format(".".join(source[0].split(".")[:-1]))
    return outname


def commandline_parser():
    """Return a command line parser."""

    parser = argparse.ArgumentParser(
        prog="pdfimpose",
        description=textwrap.dedent(
            """
            Perform an imposition on the PDF file given in argument.
            """
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent(
            # pylint: disable=line-too-long
            """
            # Layout

            The [--fold FOLD | --size WIDTHxHEIGHT | --paper PAPER | --sheets SHEETS] are used to define the layout of the output pages. They are exclusive.

            Let's say I have a PDF file of 32 A6 pages, that I want to impose on A3 paper.
            The resulting file is to be printed on two A3 sheets of paper, the first one being:

            - Recto:

                2  | 15  | 14  | 3
                7* | 10* | 11* | 6*

            - Verso:

                4  | 13  | 16 | 1
                5* | 12* | 9* | 8*

            To generate this, I could use any of those commands.

            - `pdfimpose --fold hvh file.pdf` means "Impose 'file.pdf' so that I will have to fold the resulting paper sheets horizontally, then vertically, then horizontally again."
            - `pdfimpose --size 4x2 file.pdf` means "Impose 'file.pdf' so that on the resulting paper sheets, I will have 4 columns and 2 rows of source pages."
            - `pdfimpose --paper A3 file.pdf` means "Impose 'file.pdf' so that it can be printed on A3 paper."
            - `pdfimpose --sheets 2 file.pdf` means "Impose 'file.pdf' so that it can be printed on two paper sheets."

            # Imposition

            Imposition consists in the arrangement of the printed product’s pages on the printer’s sheet, in order to obtain faster printing, simplify binding and reduce paper waste (source: http://en.wikipedia.org/wiki/Imposition).

            # How to

            ## Print

            The resulting document should be printed on both sides, binding left (or right).

            ## Fold

            Fold the document such that each page is placed against the previous one, beginning with the first page. More information on http://pdfimpose.readthedocs.io/en/latest/folding/
            """
        ),
    )

    parser.add_argument(
        "--version",
        help="Show version",
        action="version",
        version="%(prog)s " + VERSION,
    )

    parser.add_argument("-v", "--verbose", help="Verbose mode.", action="store_true")

    parser.add_argument(
        "files", metavar="FILEs", help="PDF files to process", nargs="+", type=str
    )

    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help=('Destination file. Default is "-impose" appended to first source file.'),
        type=str,
    )

    parser.add_argument(
        "--bind",
        "-b",
        help=(
            "Binding edge. Default is left or top, depending on arguments "
            "'--fold' and '--size'. Note that any prefix of accepted "
            "choices is also accepted."
        ),
        metavar="{{{}}}".format(",".join(BIND)),
        default=None,
        type=_bind_type,
    )

    parser.add_argument(
        "--last",
        "-l",
        metavar="N",
        help=(
            "Number of pages to keep as last pages. Useful, for instance, "
            "to keep the back cover as a back cover."
        ),
        type=_positive_int,
        default=0,
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--fold",
        "-f",
        help=(
            "Sequence of fold orientations, as letters 'v' (vertical) and 'h' (horizontal). "
            "See section 'Layout' below."
        ),
        default=None,
        type=_fold_type,
    )

    group.add_argument(
        "--size",
        "-s",
        metavar="WIDTHxHEIGHT",
        help=(
            "Size of destination pages (relative to source pages). Both "
            "width and height must be powers of two (1, 2, 4, 8, 16...). "
            "See section 'Layout' below."
        ),
        type=_size_type,
        default=None,
    )

    group.add_argument(
        "--paper",
        "-p",
        help=(
            """Paper format of destination pages: fold the original """
            """document so that it can be printed on this paper format. Can """
            """be either a couple of length (e.g. "21cmx29.7cm") or a named """
            """format (e.g. "letter"). """
            "See section 'Layout' below."
        ),
        type=_papersize,
        default=None,
    )

    group.add_argument(
        "--sheets",
        "-S",
        help=(
            "Number of final paper sheets: fold the original document so "
            "that it can be printed on this number of paper sheets. "
            "See section 'Layout' below."
        ),
        type=_positive_int,
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
        processed["last"] = options.last
        processed["output"] = _process_output(options.output, options.files)
        processed["pages"] = pdfimpose.PageList(options.files)

        processed.update(
            _process_size_fold_bind(options=options, pages=processed["pages"])
        )
    except FileNotFoundError as error:
        raise PdfImposeError(str(error))

    return processed
