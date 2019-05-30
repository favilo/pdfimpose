#!/usr/bin/env python3

# Copyright 2014-2017 Louis Paternault
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Installateur"""

from setuptools import setup, find_packages
import codecs
import os
import sys


def readme():
    directory = os.path.dirname(os.path.join(os.getcwd(), __file__))
    with codecs.open(
        os.path.join(directory, "README.rst"),
        encoding="utf8",
        mode="r",
        errors="replace",
    ) as file:
        return file.read()


# Requirements
install_requires = ["PyPDF2", "papersize"]
if sys.version_info < (3, 4, 0):
    install_requires.append("enum34")

setup(
    name="pdfimpose",
    version="1.1.0",
    packages=find_packages(exclude=["test*"]),
    setup_requires=["hgtools"],
    install_requires=install_requires,
    include_package_data=True,
    author="Louis Paternault",
    author_email="spalax+python@gresille.org",
    description="Perform imposition of a PDF file.",
    url="https://git.framasoft.org/spalax/pdfimpose",
    project_urls={
        "Documentation": "http://pdfimpose.readthedocs.io",
        "Source": "https://framagit.org/spalax/pdfimpose",
        "Tracker": "https://framagit.org/spalax/pdfimpose/issues",
    },
    license="GPLv3 or any later version",
    test_suite="test.suite",
    entry_points={"console_scripts": ["pdfimpose = pdfimpose.__main__:main"]},
    keywords="pdf imposition print",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.7",
        "Topic :: Printing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    long_description=readme(),
    zip_safe=True,
)
