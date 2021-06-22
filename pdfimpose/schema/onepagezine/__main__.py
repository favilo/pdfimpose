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

"""Parse arguments for the schema "one-page zine"."""

import logging
import sys

from . import __doc__ as DESCRIPTION
from . import impose
from .. import common as schema
from ... import UserError


def main():
    """Main function"""

    parser = schema.ArgumentParser(
        subcommand="onepagezine",
        options=["imargin", "omargin", "mark", "last", "bind"],
        description=DESCRIPTION,
        epilog="This command only perform imposition of the front of your fanzine. It is your job to print the poster on the back.",
    )

    try:
        args = parser.parse_args()

        return impose(**vars(args))
    except UserError as error:
        logging.error(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
