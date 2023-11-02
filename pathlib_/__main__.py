#!python
'''A reimplementation of the python standard library's pathlib.
The original pathlib module seems to revolve around the idea that the path is a string, and then it can't decide if the paths are inmutable or not. This module works with a different paradigm: a path is a sequence of individual components divided by a "separator" and such sequence is inmutable.

This module also tries to avoid assumptions about paths: people can come up with all kind of ideas of how a path would look like in system X, this module tries to avoid the dichotomy of POSIX or Windows.

This is the executable script
'''

import simplifiedapp

from . import *

simplifiedapp.main()
