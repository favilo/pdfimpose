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

"""Command line"""

import sys
import textwrap

import argdispatch

from . import VERSION, apply, schema


class _HelpSpaces(argdispatch.Action):
    def __call__(self, *args, **kwargs):
        # pylint: disable=line-too-long
        print(
            textwrap.dedent(
                """\
        # Help about spaces

        - omargin (margin on output files): Your printer is not perfect, and probably cannot print on the very edge of the sheet of paper. You might need to add some margin, so that everything is printed.
        - imargin (margin on input files): Your scissors are not perfect. You might need to add some margin, so that you can cut exactly between two (input) pages.
        - creep: Your paper is not perfect. When folded, the inner pages will go farther than the outer pages. Use creep to fix this.

        You might want to set omargin as half of imargin, so that your printed sheets can be folded exactly in half.
        """
            )
        )
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
