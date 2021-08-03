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

import importlib
import pathlib

import xdg

from .. import UserError

BASENAMES = ("pdfimpose.cfg", ".pdfimpose.cfg")


def confignames():
    """Iterate over all the possible names of the configuration file."""
    # Names from current directory
    for base in BASENAMES:
        yield pathlib.Path(base)

    # Names from parent directories
    folder = pathlib.Path.cwd().resolve()
    while folder.parent != folder:
        folder = folder.parent
        for base in BASENAMES:
            yield folder / base

    # Configuration directory
    for base in BASENAMES:
        yield xdg.xdg_config_home() / base

    # Home directory
    for base in BASENAMES:
        yield pathlib.Path.home() / base

    # OS configuration directory
    for configdir in xdg.xdg_config_dirs():
        for base in BASENAMES:
            yield configdir / base


def find_config():
    """Return the name of the configuration file."""
    for name in confignames():
        if name.exists() and name.is_file():
            return name
    raise UserError("No configuration file found.")


def apply(sources, output, schema, config):
    """Convert data found in the configuration file into a command line, and run it."""
    main = importlib.import_module(f"pdfimpose.schema.{schema}.__main__")

    args = []
    for key, value in config.items():
        args.append(f"--{key}")
        args.append(value)
    if output is not None:
        args.extend(("--output", str(output)))
    for source in sources:
        args.append(str(source))
    return main.main(args)
