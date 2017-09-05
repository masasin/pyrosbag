# -*- coding: utf-8 -*-
"""
Note that, in order to access the data within the bag file, the
``rosbag_python`` package is extremely convenient. It is available on PyPI.

"""
from .pyrosbag import (
    BagError,
    MissingBagError,
    BagNotRunningError,
    Bag,
    BagPlayer,
)

__author__ = """Jean Nassar"""
__email__ = 'jeannassar5@gmail.com'
__version__ = '0.1.3'
