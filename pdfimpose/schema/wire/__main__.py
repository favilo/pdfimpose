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

"""Parse arguments for the schema "wire"."""

import logging
import sys

import papersize

from . import __doc__ as DESCRIPTION
from . import impose
from .. import common as schema
from ... import pdf
from ... import UserError


def main():
    """Main function"""

    parser = schema.ArgumentParser(
        subcommand="wire",
        options=["omargin", "imargin", "mark", "last", "signature", "format"],
        description=DESCRIPTION,
    )

    try:
        args = parser.parse_args()

        # If --signature is not set, compute it from --format option
        args.files = pdf.Reader(args.files)

        if args.signature is None:
            if args.format is None:
                args.format = papersize.parse_papersize("A4")
            args.format = (float(args.format[0]), float(args.format[1]))

            args.signature, rotated = schema.compute_signature(
                args.files.size, args.format
            )
            if rotated:
                args.format = (args.format[1], args.format[0])

            if args.imargin == 0:
                args.omargin = (
                    (args.format[1] - args.files.size[1] * args.signature[1]) / 2,
                    (args.format[0] - args.files.size[0] * args.signature[0]) / 2,
                    (args.format[1] - args.files.size[1] * args.signature[1]) / 2,
                    (args.format[0] - args.files.size[0] * args.signature[0]) / 2,
                )

        del args.format

        return impose(**vars(args))
    except UserError as usererror:
        logging.error(usererror)
        sys.exit(1)


if __name__ == "__main__":
    main()
