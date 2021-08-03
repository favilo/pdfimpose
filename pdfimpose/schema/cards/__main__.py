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

"""Parse arguments for the schema "cards"."""

import logging
import sys

import papersize

from . import __doc__ as DESCRIPTION
from . import impose
from .. import common as schema
from ... import pdf
from ... import UserError


def format2signature(sourcesize, args):
    """Convert the --format option into a --signature option.

    Warning: This function changes the value of its argument ``args``.
    """
    if args.signature is None:
        if args.format is None:
            args.format = tuple(map(float, papersize.parse_papersize("A4")))

        args.signature, rotated = schema.compute_signature(sourcesize, args.format)
        if rotated:
            args.format = (args.format[1], args.format[0])

        if args.imargin == 0:
            args.omargin = schema.Margins(
                top=(args.format[1] - sourcesize[1] * args.signature[1]) / 2,
                bottom=(args.format[1] - sourcesize[1] * args.signature[1]) / 2,
                left=(args.format[0] - sourcesize[0] * args.signature[0]) / 2,
                right=(args.format[0] - sourcesize[0] * args.signature[0]) / 2,
            )

    del args.format


def main(argv=None):
    """Main function"""

    parser = schema.ArgumentParser(
        subcommand="cards",
        options=["omargin", "imargin", "mark", "signature", "format"],
        description=DESCRIPTION,
    )

    try:
        args = parser.parse_args(argv)

        args.files = pdf.Reader(args.files)
        format2signature(args.files.size, args)

        return impose(**vars(args))
    except UserError as usererror:
        logging.error(usererror)
        sys.exit(1)


if __name__ == "__main__":
    main()
