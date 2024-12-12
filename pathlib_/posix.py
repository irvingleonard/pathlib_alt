#!python
"""A reimplementation of the python standard library's pathlib.
The original pathlib module seems to revolve around the idea that the path is a string, and then it can't decide if the paths are immutable or not. This module works with a different paradigm: a path is a sequence of individual components divided by a "separator" and such sequence is immutable.

This submodule contains the specifics for POSIX systems.
"""

from abc import abstractmethod
from logging import getLogger
import posixpath

from ._local import __version__, BaseOSPath, BaseOSPurePath

LOGGER = getLogger(__name__)


class PurePosixPath(BaseOSPurePath):
	"""
	
	"""
	
	parser = posixpath
	
	@classmethod
	def _parse_path(cls, path):
		"""Local parsing logic
		Should implement whatever logic is needed to parse the provided path string into a tuple (drive, root, tail)

		Drive and/or root could be empty, but both should be strings. Tail should be a sequence (could be empty too).
		The empty path would yield ('', '', [])

		The method should not try to simplify the path (resolve globbing, remove separator repetitions, etc.). The class must be able to recreate the original values, which becomes impossible if any part of it is removed here.
		"""

		if path:
			if path[0] == cls.SEPARATOR:
				if (path[1:2] == cls.SEPARATOR) and (path[2:3] != cls.SEPARATOR):
					root = cls.SEPARATOR * 2
					tail = path[2:]
				else:
					root = cls.SEPARATOR
					tail = path[1:]
			else:
				root = ''
				tail = path
			tail = tail.split(cls.SEPARATOR) if tail else []
			return '', root, tail
		else:
			return '', '', []

	def as_posix(self):
		"""
		Return the string representation of the path with forward (/) slashes.
		"""

		return str(self)

	def as_uri(self):
		"""Return the path as a URI.
		The logic is local, to be defined by the path syntax.
		"""

		if not self.is_absolute():
			raise ValueError("relative path can't be expressed as a file URI")
		return 'file://' + str(self)


class PosixPath(BaseOSPath, PurePosixPath):
	"""
	
	"""
	
	@classmethod
	def new_instance(cls, *args, **kwargs):
		"""
		
		"""
		
		return cls(*args, **kwargs).stat()
	
	## Parsing and generating URIs ##
	
	@classmethod
	def from_uri(cls, uri):
		"""From URI
		Return a new path object from parsing a "file" URI.

		:param uri: The URI to parse
		:return type(self): A new instance of this type of path based out of the URI
		"""
		
		raise NotImplementedError('from_uri')
	
	def as_uri(self):
		"""As URI
		Represent the path as a "file" URI.

		:return bool: A string representing the supposedly "file URI" for this path.
		"""
		
		raise NotImplementedError('as_uri')
		
	## Expanding and resolving paths ##
	
	@classmethod
	def home(cls, user=None):
		"""User home
		Retrieves the user’s home directory path. If the home directory can’t be found, RuntimeError is raised.

		:return type(cls): A new instance of this type pointing to the provided user's home directory (current user with default None)
		"""
		
		environ = cls._get_os_attr('environ', call_it=False)
		if user is None:
			if ('HOME' in environ) and environ['HOME']:
				return environ['HOME']
			else:
				user = cls._get_os_attr('getlogin')
				
		try:
			import pwd
			return pwd.getpwnam(user).pw_dir
		except (ImportError, KeyError):
			raise RuntimeError('Home directory not available for user "{}"'.format(user))
	
	def expanduser(self, fail_hard=True):
		"""Expand user
		Resolve the "~" and "~user" constructs. If a home directory can’t be resolved and the fail_hard parameter is True, RuntimeError is raised; otherwise the constructs are not replaced.
		
		Ref: https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_06_01

		:return type(cls): A new instance of this type with the user's home directory expanded (or not)
		"""
		
		if self.tail:
			if self.tail[0] == '~':
				try:
					return self.home()
				except RuntimeError:
					if fail_hard:
						raise
			elif self.tail[0] and (self.tail[0][0] == '~'):
				try:
					return self.home(user=self.tail[0][1:])
				except RuntimeError:
					if fail_hard:
						raise
				
		return self
	
	@abstractmethod
	def absolute(self):
		"""Anchor it, making it non-relative
		Make the path absolute by anchoring it. Does not "resolve" the path (interpret upwards movements or follow symlinks)

		:return type(cls): A new instance of this type which is anchored.
		"""
		
		raise NotImplementedError('absolute')
	
	@abstractmethod
	def resolve(self, strict=False):
		"""Resolve the absolute path
		Make the path absolute not only with an anchor but in the underlying filesystem by resolving upwards movements and following symlinks.

		:param bool? strict: If False, it will be a best effort process. Non-existing branches and symlinks loops will break the process and non-resolved part will be appended as-is, "assuming" that it will be there. When True, such problems will raise an OSError instead.
		:return type(cls): A new instance of this type which is absolute.
		"""
		
		raise NotImplementedError('resolve')
	
	@abstractmethod
	def readlink(self):
		"""Resolve link
		Resolves the path to which the symbolic link points

		:return type(cls): A new instance of this type pointing to the symlink's target.
		"""
		
		raise NotImplementedError('readlink')
	
	@classmethod
	def test(cls, *parts):
		return cls(*parts).expanduser(fail_hard=False)