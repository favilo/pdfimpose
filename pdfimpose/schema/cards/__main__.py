# Copyright 2011-2024 Louis Paternault
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

from ... import UserError
from .. import ArgumentParser
from . import __doc__ as DESCRIPTION
from . import impose


def main(argv=None):
    """Main function"""

    parser = ArgumentParser(
        subcommand="cards",
        options=["omargin", "imargin", "mark-crop", "cutsignature", "format", "back"],
        description=DESCRIPTION,
    )

    try:
        return impose(**vars(parser.parse_args(argv)))
    except UserError as usererror:
        logging.error(usererror)
        sys.exit(1)


if __name__ == "__main__":
    main()
