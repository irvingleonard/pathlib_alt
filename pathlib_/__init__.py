#!python
"""A reimplementation of the python standard library's pathlib.
The original pathlib module seems to revolve around the idea that the path is a string, and then it can't decide if the paths are immutable or not. This module works with a different paradigm: a path is a sequence of individual components divided by a "separator" and such sequence is immutable.

This module also tries to avoid assumptions about paths: people can come up with all kind of ideas of how a path would look like in system X, this module tries to avoid the dichotomy of POSIX or Windows. The classes on this file do work under the assumption of such dichotomy and are basically factories that build path objects from the "right" classes.
"""

from logging import getLogger
from os import name as os_name

from ._base import __version__, BasePurePath
from .posix import PosixPath, PurePosixPath
from .windows import PureWindowsPath

LOGGER = getLogger(__name__)


class PurePath:
	"""Pure path factory
	It works under the POSIX vs Windows dichotomy: it will return a PureWindowsPath (built with the parameters provided) if it's running on Windows or a PurePosixPath otherwise.
	"""
	
	def __new__(cls, *args, **kwargs):
		"""Creation magic
		Simple system detection to select the right class to instantiate.
		"""
		
		if os_name == 'nt':
			return PureWindowsPath(*args, **kwargs)
		else:
			return PurePosixPath(*args, **kwargs)
