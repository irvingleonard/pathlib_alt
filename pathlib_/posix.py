#!python
'''A reimplementation of the python standard library's pathlib.
The original pathlib module seems to revolve around the idea that the path is a string, and then it can't decide if the paths are inmutable or not. This module works with a different paradigm: a path is a sequence of individual components divided by a "separator" and such sequence is inmutable.

This submodule contains the specifics for POSIX systems.
'''

import logging

from ._base import BaseOSPath, BasePurePath

__version__ = '2023.1'

LOGGER = logging.getLogger(__name__)


class PurePosixPath(BasePurePath):

	@classmethod
	def _parse_path(cls, path):
		'''Local parsing logic
		Should implement whatever logic is needed to parse the provided path string into a tuple (drive, root, tail)

		Drive and/or root could be empty, but both should be strings. Tail should be a sequence (could be empty too).
		The empty path would yield ('', '', [])

		The method should not try to simplify the path (resolve globbing, remove separator repetitions, etc.). The class must be able to recreate the original values, which becomes impossible if any part of it is removed here.
		'''

		if path:
			if path[0] == cls.SEPARATOR:
				root = cls.SEPARATOR
				tail = path[1:]
			else:
				root = ''
				tail = path
			tail = tail.split(cls.SEPARATOR) if tail else []
			return ('', root, tail)
		else:
			return ('', '', [])

	def as_posix(self):
		'''Return the string representation of the path with forward (/) slashes.'''

		return str(self)

	def as_uri(self):
		'''Return the path as a URI.
		The logic is local, to be defined by the path syntax.
		'''

		if not self.is_absolute():
			raise ValueError("relative path can't be expressed as a file URI")
		return 'file://' + str(self)


class PosixPath(BaseOSPath, PurePosixPath):
	
	@classmethod
	def new_instance(cls, *args, **kwargs):
		return cls(*args, **kwargs).stat()
