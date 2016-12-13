"""
Module: settings.py
Initialises app and columng configurations and global variables

Author: Daniel Harris
Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 13/12/2016

External dependencies: PyYAML
"""

import yaml

__author__ = 'Daniel Harris'
__date__ = '12 December 2016'
__email__ = 'daniel.harris@dpi.nsw.gov.au'
__status__ = 'Development'
__version__ = '1.0.0'


# Set up global configurations
app_config = yaml.load(open('config/app_config.yaml').read())
column_config = yaml.load(open('config/column_config.yaml').read())
station_list = yaml.load(open('config/station_list.yaml').read())

# Global variable for frozen columns
FROZEN_COLUMNS = 3