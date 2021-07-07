# Copyright 2011-2021 Louis Paternault
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
    # We enforce that the last fold is horizontal (to make sure the bind edge is correct).
    # To do so, we consider that the source page is twice as wide,
    # and we will add an "artificial" horizontal fold later in this function.
    inputsize = (2 * inputsize[0], inputsize[1])
    if signature is None and outputsize is None:
        outputsize = tuple(map(float, papersize.parse_papersize("A4")))
    if signature is not None:
        if not (ispowerof2(signature[0]) and ispowerof2(signature[1])):
            raise UserError("Both numbers of signature must be powers of two.")
        return signature2folds(*signature), outputsize
    else:
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
        notrotated = (
            math.floor(math.log2(round(outputsize[0] / inputsize[0], 6))),
            math.floor(math.log2(round(outputsize[1] / inputsize[1], 6))),
        )
        rotated = (
            math.floor(math.log2(round(outputsize[1] / inputsize[0], 6))),
            math.floor(math.log2(round(outputsize[0] / inputsize[1], 6))),
        )
        if (rotated[0] < 0 or rotated[1] < 0) and (
            notrotated[0] < 0 or notrotated[1] < 0
        ):
            raise UserError(
                "Incompatible source size, outputsize, bind edge, or signature."
            )
        if rotated[0] + rotated[1] > notrotated[0] + notrotated[1]:
            return signature2folds(2 ** (1 + rotated[0]), 2 ** rotated[1]), (
                outputsize[1],
                outputsize[0],
            )
        return signature2folds(2 ** (1 + notrotated[0]), 2 ** notrotated[1]), outputsize


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


def main(argv=None):
    """Main function"""

    parser = schema.ArgumentParser(
        subcommand="perfect",
        options=["omargin", "imargin", "mark", "signature", "format", "last", "bind"],
        description=DESCRIPTION,
    )

    try:
        args = parser.parse_args(argv)

        args.files = pdf.Reader(args.files)
        if args.bind in ("top", "bottom"):
            sourcesize = (args.files.size[1], args.files.size[0])
        else:
            sourcesize = (args.files.size[0], args.files.size[1])

        # Compute folds (from signature and format), and remove signature and format
        args.folds, args.format = any2folds(
            args.signature, args.format, inputsize=sourcesize
        )
        del args.signature
        if args.format is not None and args.imargin == 0:
            args.omargin = folds2margins(
                args.format, sourcesize, args.folds, args.imargin
            )
        del args.format
        return impose(**vars(args))
    except UserError as usererror:
        logging.error(usererror)
        sys.exit(1)


if __name__ == "__main__":
    main()
