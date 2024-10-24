#!python
'''A reimplementation of the python standard library's pathlib.
The original pathlib module seems to revolve around the idea that the path is a string, and then it can't decide if the paths are inmutable or not. This module works with a different paradigm: a path is a sequence of individual components divided by a "separator" and such sequence is inmutable.

This submodule implements methods of the base protocol to be used with a local filesystem.
'''

import io
import logging
import os
import stat

from ._base import BasePath, __version__

LOGGER = logging.getLogger(__name__)


class BaseOSPath(BasePath):
	'''Further implementation of BasePath for local filesystems
	Extends the BasePath by adding method implementations that are portable between local filesystem (POSIX & Windows)
	'''

	_pathmod = None

	@classmethod
	def _get_os_attr(cls, function, *args, call_it = True, **kwargs):
		'''
		Forward a call to a function in the os module
		'''

		if hasattr(os, function):
			if call_it:
				return getattr(os, function)(*args, **kwargs)
			else:
				return getattr(os, function)
		else:
			raise NotImplementedError('The current "os" module does not contain the required function: {}'.format(function))
	
	@classmethod    
	def _get_stat_attr(cls, function, *args, call_it = True, **kwargs):
		'''
		Forward a call to a function in the stat module
		'''

		if hasattr(stat, function):
			if call_it:
				return getattr(stat, function)(*args, **kwargs)
			else:
				return getattr(stat, function)
		else:
			raise NotImplementedError('The current "stat" module does not contain the required function: {}'.format(function))


	def _get_pathmod_attr(self, function, *args, call_it = True, **kwargs):
		'''
		Forward a call to a function in the current "pathmod" module
		'''
		
		pass
	
	## Querying file type and status ##

	def stat(self, *ignoring, follow_symlinks = True):
		'''Return the result of the stat() system call on this path, like os.stat() does.
		'''

		return self._get_os_attr('stat', self, follow_symlinks = follow_symlinks)

	def exists(self, *, follow_symlinks = True):
		''' Whether this path exists.
		This method normally follows symlinks; to check whether a symlink exists, add the argument follow_symlinks=False.
		'''

		try:
			self.stat(follow_symlinks = follow_symlinks)
		except (OSError, ValueError):
			return False
		return True

	def is_file(self):
		'''Whether this path is a regular file (also True for symlinks pointing to regular files).
		'''

		try:
			return self._get_stat_attr('S_ISREG', self.stat(follow_symlinks = follow_symlinks).st_mode)
		except (OSError, ValueError):
			return False

	def is_dir(self):
		'''Whether this path is a directory.
		'''

		try:
			return self._get_stat_attr('S_ISDIR', self.stat(follow_symlinks = follow_symlinks).st_mode)
		except (OSError, ValueError):
			return False

	def is_symlink(self):
		'''Whether this path is a symbolic link.
		'''

		try:
			return self._get_stat_attr('S_ISLNK', self.stat(follow_symlinks = follow_symlinks).st_mode)
		except (OSError, ValueError):
			return False

	def is_mount(self):
		'''Check if this path is a mount point
		'''

		# Need to exist and be a dir
		if not self.exists() or not self.is_dir():
			return False

		try:
			parent_dev = self.parent.stat().st_dev
		except OSError:
			return False

		dev = self.stat().st_dev
		if dev != parent_dev:
			return True
		ino = self.stat().st_ino
		parent_ino = self.parent.stat().st_ino
		return ino == parent_ino

	def is_socket(self):
		'''Whether this path is a socket.
		'''

		try:
			return self._get_stat_attr('S_ISSOCK', self.stat(follow_symlinks = follow_symlinks).st_mode)
		except (OSError, ValueError):
			return False

	def is_fifo(self):
		'''Whether this path is a FIFO.
		'''

		try:
			return self._get_stat_attr('S_ISFIFO', self.stat(follow_symlinks = follow_symlinks).st_mode)
		except (OSError, ValueError):
			return False

	def is_block_device(self):
		'''Whether this path is a block device.
		'''

		try:
			return self._get_stat_attr('S_ISBLK', self.stat(follow_symlinks = follow_symlinks).st_mode)
		except (OSError, ValueError):
			return False

	def is_char_device(self):
		'''Whether this path is a character device.
		'''

		try:
			return self._get_stat_attr('S_ISCHR', self.stat(follow_symlinks = follow_symlinks).st_mode)
		except (OSError, ValueError):
			return False

	def samefile(self, other_path):
		'''Return whether other_path is the same or not as this file (as returned by os.path.samefile()).
		'''

		other_stat = self.convert_path(other_path).stat()
		self_stat = self.stat()
		return (self_stat.st_ino == other_stat.st_ino) and (self_stat.st_dev == other_stat.st_dev)
	
	## Reading and writing files ##
	
	def open(self, mode = 'r', buffering = -1, encoding = None, errors = None, newline = None):
		'''
		Open the file pointed by this path and return a file object, as the built-in open() function does.
		'''

		if "b" not in mode:
			encoding = io.text_encoding(encoding)
		return io.open(self, mode, buffering, encoding, errors, newline)
	
	## Reading directories ##
	
	@abc.abstractmethod
	def iterdir(self):
		'''Yield path objects of the directory contents.
		The children are yielded in arbitrary order, and the special entries '.' and '..' are not included.
		'''

		raise NotImplementedError('iterdir')

	@abc.abstractmethod
	def glob(self, pattern, *, case_sensitive = None):
		'''Iterate over this subtree and yield all existing files (of any kind, including directories) matching the given relative pattern.
		'''

		raise NotImplementedError('glob')

	@abc.abstractmethod
	def rglob(self, pattern, *, case_sensitive = None):
		'''Recursively yield all existing files (of any kind, including directories) matching the given relative pattern, anywhere in this subtree.
		'''

		raise NotImplementedError('rglob')

	@abc.abstractmethod
	def walk(self, top_down = True, on_error = None, follow_symlinks = False):
		'''Walk the directory tree from this directory, similar to os.walk().
		'''

		raise NotImplementedError('walk')
		
	## Creating files and directories ##

	def touch(self, mode = 0o666, exist_ok = True):
		'''Create this file with the given access mode, if it doesn't exist.
		'''

		if exist_ok:
			# First try to bump modification time
			# Implementation note: GNU touch uses the UTIME_NOW option of
			# the utimensat() / futimens() functions.
			try:
				self._get_os_attr('utime', self, None)
			except OSError:
				# Avoid exception chaining
				pass
			else:
				return
		flags = self._get_os_attr('O_CREAT', call_it = False) | self._get_os_attr('O_WRONLY', call_it = False)
		if not exist_ok:
			flags |= self._get_os_attr('O_EXCL', call_it = False)
		fd = self._get_os_attr('open', self, flags, mode)
		self._get_os_attr('close', fd)

	def mkdir(self, mode = 0o777, parents = False, exist_ok = False):
		'''Create a new directory at this given path.
		'''

		try:
			self._get_os_attr('mkdir', self, mode)
		except FileNotFoundError:
			if not parents or self.parent == self:
				raise
			self.parent.mkdir(parents = True, exist_ok = True)
			self.mkdir(mode, parents = False, exist_ok = exist_ok)
		except OSError:
			# Cannot rely on checking for EEXIST, since the operating system
			# could give priority to other errors like EACCES or EROFS
			if not exist_ok or not self.is_dir():
				raise

	def symlink_to(self, target, target_is_directory = False):
		'''Make this path a symlink pointing to the target path. Note the order of arguments (link, target) is the reverse of os.symlink.
		'''

		self._get_os_attr('symlink', target, self, target_is_directory)

	def hardlink_to(self, target):
		'''Make this path a hard link pointing to the same file as *target*. Note the order of arguments (self, target) is the reverse of os.link's.
		'''

		self._get_os_attr('link', target, self)
	
	## Renaming and deleting ##

	def rename(self, target):
		'''Rename this file or directory to the given target, and return a new Path instance pointing to target.
		'''

		self._get_os_attr('rename', self, target)
		return self.convert_path(target)

	def replace(self, target):
		'''Rename this file or directory to the given target, and return a new Path instance pointing to target.
		If target points to an existing file or empty directory, it will be unconditionally replaced. The target path may be absolute or relative. Relative paths are interpreted relative to the current working directory, not the directory of the Path object.
		'''

		self._get_os_attr('replace', self, target)
		return self.convert_path(target)

	def unlink(self, missing_ok = False):
		'''Remove this file or symbolic link.
		If the path points to a directory, use Path.rmdir() instead. If missing_ok is false (the default), FileNotFoundError is raised if the path does not exist. If missing_ok is true, FileNotFoundError exceptions will be ignored (same behavior as the POSIX rm -f command).
		'''

		try:
			self._get_os_attr('unlink', self)
		except FileNotFoundError:
			if not missing_ok:
				raise

	def rmdir(self):
		'''Remove this directory. The directory must be empty.
		'''

		self._get_os_attr('rmdir', self)
	
	## Other methods ##

	@classmethod
	def cwd(cls):
		'''Return a new path pointing to the current working directory
		'''

		return cls('.').absolute()

	@classmethod
	def home(cls):
		'''
		Return a new path pointing to expanduser('~').
		'''

		return cls('~').expanduser()

	@abc.abstractmethod
	def chmod(self, mode, *ignoring, follow_symlinks = True):
		'''Change the file mode and permissions
		This method normally follows symlinks. Some Unix flavours support changing permissions on the symlink itself; on these platforms you may add the argument follow_symlinks = False, or use lchmod().
		'''

		self._get_os_attr('chmod', self, mode, follow_symlinks = follow_symlinks)

	def expanduser(self):
		'''Return a new path with expanded ~ and ~user constructs. If a home directory can’t be resolved, RuntimeError is raised.
		'''

		if (not (self.drive or self.root) and
			self._tail and self._tail[0][:1] == '~'):
			homedir = os.path.expanduser(self._tail[0])
			if homedir[:1] == "~":
				raise RuntimeError("Could not determine home directory.")
			drive, root, tail = self._parse_path(homedir)
			return self.__class__(drive = drive, root = root, tail = tail + self._tail[1:])

		return self

	@abc.abstractmethod
	def group(self):
		'''Return the name of the group owning the file. KeyError is raised if the file’s gid isn’t found in the system database.
		'''

		raise NotImplementedError('group')

	@abc.abstractmethod
	def owner(self):
		'''Return the name of the user owning the file. KeyError is raised if the file’s uid isn’t found in the system database.
		'''

		raise NotImplementedError('owner')

	@abc.abstractmethod
	def readlink(self):
		'''Return the path to which the symbolic link points
		'''

		raise NotImplementedError('readlink')

	@abc.abstractmethod
	def absolute(self):
		'''Make the path absolute, without normalization or resolving symlinks. Returns a new path object.
		'''

		raise NotImplementedError('absolute')

	@abc.abstractmethod
	def resolve(self, strict = False):
		'''Make the path absolute, resolving any symlinks. A new path object is returned.
		'''

		raise NotImplementedError('resolve')
