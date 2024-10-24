#!python
"""A reimplementation of the python standard library's pathlib.
The original pathlib module seems to revolve around the idea that the path is a string, and then it can't decide if the paths are immutable or not. This module works with a different paradigm: a path is a sequence of individual components divided by a "separator" and such sequence is immutable.

This submodule implements the basis of the protocol (abstract and base classes).
"""

from abc import ABC, abstractmethod
from io import open as io_open, text_encoding as io_text_encoding
from logging import getLogger
import os

__version__ = '2023.1'

LOGGER = getLogger(__name__)
	

class BasePurePath(tuple):
	"""Base class for manipulating paths without I/O.
	BasePurePath represents a filesystem path and offers operations which don't imply any actual filesystem I/O.

	This class expects the path to be a string or better (doesn't deal with bytes). It keeps 2 or more versions of the path around:
	- the original value, that will be returned with str() and the components can be accessed as part of the actual object (you can get a copy by slicing it)
	- the "simplified" value that consist of the very same value minus all the empty components, which will be returned by the os.fspath() protocol and the parts are available in the "parts" attribute.

	Added one main attribute called "pure_stem" which is the counterpart to "suffixes". This means that you could recreate the "name" attribute with:
	- name = stem + suffix   # working with a single extension
	- name = pure_stem + ''.join(suffixes)   # working with multiple extensions
	"""

	DRIVE_SUPPORTED = False
	INVALID_PATH_CHARS = frozenset()
	JOINPATH_INSANE_BEHAVIOR = False
	RESERVED_NAMES = frozenset()
	SEPARATOR = '/'
	SUFFIX_SEPARATOR = '.'

	def __add__(self, other):
		""""Addition" magic
		Append other as a continuous part of the current path.
		"""

		try:
			return self.joinpath(other)
		except TypeError:
			return NotImplemented

	def __fspath__(self):
		"""Fspath magic
		Implementing the fspath protocol from PEP 519. Return the "simplified" version of the path (might differ from the original).
		"""

		try:
			return self._fspath
		except AttributeError:
			if self.anchor:
				fspath_value = self.anchor + self.SEPARATOR.join(self.parts[1:])
			else:
				fspath_value = self.SEPARATOR.join(self.parts)
			fspath_value.encode('unicode-escape').decode()
			self._fspath = fspath_value
			return self._fspath

	def __getattr__(self, name):
		"""Lazy attribute resolution
		Avoid some processing until is actually needed.
		"""

		for attribute_names, resolver_callable in self.LOCAL_PARSING.items():
			if name in attribute_names:
				results = resolver_callable(self)
				for i in range(len(attribute_names)):
					self.__setattr__(attribute_names[i], results[i])
					if name == attribute_names[i]:
						result = results[i]
				return result

		raise AttributeError(name)

	def __new__(cls, *args, drive = None, root = None, tail = None):
		"""Creation magic
		Getting all the details to build the final object.

		The drive/root/tail keyword parameters can be used to avoid the usually expensive path parsing logic.
		"""

		if (drive is not None) or (root is not None) or (tail is not None):
			if (drive is None) or (root is None) or (tail is None):
				raise ValueError("When using drive/root/tail value to build path you must provide the three of them.")
			if args:
				LOGGER.warning('Using drive/root/tail to build path; Ignoring provided paths: %s', args)
			drive, root, tail = drive, root, tail
		else:
			paths = []
			for arg in args:
				if isinstance(arg, cls):
					paths.extend(list(arg))
				else:
					try:
						path = os.fspath(arg)
					except TypeError:
						path = arg
					if not isinstance(path, str):
						raise TypeError(f"argument should be a str or an os.PathLike object where __fspath__ returns a str, not {type(path).__name__!r}")
					paths.append(path)

			drive, root, tail = cls._parse_path(cls.SEPARATOR.join(paths))

		cls._validate_tail_parts(*tail)
		anchor = drive + root

		path = super().__new__(cls, ([anchor] if anchor else []) + tail)
		path.parts = tuple(([anchor] if anchor else []) + [part for part in tail if part])

		path.drive, path.root, path.anchor, path._tail = drive, root, anchor, tail
		path.LOCAL_PARSING = {
			('name', 'stem', 'suffix', 'pure_stem', 'suffixes') : path._parse_name,
			('parent', 'parents') : path._get_parents,
		}

		return path

	def __repr__(self):
		"""Repr magic
		Create a machine friendly representation of the object.
		"""

		return "{}({})".format(self.__class__.__name__, repr(str(self)))

	def __radd__(self, other):
		"""Reverse "addition" magic
		When the left hand side is naïve and doesn't know how to do the "addition".
		"""

		try:
			return self.convert_path(other) + self
		except TypeError:
			return NotImplemented

	def __rtruediv__(self, other):
		"""Reverse "division" magic
		When the left hand side is naïve and doesn't know how to do the "division".
		"""

		try:
			return self.convert_path(other) / self
		except TypeError:
			return NotImplemented

	def __str__(self):
		"""String magic
		Return the string representation of the path, suitable for passing to system calls.

		ToDo: Why default to "."?
		"""

		try:
			return self._str
		except AttributeError:
			str_value = ((self.anchor if self.anchor else '') + self.SEPARATOR.join(self._tail)) or '.'
			str_value.encode('unicode-escape').decode()
			self._str = str_value
			return self._str

	def __truediv__(self, other):
		""""Division" magic
		Append other as a continuous part of the current path.
		"""

		try:
			return self.joinpath(other)
		except TypeError:
			return NotImplemented

	@classmethod
	def _get_parents(cls, path_instance):
		"""Get the parents of a certain path instance
		It should be usable by all applications but it could be overriden if needed.
		"""

		parents = []
		if path_instance._tail:
			for i in range(len(path_instance._tail) - 1, 0, -1):
				parents.append(cls(drive = path_instance.drive, root = path_instance.root, tail = path_instance._tail[:i]))
			if path_instance.anchor:
				parents.append(cls(drive = path_instance.drive, root = path_instance.root, tail = []))
			else:
				parents.append(cls())
			if len(parents):
				parent = parents[0]
		else:
			parent = path_instance

		return parent, parents

	@staticmethod
	def _parse_name(path_instance):
		"""Local name parsing logic
		This implementation should work most of the time, but it can be overriden if needed.
		New implementations should return the same tuple, though: name, stem, suffix, pure_stem, suffixes
		"""

		name = path_instance._tail[-1] if path_instance._tail else ''
		if (not name) or name.endswith(path_instance.SUFFIX_SEPARATOR):
			suffixes = []
		else:
			suffixes = [path_instance.SUFFIX_SEPARATOR + suffix for suffix in name.lstrip(path_instance.SUFFIX_SEPARATOR).split(path_instance.SUFFIX_SEPARATOR)[1:]]
		suffix = suffixes[-1] if suffixes else ''
		stem = name[:-len(suffix)] if suffix else name
		# New Attribute
		pure_stem = name[:-len(''.join(suffixes))] if suffixes else name

		return name, stem, suffix, pure_stem, suffixes

	@classmethod
	def _parse_path(cls, path):
		"""Local parsing logic
		Should implement whatever logic is needed to parse the provided path string into a tuple (drive, root, tail)

		Drive and/or root could be empty, but both should be strings. Tail should be a sequence (could be empty too).
		The empty path would yield ('', '', [])

		The method should not try to simplify the path (resolve globbing, remove separator repetitions, etc.). The class must be able to recreate the original values, which becomes impossible if any part of it is removed here.
		"""

		raise NotImplementedError('_parse_path()')

	@classmethod
	def _validate_tail_parts(cls, *tail_parts):
		"""Validate the name of the provided tail parts
		Check each part's name against the list of invalid characters and raises ValueError on a match.
		"""

		if not tail_parts:
			return True

		for part in tail_parts:
			if frozenset(part) & (cls.INVALID_PATH_CHARS | frozenset(cls.SEPARATOR)):
				raise ValueError('Invalid path name: {}'.format(part))

		return True

	def as_posix(self):
		"""Return the string representation of the path with forward (/) slashes."""

		raise NotImplementedError('as_posix()')

	def as_uri(self):
		"""Return the path as a URI.
		The logic is local, to be defined by the path syntax.
		"""

		raise NotImplementedError('as_uri()')

	@classmethod
	def convert_path(cls, path):
		"""Convert the provided path to an object of this class.
		Very thin layer, just an optimization to avoid parsing the same object several times. It basically confirms that the path is in the right "format".
		"""

		return path if isinstance(path, cls) else cls(path)

	def is_absolute(self):
		"""True if the path is absolute. A path is considered absolute if it has both a root and a drive (if supported)."""

		return (bool(self.drive) if self.DRIVE_SUPPORTED else True) and bool(self.root)

	def is_relative_to(self, other):
		"""Return True if the path is relative to another path or False."""

		other = self.convert_path(other)
		return other == self or other in self.parents

	def is_reserved(self):
		"""Return True if the path contains one of the special names reserved by the system, if any."""

		return self.name in self.RESERVED_NAMES

	def joinpath(self, *pathsegments):
		"""Combine this path with one or several arguments, and return a new subpath.

		The JOINPATH_INSANE_BEHAVIOR (default upstream behavior, currently not implemented) would return a totally different path if one of the arguments is anchored; actually, it would replace the path with the latest anchored argument joined to the rest (and would drop everything else, including the current content and all the earliest arguments).
		Ex: ('/', 'tmp').joinpath('esdferts-asf328', '/usr/local/bin/my_script.sh', '/etc', 'shadow') would yield ('/', 'etc', 'shadow')
		"""

		tails = []
		for path in pathsegments:
			path = self.convert_path(path)
			if self.JOINPATH_INSANE_BEHAVIOR:
				raise NotImplementedError('For you to implement here: JOINPATH_INSANE_BEHAVIOR')
			elif path.anchor():
				raise ValueError("Can't join an anchored path")
			else:
				tails.extend(list(path._tail))

		return self.__class__(drive = self.drive, root = self.root, tail = self._tail + tails)

	def match(self, pattern):
		"""Local globbing logic
		Should follow your system's globbing features.
		"""

		raise NotImplementedError('match()')

	def relative_to(self, other):
		"""Return the relative path to another path

		If the operation is not possible (because this is not related to the other path), raise ValueError.
		"""

		other = self.convert_path(other)
		if not self.is_relative_to(other):
			raise ValueError(f"{str(self)!r} is not in the subpath of {str(other)!r}")

		return self.__class__(drive = '', root = '', tail = self._tail[len(other._tail):])

	def with_name(self, name):
		"""Return a similar path with the file name replaced.

		It won't work on paths without names (like the root)
		The name can't be empty, nor have the SEPARATOR in it, nor be the "dot" (".")
		"""

		if not self.name:
			raise ValueError("%r has an empty name" % (self,))
		self._validate_tail_parts(name)

		return self.__class__(drive = self.drive, root = self.root, tail = self._tail[:-1] + [name])

	def with_pure_stem(self, pure_stem):
		"""Return a similar path with the pure_stem replaced."""

		if (not pure_stem) or (pure_stem[-1] == self.SUFFIX_SEPARATOR):
			raise ValueError('Invalid pure_stem "{}"'.format(pure_stem))
		if self.SUFFIX_SEPARATOR in pure_stem.lstrip(self.SUFFIX_SEPARATOR):
			raise ValueError('Provided pure_stem is not pure, it contains suffixes "{}"'.format(pure_stem))
		return self.with_name(pure_stem + ''.join(self.suffixes))

	def with_stem(self, stem):
		"""Return a similar path with the stem replaced."""

		if not stem:
			raise ValueError('Invalid stem "{}"'.format(stem))
		return self.with_name(stem + self.suffix)

	def with_suffix(self, suffix):
		"""Return a similar path with the file suffix replaced.

		If the path has no suffix, add given suffix.
		If the given suffix is an empty string, remove the suffix from the path.
		"""

		if suffix and not suffix.startswith(self.SUFFIX_SEPARATOR) or suffix == self.SUFFIX_SEPARATOR:
			raise ValueError('Invalid suffix {}'.format(suffix))
		return self.with_name(self.stem + suffix)

	def with_suffixes(self, *suffixes):
		"""Return a similar path with the file suffixes replaced.

		If the path has no suffixes, add given suffixes.
		If no suffixes are given, remove the suffixes from the path.
		"""

		for suffix in suffixes:
			if not suffix.startswith(self.SUFFIX_SEPARATOR) or suffix == self.SUFFIX_SEPARATOR:
				raise ValueError('Invalid suffix {}'.format(suffix))
		return self.with_name(self.pure_stem + ''.join(suffixes))


