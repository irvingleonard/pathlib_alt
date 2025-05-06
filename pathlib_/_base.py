#!python
"""A reimplementation of the python standard library's pathlib.
The original pathlib module seems to revolve around the idea that the path is a string, and then it can't decide if the paths are immutable or not. This module works with a different paradigm: a path is a sequence of individual components divided by a "separator" and such sequence is immutable.

This submodule implements the basis of the protocol (abstract and base classes).
"""

from abc import ABC, abstractmethod
from io import text_encoding as io_text_encoding
from logging import getLogger
from os import fspath
from re import IGNORECASE as RE_IGNORECASE, NOFLAG as RE_NOFLAG, match as re_match

from pathlib_.glob_ import translate as glob_translate

__version__ = '0.1.2'

JOINPATH_INSANE_BEHAVIOR = False
LOGGER = getLogger(__name__)
	

class BasePurePath(tuple):
	"""Base class for manipulating paths without I/O.
	BasePurePath represents a conceptual path and offers operations which don't imply any actual I/O.

	This class expects the path to be a string or better (doesn't deal with bytes). It keeps two versions of the path:
	- the original value, that will be returned with str() and the parts are available in the "parts" attribute (the "repr" logic uses this version).
	- the "simplified" value that will depend on the local simplification logic, which will be returned by the os.fspath() protocol and the components can be accessed as part of the actual object (you can get a copy by slicing it)
	By storing the simplified version on the underlying tuple it enables better comparisons since equivalent paths will be equal. The paths could also be normalized to ignore case differences, etc.

	Added one main attribute called "pure_stem" which is the counterpart to "suffixes". This means that you could recreate the "name" attribute with:
	- name = stem + suffix   # working with a single extension
	- name = pure_stem + ''.join(suffixes)   # working with multiple extensions
	"""
	
	DRIVE_SUPPORTED = False
	INVALID_PATH_CHARS = frozenset()
	INVALID_PATH_COMPONENTS = frozenset()
	JOINPATH_INSANE_BEHAVIOR = JOINPATH_INSANE_BEHAVIOR
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
				fspath_value = self.anchor + self.SEPARATOR.join(self[1:])
			else:
				fspath_value = self.SEPARATOR.join(self)
			fspath_value.encode('unicode-escape').decode()
			self._fspath = fspath_value
			return self._fspath

	def __getattr__(self, name):
		"""Lazy attribute resolution
		Avoid some processing until is actually needed.
		"""
		
		if name == '_basic_str':
			value = ((self.anchor if self.anchor else '') + self.SEPARATOR.join(self.tail))
			value.encode('unicode-escape').decode()
		elif name == '_pattern_str':
			value = self._basic_str
		else:
			for attribute_names, resolver_callable in self.LOCAL_PARSING.items():
				if name in attribute_names:
					results = resolver_callable(self)
					for i in range(len(attribute_names)):
						self.__setattr__(attribute_names[i], results[i])
						if name == attribute_names[i]:
							result = results[i]
					return result
	
			raise AttributeError(name)
		
		self.__setattr__(name, value)
		return value

	def __new__(cls, *args, drive=None, root=None, tail=None):
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
						path = fspath(arg)
					except TypeError:
						path = arg
					if not isinstance(path, str):
						raise TypeError(f"argument should be a str or an os.PathLike object where __fspath__ returns a str, not {type(path).__name__!r}")
					paths.append(path)

			drive, root, tail = cls._parse_path(cls.SEPARATOR.join(paths))

		anchor = drive + root
		parts = ([anchor] if anchor else []) + [part for part in tail]
		cls._validate_parts(anchor, *tail)
		simplified_tail = cls._simplify_tail(anchor, *tail)

		path = super().__new__(cls, ([anchor] if anchor else []) + simplified_tail)

		path.parts, path.drive, path.root, path.anchor, path.tail, path.simplified_tail = tuple(parts), drive, root, anchor, tuple(tail), tuple(simplified_tail)
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
		Using a default behavior here. This method usually gets replaced that's why the default behavior implementation lives in "_true_str".
		
		:return str: this path as a string
		"""
		
		try:
			return self._str
		except AttributeError:
			self._str = self._basic_str
			return self._str

	def __truediv__(self, other):
		""""Division" magic
		Append other as a continuous part of the current path.
		"""

		try:
			return self.joinpath(other)
		except TypeError:
			return NotImplemented

	@staticmethod
	def _get_parents(path_instance):
		"""Get the parents of a certain path instance
		The default implementation should work for most cases. Child classes can override it for custom behavior. New implementations should have the same signature and return the same structure.
		
		:param path_instance: the Path instance to get the parents from
		:return: currently a tuple of ('parent', 'parents') where parent is the direct parent and parents is the list from the closest to the furthest parent in the tree (as a tuple). The current expected result is the matching key on the cls.LOCAL_PARSING dictionary.
		"""
		
		cls = type(path_instance)
		parent, parents = path_instance, []
		if path_instance.tail:
			for i in range(len(path_instance.tail) - 1, 0, -1):
				parents.append(cls(drive=path_instance.drive, root=path_instance.root, tail=path_instance.tail[:i]))
			if path_instance.anchor:
				parents.append(cls(drive=path_instance.drive, root=path_instance.root, tail=[]))
			else:
				parents.append(cls())
			if len(parents):
				parent = parents[0]

		return parent, tuple(parents)

	@staticmethod
	def _parse_name(path_instance):
		"""Local name parsing logic
		This implementation should work for most cases.Child classes could still override it for custom behavior. New implementations should have the same signature and return the same structure.
		
		:param path_instance: the Path instance to get the name (and other values) for
		:return: currently a tuple of ('name', 'stem', 'suffix', 'pure_stem', 'suffixes') where name is the final component of the path (or some special case value), stem + suffix = name, and pure_stem + ''.join(suffixes) = name. The up-to-date expected result structure can be found in the matching key on the cls.LOCAL_PARSING dictionary.
		"""

		name = path_instance.tail[-1] if path_instance.tail else ''
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

		The method should not try to simplify the path (resolve globbing, remove separator repetitions, etc.). The class must be able to recreate the original values, which becomes impossible if any part of it is removed here.
		
		:param path: the "path" provided to build the instance. Should be a string or better.
		:return: a tuple (drive, root, tail) where the empty result would be ('', '', []). The drive and root values are the "sections" of the anchor, and tail is a list containing all the other "parts" for the path.
		"""

		raise NotImplementedError('_parse_path()')
	
	@staticmethod
	def _simplify_tail(anchor='', *tail):
		"""Simplify components
		The concept is that it will apply local path logic to "resolve" all possible path components without actually looking for its existence.
		Ex: the POSIX/Windows path ('foo', '', 'bar', '..', 'baz', '.') would be simplified to ('foo', 'baz')
		
		The default is a passthrough (do nothing).
		
		:param tail: the tail of the Path to simplify
		:return: simplified version of the provided tail
		"""
		
		return list(tail)

	@classmethod
	def _validate_parts(cls, anchor='', *tail):
		"""Validate the name of the provided tail parts
		Check each part's name against the list of invalid characters and raises ValueError on a match.
		
		:param tail_parts: The parts of the tail to validate
		:return bool: True if all are valid, False otherwise.
		"""

		if not tail:
			return True

		if invalid_component := frozenset(tail) & cls.INVALID_PATH_COMPONENTS:
			raise ValueError('Invalid path component: {}'.format(invalid_component))
		
		for part in tail:
			if invalid_chars := frozenset(part) & (cls.INVALID_PATH_CHARS | frozenset(cls.SEPARATOR)):
				raise ValueError('Invalid character(s) in path component: "{}" -> {}'.format(invalid_chars, part))

		return True

	def as_posix(self):
		"""As POSIX
		Return the string representation of the path with forward (/) slashes. Not a great method but kept for full compatibility.
		
		:return str: A string representing the supposedly "POSIX equivalent" of this path.
		"""
		
		raise NotImplementedError('as_posix()')
	
	def is_absolute(self):
		"""Is it absolute?
		True if the path is absolute. A path is considered absolute if it has both a root and a drive (if supported).

		:return bool: True if it has root and drive (if supported), False otherwise.
		"""
		
		return (bool(self.drive) if self.DRIVE_SUPPORTED else True) and bool(self.root)
	
	def is_relative_to(self, other):
		"""Is it relative to "other"?
		Check if the path is relative to another path.

		:param other: The potentially parent path
		:return bool: True if it's a parent, False otherwise
		"""
		
		other = self.convert_path(other)
		return other == self or other in self.parents
	
	def joinpath(self, *pathsegments):
		"""Join path
		Combine this path with one or several arguments, and return a new subpath.

		The JOINPATH_INSANE_BEHAVIOR (default upstream behavior, currently not implemented) would return a totally different path if one of the arguments is anchored; actually, it would replace the path with the latest anchored argument joined to the rest (and would drop everything else, including the current content and all the earliest arguments).
		Ex: ('/', 'tmp').joinpath('esdferts-asf328', '/usr/local/bin/my_script.sh', '/etc', 'shadow') would yield ('/', 'etc', 'shadow')

		:param pathsegments: The multiple segments to join into this path
		:return type(self): A new instance of this type of path with the extra segments appended
		"""
		
		drive, root, tail = self.drive, self.root, list(self.tail)
		for path in pathsegments:
			path = self.convert_path(path)
			if path.anchor:
				if self.JOINPATH_INSANE_BEHAVIOR:
					if (path.drive == self.drive) and not path.root:
						tail.extend(list(path.tail))
					else:
						drive, root, tail = path.drive, path.root, list(path.tail)
				else:
					raise ValueError("Can't join an anchored path")
			else:
				tail.extend(list(path.tail))
		
		return self.__class__(drive=drive, root=root, tail=tail)
	
	def full_match(self, pattern, *, case_sensitive=None):
		"""Globbing with the pattern language
		Match this path against the provided glob-style pattern.

		:param str pattern: The pattern, following the "pattern language"
		:param bool? case_sensitive: True will make comparisons case-sensitive, False will do the opposite. None (the default) will "guess" the right value from the system.
		:return bool: True if matching is successful, False otherwise.
		"""
		
		return self.match(pattern, case_sensitive=case_sensitive, recursive=True)

	def match(self, pattern, *, case_sensitive=None, recursive=False):
		"""Globbing with the pattern language
		Match this path against the provided non-recursive glob-style pattern. Empty patterns aren't allowed, recursive wildcard ("**") becomes "*", and relative patterns will trigger the matching to be done from the right.

		:param str pattern: The pattern, following the "pattern language".
		:param bool? case_sensitive: True will make comparisons case-sensitive, False will do the opposite. None (the default) will "guess" the right value from the system.
		:return bool: True if matching is successful, False otherwise.
		"""
		
		pattern = self.convert_path(pattern)
		if (case_sensitive is None) and hasattr(self, 'CASE_SENSITIVE'):
			case_sensitive = self.CASE_SENSITIVE
		flags = RE_IGNORECASE if (case_sensitive is not None) and not case_sensitive else RE_NOFLAG
		
		if recursive:
			regex = glob_translate(pattern._pattern_str, recursive=True, include_hidden=True, seps=pattern.SEPARATOR)
			return re_match(regex, self._pattern_str, flags=flags) is not None
		
		reverse_pattern_parts, reverse_path_parts = pattern.parts[::-1], self.parts[::-1]
		
		if not reverse_pattern_parts:
			raise ValueError("empty pattern")
		if len(reverse_path_parts) < len(reverse_pattern_parts):
			return False
		if len(reverse_path_parts) > len(reverse_pattern_parts) and pattern.anchor:
			return False
		
		for path_part, pattern_part in zip(reverse_path_parts, reverse_pattern_parts):
			regex = glob_translate(str(pattern_part), recursive=False, include_hidden=True, seps=pattern.SEPARATOR)
			if re_match(regex, path_part, flags=flags) is None:
				return False
		return True

	def relative_to(self, other, walk_up=False):
		"""Relative to "other" path
		Compute a version of this path relative to the path presented by "other". If it's impossible, ValueError is raised.
		
		:param other: The supposed parent path
		:param bool walk_up: when true, "other" can be a sibling. This would be a local logic and would have to be reimplemented locally (it's not supported by default)
		:return type(self): A new instance of this type of path with the relative path
		"""
		
		if walk_up:
			raise NotImplementedError('relative_to with walk_up')

		other = self.convert_path(other)
		if not self.is_relative_to(other):
			raise ValueError(f"{str(self)!r} is not in the subpath of {str(other)!r}")

		return self.__class__(drive='', root='', tail=self.tail[len(other.tail):])

	def with_name(self, name):
		"""Different name
		Create a similar path with the name component replaced (the last part of the path).
		
		:param name: The name for the new path instance
		:return type(self): A new instance of this type of path with the new name
		"""

		return self.__class__(drive=self.drive, root=self.root, tail=(self.tail[:-1] + (name,)))
	
	def with_stem(self, stem):
		"""Different stem
		Create a similar path with the stem replaced.

		:param stem: The stem for the new path instance
		:return type(self): A new instance of this type of path with the new stem
		"""
		
		if (not stem) and self.suffix:
			raise ValueError("Can't clear stem while having suffix. Use with_name instead.")
		
		return self.with_name(stem + self.suffix)
	
	def with_pure_stem(self, pure_stem):
		"""Different pure_stem
		Create a similar path with the pure_stem replaced.
		
		:param pure_stem: The pure_stem for the new path instance
		:return type(self): A new instance of this type of path with the new pure_stem
		"""

		if (not pure_stem) or (pure_stem[-1] == self.SUFFIX_SEPARATOR):
			raise ValueError('Invalid pure_stem "{}"'.format(pure_stem))
		if self.SUFFIX_SEPARATOR in pure_stem.lstrip(self.SUFFIX_SEPARATOR):
			raise ValueError('Provided pure_stem is not pure, it contains suffixes "{}"'.format(pure_stem))
		return self.with_name(pure_stem + ''.join(self.suffixes))
	
	def with_suffix(self, suffix):
		"""Different suffix
		Create a similar path with the suffix replaced. If the path has no suffix, add given suffix. If the given suffix is an empty string, remove the suffix from the path.

		:param suffix: The suffix for the new path instance
		:return type(self): A new instance of this type of path with the new suffix
		"""
		
		if suffix and not suffix.startswith(self.SUFFIX_SEPARATOR) or suffix == self.SUFFIX_SEPARATOR:
			raise ValueError('Invalid suffix {}'.format(suffix))
		if not self.stem:
			raise ValueError("Can't add suffix to empty stem. Use with_name instead.")
		return self.with_name(self.stem + suffix)
	
	def with_suffixes(self, *suffixes):
		"""Different suffixes
		Create a similar path with the suffixes replaced. If the path has no suffixes, add given suffixes. If no suffixes are given, remove the suffixes from the path.

		:param suffixes: The list of suffixes for the new path instance
		:return type(self): A new instance of this type of path with the new suffixes
		"""
		
		for suffix in suffixes:
			if not suffix.startswith(self.SUFFIX_SEPARATOR) or suffix == self.SUFFIX_SEPARATOR:
				raise ValueError('Invalid suffix {}'.format(suffix))
		return self.with_name(self.pure_stem + ''.join(suffixes))
	
	@classmethod
	def with_segments(cls, *pathsegments):
		"""Legacy method
		Part of the original implementation, kept around for full compatibility
		
		:param pathsegments: Different components to form a new/combined path
		:return type(self): A new instance of this type of path out of the provided components
		"""
		
		return cls(*pathsegments)
	
	@classmethod
	def convert_path(cls, path):
		"""Convert the provided path to an object of this class.
		Very thin layer, just an optimization to avoid parsing the same object several times. It basically confirms that the path is in the right "format".

		:param path: The "path" to create the instance
		:return cls: An instance of "cls" created out of "path"
		"""
		
		return path if isinstance(path, cls) else cls(path)


