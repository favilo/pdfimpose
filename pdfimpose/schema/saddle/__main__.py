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

"""Parse arguments for the schema "saddle"."""

import logging
import sys

from . import __doc__ as DESCRIPTION
from . import impose
from .. import common as schema
from ..perfect.__main__ import any2folds, folds2margins
from ... import UserError
from ... import pdf


def main(argv=None):
    """Main function"""

    parser = schema.ArgumentParser(
        subcommand="saddle",
        options=[
            "omargin",
            "imargin",
            "mark",
            "signature",
            "format",
            "last",
            "bind",
            "creep",
        ],
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
        if (
            args.format is not None
            and args.imargin == 0
            and args.creep == schema.nocreep  # pylint: disable=comparison-with-callable
        ):
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
