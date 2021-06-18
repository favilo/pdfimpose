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

"""A one-page fanzine, with a poster on the back."""

import collections.abc
import dataclasses
import decimal

from .. import common


@dataclasses.dataclass
class Impositor(common.Impositor):

    imargin: float = 0
    omargin: float = 0
    last: int = 0
    mark: list[str] = dataclasses.field(default_factory=list)
    creep: collections.abc.Callable[[int], float] = lambda x: 0

    def __post_init__(self):
        print(self)
        print("TODO post_init")

    def impose(self, files, output):
        print(f"TODO impose {files} {output}")


def impose(files, output, *, creep=0, imargin=0, omargin=0, last=0, mark=None):
    if mark is None:
        mark = []
    Impositor(
        imargin=imargin, omargin=omargin, creep=creep, last=last, mark=mark
    ).impose(files, output)
