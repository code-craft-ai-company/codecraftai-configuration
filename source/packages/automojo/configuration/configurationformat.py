"""
.. module:: configurationformat
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Enumeration defining configuration formats supported by the foundation.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from enum import Enum

class ConfigurationFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"
