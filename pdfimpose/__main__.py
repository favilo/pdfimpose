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

"""Command line"""

import sys

import argdispatch

from . import VERSION
from . import schema
from . import apply


class _HelpSpaces(argdispatch.Action):
    def __call__(self, *args, **kwargs):
        print("TODO")
        sys.exit(0)


def main():
    """Main function"""

    parser = argdispatch.ArgumentParser(
        prog="pdfimpose",
        description="Perform an imposition on the PDF file given in argument.",
    )

    parser.add_argument(
        "--version",
        help="Show version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    parser.add_argument(
        "--help-spaces",
        help="Show help about spaces (margins, creep, etc.).",
        action=_HelpSpaces,
        nargs=0,
    )

    subparser = parser.add_subparsers()
    subparser.add_submodules(schema)
    subparser.add_module(apply, command="apply")
    subparser.required = True
    subparser.dest = "schema"

    parser.parse_args()


if __name__ == "__main__":
    main()
