# Copyright 2011-2021 Louis Paternault
#
# Pdfimpose is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pdfimpose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with pdfimpose.  If not, see <http://www.gnu.org/licenses/>.

"""Parse arguments for the schema "perfect"."""

import itertools
import logging
import math
import sys

import papersize

from . import __doc__ as DESCRIPTION
from . import impose
from .. import common as schema
from ... import pdf
from ... import UserError


def ispowerof2(number):
    """Return True iff the number is a power of two."""
    # Is there a cleaner way?
    return round(math.log2(number)) == math.log2(number)


def signature2folds(width, height):
    """Convert a signature into a list of folds."""
    if width > height:
        alternator = itertools.cycle("hv")
    else:
        alternator = itertools.cycle("vh")

    folds = ""
    while width * height != 1:
        fold = next(alternator)
        folds += fold
        if fold == "h":
            width /= 2
        else:
            height /= 2

    return folds


def any2folds(signature, outputsize, *, inputsize):
    """Convert signature or outputsize to a list of folds."""
    if signature is None and outputsize is None:
        outputsize = papersize.parse_papersize("A4")
    if signature is not None:
        if not (ispowerof2(signature[0]) and ispowerof2(signature[1])):
            raise UserError("Both numbers of signature must be powers of two.")
        return signature2folds(*signature)
    else:
        notrotated = (
            math.floor(math.log2(float(outputsize[0]) // inputsize[0])),
            math.floor(math.log2(float(outputsize[1]) // inputsize[1])),
        )
        rotated = (
            math.floor(math.log2(float(outputsize[1]) // inputsize[0])),
            math.floor(math.log2(float(outputsize[0]) // inputsize[1])),
        )
        if rotated[0] * rotated[1] > notrotated[0] * notrotated[1]:
            return signature2folds(2 ** rotated[0], 2 ** rotated[1])
        return signature2folds(2 ** notrotated[0], 2 ** notrotated[1])


def folds2margins(outputsize, sourcesize, folds, imargin):
    """Return output margins."""
    leftright = (
        outputsize[0]
        - sourcesize[0] * 2 ** folds.count("h")
        - imargin * (2 ** folds.count("h") - 1)
    )
    topbottom = (
        outputsize[1]
        - sourcesize[1] * 2 ** folds.count("v")
        - imargin * (2 ** folds.count("v") - 1)
    )
    return schema.Margins(
        top=topbottom, bottom=topbottom, left=leftright, right=leftright
    )


def main():
    """Main function"""

    parser = schema.ArgumentParser(
        subcommand="perfect",
        options=["omargin", "imargin", "mark", "signature", "format", "last", "bind"],
        description=DESCRIPTION,
    )

    try:
        args = parser.parse_args()

        args.files = pdf.Reader(args.files)
        if args.bind in ("top", "bottom"):
            sourcesize = (args.files.size[1], args.files.size[0])
        else:
            sourcesize = (args.files.size[0], args.files.size[1])

        # Compute folds (from signature and format), and remove signature and format
        args.folds = any2folds(args.signature, args.format, inputsize=sourcesize)
        del args.signature
        if args.format is not None and args.imargin == 0:
            args.omargin = folds2margins(
                args.format, args.files.size, args.folds, args.imargin
            )
        del args.format

        return impose(**vars(args))
    except UserError as usererror:
        logging.error(usererror)
        sys.exit(1)


if __name__ == "__main__":
    main()
