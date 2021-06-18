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

import argparse
import decimal
import pathlib
import os
import re

import papersize


RE_CREEP = re.compile(
    r"(?P<slope>-?\d+(.\d+)?)x(?P<yintercept>[+-]\d+(.\d+)?)?(?P<unit>[^\d]+)?"
)


def _type_creep(text):
    """Turn a linear function (as a string) into a linear Python function.

    >>> _type_creep("-2x+3")(5)
    Decimal('-7')
    >>> _type_creep("2.5x")(2)
    Decimal('5.0')
    >>> _type_creep("7")(9)
    Decimal('7')
    >>> _type_creep("2x-5pc")(3)
    Decimal('12')
    """
    if "x" in text:
        if match := RE_CREEP.match(text):
            try:
                groups = match.groupdict()
                slope = decimal.Decimal(groups["slope"])
                if groups["yintercept"]:
                    yintercept = decimal.Decimal(groups["yintercept"])
                else:
                    yintercept = 0
                if groups["unit"]:
                    unit = papersize.UNITS[groups["unit"]]
                else:
                    unit = 1
                return lambda x: (slope * x + yintercept) * unit
            except KeyError:
                raise argparse.ArgumentTypeError(
                    "Invalid creep function (must be a linear function, with an optional unit, e.g. '2.3x-1mm')."
                )
    return lambda x: papersize.parse_length(text)


def _type_positive_int(text):
    """Return ``int(text)`` iff ``text`` represents a positive integer."""
    try:
        if int(text) >= 0:
            return int(text)
        else:
            raise ValueError()
    except ValueError:
        raise argparse.ArgumentTypeError("Argument must be a positive integer.")


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, subcommand, options=None, **kwargs):
        if options is None:
            options = []

        if "prog" not in kwargs:
            kwargs["prog"] = f"pdfimpose {subcommand}"

        super().__init__(**kwargs)

        self.add_argument(
            "files", metavar="FILEs", help="PDF files to process", nargs="+", type=str
        )

        self.add_argument(
            "--output",
            "-o",
            metavar="FILE",
            help='Destination file. Default is "-impose" appended to first source file.',
            type=str,
        )

        if "imargin" in options:
            self.add_argument(
                "--imargin",
                "-m",
                help="Set margin added to input pages when imposed on the output page.",
                default=0,
                type=papersize.parse_length,
            )

        if "omargin" in options:
            self.add_argument(
                "--omargin",
                "-M",
                help="Set margin added to output pages.",
                default=0,
                type=papersize.parse_length,
            )

        if "creep" in options:
            self.add_argument(
                "--creep",
                "-c",
                help="Set creep (space added at each fold). This is a linear fonction of 'x', the number of folds.",
                type=_type_creep,
                default=lambda x: 0,
            )

        if "last" in options:
            self.add_argument(
                "--last",
                "-l",
                help="Number of pages to keep as last pages. Useful to keep the back cover as a back cover.",
                type=_type_positive_int,
                default=0,
            )

        if "mark" in options:
            self.add_argument(
                "--mark",
                "-k",
                help="List of marks to add (crop or bind). Can be given multiple times.",
                choices=["bind", "crop"],
                action="append",
                default=[],
            )

    def parse_args(self, *args, **kwargs):
        args = super().parse_args(*args, **kwargs)

        for i, path in enumerate(args.files):
            if (not os.path.exists(path)) and os.path.exists(f"{path}.pdf"):
                args.files[i] = f"{path}.pdf"

        if args.output is None:
            source = pathlib.Path(args.files[0])
            args.output = "{}-impose{}".format(
                source.parent / source.stem, source.suffix
            )

        return args


class Impositor:
    pass
