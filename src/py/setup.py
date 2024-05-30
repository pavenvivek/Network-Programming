#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
from setuptools import setup

version = "0.1"

sys.path.append(".")
if sys.version_info[0] < 3: 
    sys.stderr.write("------------------------------\n")
    sys.stderr.write("Must use python 3.0 or greater\n")
    sys.stderr.write("Found python version:\n")
    sys.stderr.write(sys.version)
    sys.stderr.write("\nInstallation aborted\n")
    sys.stderr.write("------------------------------\n")
    sys.exit()

setup(
    name = "netster",
    version = version,
    author = "SICE Networks",
    author_email="sice-networks-l@list.indiana.edu",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    packages = [],
    install_requires=[
        "setuptools",
    ],
    entry_points = {
        'console_scripts': [
            'netster = netster:main'
        ]
    },
)
