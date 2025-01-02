#!python
"""A reimplementation of the python standard library's pathlib.
The original pathlib module seems to revolve around the idea that the path is a string, and then it can't decide if the paths are immutable or not. This module works with a different paradigm: a path is a sequence of individual components divided by a "separator" and such sequence is immutable.

This submodule contains the specifics for POSIX systems.
"""

from abc import abstractmethod
from errno import ELOOP
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
				return cls(environ['HOME'])
			else:
				user = cls._get_os_attr('getlogin')
				
		try:
			import pwd
			return cls(pwd.getpwnam(user).pw_dir)
		except (ImportError, KeyError):
			raise RuntimeError('Home directory not available for user "{}"'.format(user))
	
	def absolute(self, cwd=None):
		"""Anchor it, making it non-relative
		Make the path absolute by anchoring it. Does not "resolve" the path (interpret upwards movements or follow symlinks)

		:return type(cls): A new instance of this type which is anchored.
		"""
		
		if self.is_absolute():
			return self
		
		if cwd is None:
			cwd = self.cwd()
		return self.__class__(drive=cwd.drive, root=cwd.root, tail=cwd.tail + self.tail)
	
	@abstractmethod
	def resolve(self, *, strict=False, maxlinks=None, traversals=None, link_count=0):
		"""Resolve the absolute path
		Make the path absolute not only with an anchor but in the underlying filesystem by resolving upwards movements and following symlinks.

		:param bool? strict: If False, it will be a best effort process. Non-existing branches and symlinks loops will break the process and non-resolved part will be appended as-is, "assuming" that it will be there. When True, such problems will raise an OSError instead.
		:return type(cls): A new instance of this type which is absolute.
		"""
		
		rest = list(self.simplified_tail[::-1])
		if traversals is None:
			traversals = {}
		result = self.root_dir() if self.is_absolute() else self.cwd()
		
		while rest:
			
			part = rest.pop()
			if part == self.PARENT_DIRECTORY_ENTRY:
				result = result.parent
				continue
			result = result.append(part)
			if result.is_symlink():
				link_target = result.readlink()
				if maxlinks is None:
					if (result in traversals) and (traversals[result] == len(rest)):
						if strict:
							raise OSError(ELOOP, self._get_os_attr('strerror', ELOOP), str(result))
						else:
							return result.joinpath(*rest[::-1])
					traversals[result] = len(rest)
				else:
					link_count += 1
					if link_count > maxlinks:
						raise OSError(ELOOP, self._get_os_attr('strerror', ELOOP), str(result))
				if link_target.is_absolute() and not link_target.is_symlink():
					result = link_target
				else:
					result = link_target.absolute(cwd=result.parent).resolve(strict=strict, maxlinks=maxlinks, traversals=traversals, link_count=link_count)
			elif rest and not result.is_dir():
				raise NotADirectoryError(result)
		
		return result
			
			
	
	@classmethod
	def test(cls, *parts, child='.'):
		return cls(*parts).resolve(strict=True)
		return cls(*parts).is_symlink()