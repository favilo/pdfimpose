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
import pathlib
import os

import papersize


def _creep_function(text):
    # TODO: Make it a function
    return lambda x: papersize.parse_length(text)


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
                type=_creep_function,
                default=lambda x: 0,
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