class BasePath(ABC):
	"""Base class for I/O enabled methods.
	BasePath implements the diverse methods that do I/O.

	This class is mostly abstract and defines the rest of the public interface of a concrete Path (in addition to BasePurePath). Only a few high level methods are implemented and the rest (the most part of the class) are abstract and should be overriden by the child classes. Some mechanisms, like all the stat related methods, are not truly portable (not applicable to virtual filesystems, for example) so they're not implemented here. The enhancement of this class for local filesystems is called BaseOSPath.
	"""
	
	RESERVED_ABSOLUTE_PATHS = frozenset()
	RESERVED_NAMES = frozenset()
	RESERVED_RELATIVE_PATHS = frozenset()
	
	## Enhanced implementations ##
	
	def is_reserved(self):
		"""Is it reserved?
		Check if the path is somehow reserved. Checks the name, the path as relative, and the fully resolved path. In the original module this method lives in the PurePath class. It was moved here because it was extended to actually check for resolved paths that are reserved (hence, an "impure" operation).

		:return bool: True if the path contains one of the special names reserved by the system, or is a reserved relative path, or is a reserved absolute path
		"""
		
		return (self.name in self.RESERVED_NAMES) or (self in self.RESERVED_RELATIVE_PATHS) or (self.resolve() in self.RESERVED_ABSOLUTE_PATHS)
	
	## Parsing and generating URIs ##
	
	@classmethod
	@abstractmethod
	def from_uri(cls, uri):
		"""From URI
		Return a new path object from parsing a "file" URI.
		
		:param uri: The URI to parse
		:return type(self): A new instance of this type of path based out of the URI
		"""
		
		raise NotImplementedError('from_uri')
	
	@abstractmethod
	def as_uri(self):
		"""As URI
		Represent the path as a "file" URI.

		:return bool: A string representing the supposedly "file URI" for this path.
		"""
		
		raise NotImplementedError('as_uri')
	
	## Expanding and resolving paths ##
	
	@classmethod
	@abstractmethod
	def home(cls):
		"""User home
		Resolves the user’s home directory path. If the home directory can’t be resolved, RuntimeError is raised.
		
		:return type(cls): A new instance of this type pointing to the current user's home directory
		"""
		
		raise NotImplementedError('home')
	
	@abstractmethod
	def expanduser(self):
		"""Expand user
		Resolve the "~" and "~user" constructs. If a home directory can’t be resolved, RuntimeError is raised.
		
		:return type(cls): A new instance of this type with the user's home directory expanded
		"""
		
		raise NotImplementedError('expanduser')
	
	@classmethod
	@abstractmethod
	def cwd(cls):
		"""Current working directory
		Resolve the current working directory.
		
		:return type(cls): A new instance of this type pointing to the current working directory
		"""
		
		raise NotImplementedError('cwd')
	
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
	
	## Querying file type and status ##

	@abstractmethod
	def stat(self, *, follow_symlinks=True):
		"""Return the result of the stat() system call on this path, like os.stat() does.
		"""

		raise NotImplementedError('stat')

	@abstractmethod
	def lstat(self):
		"""
		Like stat(), except if the path points to a symlink, the symlink's status information is returned, rather than its target's.
		"""

		return self.stat(follow_symlinks=False)

	@abstractmethod
	def exists(self, *, follow_symlinks=True):
		""" Whether this path exists.
		This method normally follows symlinks; to check whether a symlink exists, add the argument follow_symlinks=False.
		"""

		raise NotImplementedError('exists')

	@abstractmethod
	def is_file(self, follow_symlinks=True):
		"""Whether this path is a regular file (also True for symlinks pointing to regular files).
		"""

		raise NotImplementedError('is_file')

	@abstractmethod
	def is_dir(self, follow_symlinks=True):
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
	def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
		"""Open the file pointed to by this path and return a file object, as the built-in open() function does.
		"""

		raise NotImplementedError('open')

	def read_text(self, encoding=None, errors=None, newline=None):
		"""
		Open the file in text mode, read it, and close the file.
		"""

		encoding = io_text_encoding(encoding)
		with self.open(mode='r', encoding=encoding, errors=errors, newline=newline) as f:
			return f.read()

	def read_bytes(self):
		"""
		Open the file in bytes mode, read it, and close the file.
		"""

		with self.open(mode='rb') as f:
			return f.read()

	def write_text(self, data, encoding=None, errors=None, newline=None):
		"""
		Open the file in text mode, write to it, and close the file.
		"""

		if not isinstance(data, str):
			raise TypeError('data must be str, not %s' % data.__class__.__name__)
		encoding = io_text_encoding(encoding)
		with self.open(mode='w', encoding=encoding, errors=errors, newline=newline) as f:
			return f.write(data)

	def write_bytes(self, data):
		"""
		Open the file in bytes mode, write to it, and close the file.
		"""

		view = memoryview(data)
		with self.open(mode='wb') as f:
			return f.write(view)

	## Reading directories ##

	@abstractmethod
	def iterdir(self):
		"""Yield path objects of the directory contents.
		The children are yielded in arbitrary order, and the special entries '.' and '..' are not included.
		"""

		raise NotImplementedError('iterdir')

	@abstractmethod
	def glob(self, pattern, *, case_sensitive=None, recurse_symlinks=False):
		"""Iterate over this subtree and yield all existing files (of any kind, including directories) matching the given relative pattern.
		"""

		raise NotImplementedError('glob')

	@abstractmethod
	def rglob(self, pattern, *, case_sensitive=None, recurse_symlinks=False):
		"""Recursively yield all existing files (of any kind, including directories) matching the given relative pattern, anywhere in this subtree.
		"""

		raise NotImplementedError('rglob')

	@abstractmethod
	def walk(self, top_down=True, on_error=None, follow_symlinks=False):
		"""Walk the directory tree from this directory, similar to os.walk().
		"""

		raise NotImplementedError('walk')

	## Creating files and directories ##

	@abstractmethod
	def touch(self, mode=0o666, exist_ok=True):
		"""Create this file with the given access mode, if it doesn't exist.
		"""

		raise NotImplementedError('touch')

	@abstractmethod
	def mkdir(self, mode=0o777, parents=False, exist_ok=False):
		"""Create a new directory at this given path.
		"""

		raise NotImplementedError('mkdir')

	@abstractmethod
	def symlink_to(self, target, target_is_directory=False):
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
	def unlink(self, missing_ok=False):
		"""Remove this file or symbolic link.
		If the path points to a directory, use Path.rmdir() instead. If missing_ok is false (the default), FileNotFoundError is raised if the path does not exist. If missing_ok is true, FileNotFoundError exceptions will be ignored (same behavior as the POSIX rm -f command).
		"""

		raise NotImplementedError('unlink')

	@abstractmethod
	def rmdir(self):
		"""Remove this directory. The directory must be empty.
		"""

		raise NotImplementedError('rmdir')

	## Permissions and ownership ##
	
	@abstractmethod
	def owner(self, *, follow_symlinks=True):
		"""Return the name of the user owning the file. KeyError is raised if the file’s uid isn’t found in the system database.
		"""
		
		raise NotImplementedError('owner')
	
	@abstractmethod
	def group(self, *, follow_symlinks=True):
		"""Return the name of the group owning the file. KeyError is raised if the file’s gid isn’t found in the system database.
		"""
		
		raise NotImplementedError('group')

	@abstractmethod
	def chmod(self, mode, *, follow_symlinks=True):
		"""Change the file mode and permissions
		This method normally follows symlinks. Some Unix flavours support changing permissions on the symlink itself; on these platforms you may add the argument follow_symlinks = False, or use lchmod().
		"""

		raise NotImplementedError('chmod')

	def lchmod(self, mode):
		"""Change the file or symlink mode and permissions
		Like chmod(), except if the path points to a symlink, the symlink's permissions are changed, rather than its target's.
		"""

		self.chmod(mode, follow_symlinks=False)
