#!python
'''A reimplementation of the python standard library's pathlib.
The original pathlib module seems to revolve around the idea that the path is a string, and then it can't decide if the paths are inmutable or not. This module works with a different paradigm: a path is a sequence of individual components divided by a "separator" and such sequence is inmutable.

This submodule contains the specifics for the Windows systems.
'''

import logging

from ._base import BasePurePath

__version__ = '2023.1'

LOGGER = logging.getLogger(__name__)


class PureWindowsPath(BasePurePath):

	CASE_SENSITIVE = False
	DRIVE_SUPPORTED = True
	RESERVED_NAMES = frozenset(['CON', 'PRN', 'AUX', 'NUL'] + ['COM{}'.format(i) for i in range(9)] + ['LPT{}'.format(i) for i in range(9)])
	INVALID_PATH_CHARS = frozenset(('<', '>', ':', '"', '/', '|', '?', '*'))
	SEPARATOR = '\\'

	@classmethod
	def _parse_path(cls, path):
		'''Local parsing logic
		Should implement whatever logic is needed to parse the provided path string into a tuple (drive, root, tail)

		Drive and/or root could be empty, but both should be strings. Tail should be a sequence (could be empty too).
		The empty path would yield ('', '', [])

		The method should not try to simplify the path (resolve globbing, remove separator repetitions, etc.). The class must be able to recreate the original values, which becomes impossible if any part of it is removed here.

		References:
		- https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file
		- https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation
		'''

		path = path.replace('/', cls.SEPARATOR) # This is a weird backwards compatibility reason. At the end of the day it seems that Windows internally converts it to its preferred separator.
		if path[:1] == cls.SEPARATOR:
			if path[1:2] == cls.SEPARATOR:
				if (path[2:3] in ['?','.']) and (path[3:4] == cls.SEPARATOR):
					# Namespace prefix, e.g. \\?\ or \\.\
					if path[2:3] == '.':
						# Win32 Device Namespace, e.g. \\.\COM56
						return path[:3], path[3], path[4:].split(cls.SEPARATOR)
					elif path[4:8] == 'UNC' + cls.SEPARATOR:
						# Win32 UNC drives through WinNT Namespace, e.g. \\?\UNC\server or \\?\UNC\server\share\path\to\somewhere
						late_path = [part for part in path[8:].split(cls.SEPARATOR)]
						drive = [part for part in late_path[:2] if part]
						tail = late_path[2:]
						if (path[8:] and not drive) or (late_path[1:2] and not late_path[0:1]) or ((len(drive) < 2) and tail):
							raise ValueError('Invalid drive: {}'.format(late_path[:2]))
						return path[:8] + cls.SEPARATOR.join(drive), cls.SEPARATOR if tail else '', tail
					elif path[5:6] == ':' and (path[6:7] == cls.SEPARATOR):
						# Win32 File through WinNT Namespace, e.g. \\?\X:\Windows
						return path[:6], path[6:7], path[7:].split(cls.SEPARATOR)
					else:
						# WinNT Namespace, e.g. \\?\Device\HarddiskVolume1 or \\?\KernelObjects\Session0
						cls.INVALID_PATH_CHARS = frozenset()
						return path[:3], path[3:4], path[4:].split(cls.SEPARATOR)
				else:
					# UNC drives, e.g. \\server or \\server\share\path\to\somewhere
					late_path = [part for part in path[2:].split(cls.SEPARATOR)]
					drive = [part for part in late_path[:2] if part]
					tail = late_path[2:]
					if (path[2:] and not drive) or (late_path[1:2] and not late_path[0:1]) or ((len(drive) < 2) and tail):
						raise ValueError('Invalid drive: {}'.format(late_path[:2]))
					return cls.SEPARATOR.join(['',''] + drive), cls.SEPARATOR if tail else '', tail
			else:
				# Relative path with root, e.g. \Windows
				return '', path[:1], path[1:].split(cls.SEPARATOR)
		elif path[1:2] == ':':
			if path[2:3] == cls.SEPARATOR:
				# Absolute drive-letter path, e.g. X:\Windows
				return path[:2], path[2:3], path[3:].split(cls.SEPARATOR)
			else:
				# Relative path with drive, e.g. X:Windows
				return path[:2], '', path[2:].split(cls.SEPARATOR)
		else:
			# Relative path, e.g. Windows
			return '', '', path.split(cls.SEPARATOR)

	@classmethod
	def _validate_tail_parts(cls, *tail_parts):
		'''Validate the name of the provided tail parts
		Check each part's name against the list of invalid characters. It assumes the last part is always a file, which might not be the case sometimes, if the path points to a directory, for example, but the BasePurePath is incapable of knowing that reliably.
		'''

		super()._validate_tail_parts(*tail_parts)

		for part in tail_parts:
			if part[-1:] in [' ', '.']:
				raise ValueError('Invalid file name: {}'.format(repr(part)))

		return True

	def as_posix(self):
		'''Return the string representation of the path with forward (/) slashes.'''

		return str(self).replace(self.SEPARATOR, '/')

	def as_uri(self):
		'''Return the path as a URI.
		The logic is local, to be defined by the path syntax.
		'''

		if not self.is_absolute():
			raise ValueError("relative path can't be expressed as a file URI")
		return 'file://' + self.as_posix()

	def is_reserved(self):
		'''Return True if the path contains one of the special names reserved by the system, if any.'''

		if self.pure_stem:
			if frozenset((self.pure_stem if self.CASE_SENSITIVE else self.pure_stem.upper(),)) & self.RESERVED_NAMES:
				return True
		return False