class BasePath(ABC):
	"""Base class for I/O enabled methods.
	BasePath implements the diverse methods that do I/O.

	This class is mostly abstract and defines the rest of the public interface of a concrete Path (in addition to BasePurePath). Only a few high level methods are implemented and the rest (the most part of the class) are abstract and should be overriden by the child classes. Some mechanisms, like all the stat related methods, are not truly portable (not applicable to virtual filesystems, for example) so they're not implemented here. The enhancement of this class for local filesystems is called BaseOSPath.
	"""

	## Querying file type and status ##

	@abstractmethod
	def stat(self, *, follow_symlinks = True):
		"""Return the result of the stat() system call on this path, like os.stat() does.
		"""

		raise NotImplementedError('stat')

	@abstractmethod
	def lstat(self):
		"""
		Like stat(), except if the path points to a symlink, the symlink's status information is returned, rather than its target's.
		"""

		return self.stat(follow_symlinks = False)

	@abstractmethod
	def exists(self, *, follow_symlinks = True):
		""" Whether this path exists.
        This method normally follows symlinks; to check whether a symlink exists, add the argument follow_symlinks=False.
		"""

		raise NotImplementedError('exists')

	@abstractmethod
	def is_file(self):
		"""Whether this path is a regular file (also True for symlinks pointing to regular files).
		"""

		raise NotImplementedError('is_file')

	@abstractmethod
	def is_dir(self):
		"""Whether this path is a directory.
		"""

		raise NotImplementedError('is_dir')

	@abstractmethod
	def is_symlink(self):
		"""Whether this path is a symbolic link.
		"""

		raise NotImplementedError('is_symlink')

	def is_junction(self):
		"""Whether this path is a junction.
		Junctions are a Windows-only feature, not present in POSIX nor the majority of virtual filesystems. There is no cross-platform idiom to check for junctions (using stat().st_mode).
		"""

		return False

	@abstractmethod
	def is_mount(self):
		"""Check if this path is a mount point
		"""

		raise NotImplementedError('is_mount')

	@abstractmethod
	def is_socket(self):
		"""Whether this path is a socket.
		"""

		raise NotImplementedError('is_socket')

	@abstractmethod
	def is_fifo(self):
		"""Whether this path is a FIFO.
		"""

		raise NotImplementedError('is_fifo')

	@abstractmethod
	def is_block_device(self):
		"""Whether this path is a block device.
		"""

		raise NotImplementedError('is_block_device')

	@abstractmethod
	def is_char_device(self):
		"""Whether this path is a character device.
		"""

		raise NotImplementedError('is_char_device')

	@abstractmethod
	def samefile(self, other_path):
		"""Return whether other_path is the same or not as this file (as returned by os.path.samefile()).
		"""

		raise NotImplementedError('samefile')

	## Reading and writing files ##

	@abstractmethod
	def open(self, mode = 'r', buffering = -1, encoding = None, errors = None, newline = None):
		"""Open the file pointed to by this path and return a file object, as the built-in open() function does.
		"""

		raise NotImplementedError('open')

	def read_text(self, encoding = None, errors = None):
		"""
		Open the file in text mode, read it, and close the file.
		"""

		encoding = io_text_encoding(encoding)
		with self.open(mode = 'r', encoding = encoding, errors = errors) as f:
			return f.read()

	def read_bytes(self):
		"""
		Open the file in bytes mode, read it, and close the file.
		"""

		with self.open(mode = 'rb') as f:
			return f.read()

	def write_text(self, data, encoding = None, errors = None, newline = None):
		"""
		Open the file in text mode, write to it, and close the file.
		"""

		if not isinstance(data, str):
			raise TypeError('data must be str, not %s' % data.__class__.__name__)
		encoding = io_text_encoding(encoding)
		with self.open(mode = 'w', encoding = encoding, errors = errors, newline = newline) as f:
			return f.write(data)

	def write_bytes(self, data):
		"""
		Open the file in bytes mode, write to it, and close the file.
		"""

		view = memoryview(data)
		with self.open(mode = 'wb') as f:
			return f.write(view)

	## Reading directories ##

	@abstractmethod
	def iterdir(self):
		"""Yield path objects of the directory contents.
        The children are yielded in arbitrary order, and the special entries '.' and '..' are not included.
		"""

		raise NotImplementedError('iterdir')

	@abstractmethod
	def glob(self, pattern, *, case_sensitive = None):
		"""Iterate over this subtree and yield all existing files (of any kind, including directories) matching the given relative pattern.
		"""

		raise NotImplementedError('glob')

	@abstractmethod
	def rglob(self, pattern, *, case_sensitive = None):
		"""Recursively yield all existing files (of any kind, including directories) matching the given relative pattern, anywhere in this subtree.
		"""

		raise NotImplementedError('rglob')

	@abstractmethod
	def walk(self, top_down = True, on_error = None, follow_symlinks = False):
		"""Walk the directory tree from this directory, similar to os.walk().
		"""

		raise NotImplementedError('walk')

	## Creating files and directories ##

	@abstractmethod
	def touch(self, mode = 0o666, exist_ok = True):
		"""Create this file with the given access mode, if it doesn't exist.
		"""

		raise NotImplementedError('touch')

	@abstractmethod
	def mkdir(self, mode = 0o777, parents = False, exist_ok = False):
		"""Create a new directory at this given path.
		"""

		raise NotImplementedError('mkdir')

	@abstractmethod
	def symlink_to(self, target, target_is_directory = False):
		"""Make this path a symlink pointing to the target path. Note the order of arguments (link, target) is the reverse of os.symlink.
		"""

		raise NotImplementedError('symlink_to')

	@abstractmethod
	def hardlink_to(self, target):
		"""Make this path a hard link pointing to the same file as *target*. Note the order of arguments (self, target) is the reverse of os.link's.
		"""

		raise NotImplementedError('hardlink_to')

	## Renaming and deleting ##

	@abstractmethod
	def rename(self, target):
		"""Rename this file or directory to the given target, and return a new Path instance pointing to target.
		"""

		raise NotImplementedError('rename')

	@abstractmethod
	def replace(self, target):
		"""Rename this file or directory to the given target, and return a new Path instance pointing to target.
		If target points to an existing file or empty directory, it will be unconditionally replaced. The target path may be absolute or relative. Relative paths are interpreted relative to the current working directory, not the directory of the Path object.
		"""

		raise NotImplementedError('replace')

	@abstractmethod
	def unlink(self, missing_ok = False):
		"""Remove this file or symbolic link.
		If the path points to a directory, use Path.rmdir() instead. If missing_ok is false (the default), FileNotFoundError is raised if the path does not exist. If missing_ok is true, FileNotFoundError exceptions will be ignored (same behavior as the POSIX rm -f command).
		"""

		raise NotImplementedError('unlink')

	@abstractmethod
	def rmdir(self):
		"""Remove this directory. The directory must be empty.
		"""

		raise NotImplementedError('rmdir')

	## Other methods ##

	@classmethod
	@abstractmethod
	def cwd(cls):
		"""
		Return a new path pointing to the current working directory
		"""

		raise NotImplementedError('cwd')

	@classmethod
	@abstractmethod
	def home(cls):
		"""User home
		Return a new path object representing the user’s home directory. If the home directory can’t be resolved, RuntimeError is raised.
		"""

		raise NotImplementedError('home')

	@abstractmethod
	def chmod(self, mode, *ignoring, follow_symlinks = True):
		"""Change the file mode and permissions
		This method normally follows symlinks. Some Unix flavours support changing permissions on the symlink itself; on these platforms you may add the argument follow_symlinks = False, or use lchmod().
		"""

		raise NotImplementedError('chmod')

	@abstractmethod
	def expanduser(self):
		"""Return a new path with expanded ~ and ~user constructs. If a home directory can’t be resolved, RuntimeError is raised.
		"""

		raise NotImplementedError('expanduser')

	@abstractmethod
	def group(self):
		"""Return the name of the group owning the file. KeyError is raised if the file’s gid isn’t found in the system database.
		"""

		raise NotImplementedError('group')

	def lchmod(self, mode):
		"""
		Like chmod(), except if the path points to a symlink, the symlink's permissions are changed, rather than its target's.
		"""

		self.chmod(mode, follow_symlinks = False)

	@abstractmethod
	def owner(self):
		"""Return the name of the user owning the file. KeyError is raised if the file’s uid isn’t found in the system database.
		"""

		raise NotImplementedError('owner')

	@abstractmethod
	def readlink(self):
		"""Return the path to which the symbolic link points
		"""

		raise NotImplementedError('readlink')

	@abstractmethod
	def absolute(self):
		"""Make the path absolute, without normalization or resolving symlinks. Returns a new path object.
		"""

		raise NotImplementedError('absolute')

	@abstractmethod
	def resolve(self, strict = False):
		"""Make the path absolute, resolving any symlinks. A new path object is returned.
		"""

		raise NotImplementedError('resolve')
