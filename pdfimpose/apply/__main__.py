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

"""Apply a configuration file"""

import argparse
import configparser
import logging
import os
import pathlib
import shlex
import sys
import textwrap

from . import __doc__ as DESCRIPTION
from . import apply, find_config
from .. import UserError


def main():
    """Main function"""
    # pylint: disable=line-too-long, too-many-branches

    parser = argparse.ArgumentParser(
        prog="apply",
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
                # Syntax of configuration file

                The configuration file has (at least) two sectins.

                The first section is '[general]', and contains the following optional values:

                - files: the list of files to process;
                - schema: the imposition schema to use;
                - output: the output file.

                Both values can be overridden by command line arguments.

                Then, each schema has its own section, where values are transmitted as-is to the corresponding pdfimpose call. For instance, the following configuration file:

                    [general]
                    schema = perfect
                    files = foo.pdf bar.pdf

                    [perfect]
                    imargin = 1cm
                    omargin = .5cm

                is equivalent to the following command line:

                    pdfimpose perfect --imargin 1cm --omargin .5cm foo.pdf bar.pdf

                # Path of configuration file

                If not explicitely given, the configuration file is the first existing file among:

                - pdfimpose.cfg or .pdfimpose.cfg, in the current working directory;
                - the same files, in the parent directory, or grand-parent directory, or…;
                - the same files, in '~/.config';
                - the same files, in the home directory;
                - /etc/pdfimpose.cfg (depending on the operating system).

                # Extensions of arguments

                An argument with a '.cfg' extension is considered the configuration file. An argument with a '.pdf' file is considered the PDF file; and argument with any other extension, which does not exists, is appended the '.pdf' extension.

                - If neither configuration file nor pdf file are given, configuration file is searched (see above), and PDF file is read from the configuration file.

                      pdfimpose apply

                - If the configuration file is missing, but a '.pdf' file is provided, the configuration file is searched (see above). The pdf file overrides the name that might be defined inside the configuration file.

                      pdfimpose apply foo.pdf

                - If the configuration file is provided (a '.cfg' file), the path of the PDF file is read from the configuration file.

                      pdfimpose apply foo.cfg

                - If both the configuration file and PDF files are given, the PDF file overrides the one defined in the configuration file.

                      pdfimpose apply foo.cfg foo.pdf
                """
        ),
    )

    parser.add_argument(
        "--schema",
        "-s",
        help="Imposition schema to use. This overrides the one defined in the configuration file.",
    )
    parser.add_argument("CONF", help="Configuration file", default=None, nargs="?")
    parser.add_argument("PDF", help="PDF files to process", default=None, nargs="*")

    try:
        args = parser.parse_args()

        conf = list()
        pdf = list()
        for arg in [args.CONF] + args.PDF:
            if arg is None:
                continue
            if arg.endswith(".cfg"):
                conf.append(arg)
            elif arg.endswith(".pdf"):
                pdf.append(arg)
            elif os.path.exists(f"{arg}.pdf"):
                pdf.append(f"{arg}.pdf")
            else:
                raise UserError(
                    f"{arg} is neither a PDF file nor a configuration file (it should end with '.pdf' or '.cfg')."
                )

        # Open configuration file
        config = configparser.ConfigParser()
        if len(conf) == 0:
            confname = find_config()
        elif len(conf) == 1:
            confname = pathlib.Path(conf[0])
        else:
            raise UserError(
                "Too many configuration files provided: {}.".format(", ".join(conf))
            )
        with open(confname) as conffile:
            config.read_file(conffile)

        # Get list of PDF
        if not pdf:
            pdf = [
                confname.parent / basename
                for basename in shlex.split(config["general"]["files"])
            ]
            if not pdf:
                raise UserError(
                    "At least one PDF file must be provided (either as command line argument, or in the configuration file)."
                )

        # Get schema
        if args.schema is None:
            schema = config["general"]["schema"]
            if not schema:
                raise UserError(
                    "Schema must be provided, either as command line argument, or in the configuration file."
                )
        else:
            schema = args.schema

        # Get output name
        if "output" in config["general"]:
            output = confname.parent / config["general"]["output"]
        else:
            output = None

        # Get config name
        if schema in config:
            schemacfg = dict(config[schema])
        else:
            schemacfg = dict()

        apply(
            sources=pdf,
            output=output,
            schema=schema,
            config=schemacfg,
        )

    except UserError as usererror:
        logging.error(usererror)
        sys.exit(1)


if __name__ == "__main__":
    main()
