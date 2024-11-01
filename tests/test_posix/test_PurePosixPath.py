#!python
"""
Testing the posix.PurePosixPath class magic methods
"""

from unittest import TestCase

from pathlib_.posix import PurePosixPath


class PurePosixPathInsaneVersion(PurePosixPath):
	"""PurePosixPath
	This version matches the behavior of the one upstream. This allows to check against upstream tests.
	"""
	
	JOINPATH_INSANE_BEHAVIOR = True


class TestNew(TestCase):
	"""
	Testing the posix.PurePosixPath.__new__ class method
	"""
	
	@classmethod
	def setUpClass(cls):
		"""
		Initial values
		"""
		
		cls.cls = PurePosixPathInsaneVersion

	def test_constructor_common(self):
		"""
		Running posix.PurePosixPath.__new__ through upstream tests
		"""
		
		P = self.cls
		p = P('a')
		self.assertIsInstance(p, P)
		P('a', 'b', 'c')
		P('/a', 'b', 'c')
		P('a/b/c')
		P('/a/b/c')
	
	def test_div_common(self):
		"""
		Running posix.PurePosixPath.__truediv__ through upstream tests
		"""
		
		# Basically the same as joinpath().
		P = self.cls
		p = P('a/b')
		pp = p / 'c'
		self.assertEqual(pp, P('a/b/c'))
		self.assertIs(type(pp), type(p))
		pp = p / 'c/d'
		self.assertEqual(pp, P('a/b/c/d'))
		pp = p / 'c' / 'd'
		self.assertEqual(pp, P('a/b/c/d'))
		pp = 'c' / p / 'd'
		self.assertEqual(pp, P('c/a/b/d'))
		pp = p / '/c'
		self.assertEqual(pp, P('/c'))
	
	def test_div_posix(self):
		"""
		Running posix.PurePosixPath.__truediv__ through upstream tests (POSIX)
		"""
		
		# Basically the same as joinpath().
		P = self.cls
		p = P('//a')
		pp = p / 'b'
		self.assertEqual(pp, P('//a/b'))
		pp = P('/a') / '//c'
		self.assertEqual(pp, P('//c'))
		pp = P('//a') / '/c'
		self.assertEqual(pp, P('/c'))
	
	def _check_str(self, expected, args):
		p = self.cls(*args)
		self.assertEqual(str(p), expected.replace('/', self.cls.SEPARATOR))
	
	def test_str_common(self):
		"""
		Running posix.PurePosixPath.__str__ through upstream tests
		"""
		
		# Canonicalized paths roundtrip.
		for pathstr in ('a', 'a/b', 'a/b/c', '/', '/a/b', '/a/b/c'):
			self._check_str(pathstr, (pathstr,))
		# Other tests for str() are in test_equivalences().
	
	def test_parts_common(self):
		"""
		Running posix.PurePosixPath.parts through upstream tests
		"""
		
		# `parts` returns a tuple.
		sep = self.cls.SEPARATOR
		P = self.cls
		p = P('a/b')
		parts = p.parts
		self.assertEqual(parts, ('a', 'b'))
		# When the path is absolute, the anchor is a separate part.
		p = P('/a/b')
		parts = p.parts
		self.assertEqual(parts, (sep, 'a', 'b'))
	
	def test_parent_common(self):
		"""
		Running posix.PurePosixPath.parent through upstream tests
		"""
		
		# Relative
		P = self.cls
		p = P('a/b/c')
		self.assertEqual(p.parent, P('a/b'))
		self.assertEqual(p.parent.parent, P('a'))
		self.assertEqual(p.parent.parent.parent, P(''))
		self.assertEqual(p.parent.parent.parent.parent, P(''))
		# Anchored
		p = P('/a/b/c')
		self.assertEqual(p.parent, P('/a/b'))
		self.assertEqual(p.parent.parent, P('/a'))
		self.assertEqual(p.parent.parent.parent, P('/'))
		self.assertEqual(p.parent.parent.parent.parent, P('/'))
	
	def test_parents_common(self):
		"""
		Running posix.PurePosixPath.parents through upstream tests
		"""
		
		# Relative
		P = self.cls
		p = P('a/b/c')
		par = p.parents
		self.assertEqual(len(par), 3)
		self.assertEqual(par[0], P('a/b'))
		self.assertEqual(par[1], P('a'))
		self.assertEqual(par[2], P(''))
		self.assertEqual(par[-1], P(''))
		self.assertEqual(par[-2], P('a'))
		self.assertEqual(par[-3], P('a/b'))
		self.assertEqual(par[0:1], (P('a/b'),))
		self.assertEqual(par[:2], (P('a/b'), P('a')))
		self.assertEqual(par[:-1], (P('a/b'), P('a')))
		self.assertEqual(par[1:], (P('a'), P('')))
		self.assertEqual(par[::2], (P('a/b'), P('')))
		self.assertEqual(par[::-1], (P(''), P('a'), P('a/b')))
		self.assertEqual(list(par), [P('a/b'), P('a'), P('')])
		with self.assertRaises(IndexError):
			par[-4]
		with self.assertRaises(IndexError):
			par[3]
		with self.assertRaises(TypeError):
			par[0] = p
		# Anchored
		p = P('/a/b/c')
		par = p.parents
		self.assertEqual(len(par), 3)
		self.assertEqual(par[0], P('/a/b'))
		self.assertEqual(par[1], P('/a'))
		self.assertEqual(par[2], P('/'))
		self.assertEqual(par[-1], P('/'))
		self.assertEqual(par[-2], P('/a'))
		self.assertEqual(par[-3], P('/a/b'))
		self.assertEqual(par[0:1], (P('/a/b'),))
		self.assertEqual(par[:2], (P('/a/b'), P('/a')))
		self.assertEqual(par[:-1], (P('/a/b'), P('/a')))
		self.assertEqual(par[1:], (P('/a'), P('/')))
		self.assertEqual(par[::2], (P('/a/b'), P('/')))
		self.assertEqual(par[::-1], (P('/'), P('/a'), P('/a/b')))
		self.assertEqual(list(par), [P('/a/b'), P('/a'), P('/')])
		with self.assertRaises(IndexError):
			par[-4]
		with self.assertRaises(IndexError):
			par[3]
	
	def test_drive_common(self):
		"""
		Running posix.PurePosixPath.drive through upstream tests
		"""
		
		P = self.cls
		self.assertEqual(P('a/b').drive, '')
		self.assertEqual(P('/a/b').drive, '')
		self.assertEqual(P('').drive, '')
	
	def test_root_common(self):
		"""
		Running posix.PurePosixPath.root through upstream tests
		"""
		
		P = self.cls
		sep = self.cls.SEPARATOR
		self.assertEqual(P('').root, '')
		self.assertEqual(P('a/b').root, '')
		self.assertEqual(P('/').root, sep)
		self.assertEqual(P('/a/b').root, sep)
	
	def test_root_posix(self):
		"""
		Running posix.PurePosixPath.root through upstream tests (POSIX)
		"""
		
		P = self.cls
		self.assertEqual(P('/a/b').root, '/')
		# POSIX special case for two leading slashes.
		self.assertEqual(P('//a/b').root, '//')
	
	def test_anchor_common(self):
		"""
		Running posix.PurePosixPath.anchor through upstream tests
		"""
		
		P = self.cls
		sep = self.cls.SEPARATOR
		self.assertEqual(P('').anchor, '')
		self.assertEqual(P('a/b').anchor, '')
		self.assertEqual(P('/').anchor, sep)
		self.assertEqual(P('/a/b').anchor, sep)
	
	def test_name_empty(self):
		"""
		Running posix.PurePosixPath.name through upstream tests (empty)
		"""
		
		P = self.cls
		self.assertEqual(P('').name, '')
		self.assertEqual(P('.').name, '.')
		self.assertEqual(P('/a/b/.').name, '.')
	
	def test_name_common(self):
		"""
		Running posix.PurePosixPath.name through upstream tests
		"""
		
		P = self.cls
		self.assertEqual(P('/').name, '')
		self.assertEqual(P('a/b').name, 'b')
		self.assertEqual(P('/a/b').name, 'b')
		self.assertEqual(P('a/b.py').name, 'b.py')
		self.assertEqual(P('/a/b.py').name, 'b.py')
	
	def test_suffix_common(self):
		"""
		Running posix.PurePosixPath.suffix through upstream tests
		"""

		P = self.cls
		self.assertEqual(P('').suffix, '')
		self.assertEqual(P('.').suffix, '')
		self.assertEqual(P('..').suffix, '')
		self.assertEqual(P('/').suffix, '')
		self.assertEqual(P('a/b').suffix, '')
		self.assertEqual(P('/a/b').suffix, '')
		self.assertEqual(P('/a/b/.').suffix, '')
		self.assertEqual(P('a/b.py').suffix, '.py')
		self.assertEqual(P('/a/b.py').suffix, '.py')
		self.assertEqual(P('a/.hgrc').suffix, '')
		self.assertEqual(P('/a/.hgrc').suffix, '')
		self.assertEqual(P('a/.hg.rc').suffix, '.rc')
		self.assertEqual(P('/a/.hg.rc').suffix, '.rc')
		self.assertEqual(P('a/b.tar.gz').suffix, '.gz')
		self.assertEqual(P('/a/b.tar.gz').suffix, '.gz')
		# self.assertEqual(P('a/trailing.dot.').suffix, '.') # This should be failing upstream
		self.assertEqual(P('a/trailing.dot.').suffix, '')
		# self.assertEqual(P('/a/trailing.dot.').suffix, '.') # This should be failing upstream
		self.assertEqual(P('/a/trailing.dot.').suffix, '')
		# self.assertEqual(P('a/..d.o.t..').suffix, '.') # This should be failing upstream
		self.assertEqual(P('a/..d.o.t..').suffix, '')
		self.assertEqual(P('a/inn.er..dots').suffix, '.dots')
		self.assertEqual(P('photo').suffix, '')
		self.assertEqual(P('photo.jpg').suffix, '.jpg')
	
	def test_suffixes_common(self):
		"""
		Running posix.PurePosixPath.suffixes through upstream tests
		"""
		
		P = self.cls
		self.assertEqual(P('').suffixes, [])
		self.assertEqual(P('.').suffixes, [])
		self.assertEqual(P('/').suffixes, [])
		self.assertEqual(P('a/b').suffixes, [])
		self.assertEqual(P('/a/b').suffixes, [])
		self.assertEqual(P('/a/b/.').suffixes, [])
		self.assertEqual(P('a/b.py').suffixes, ['.py'])
		self.assertEqual(P('/a/b.py').suffixes, ['.py'])
		self.assertEqual(P('a/.hgrc').suffixes, [])
		self.assertEqual(P('/a/.hgrc').suffixes, [])
		self.assertEqual(P('a/.hg.rc').suffixes, ['.rc'])
		self.assertEqual(P('/a/.hg.rc').suffixes, ['.rc'])
		self.assertEqual(P('a/b.tar.gz').suffixes, ['.tar', '.gz'])
		self.assertEqual(P('/a/b.tar.gz').suffixes, ['.tar', '.gz'])
		# self.assertEqual(P('a/trailing.dot.').suffixes, ['.dot', '.']) # This should be failing upstream
		self.assertEqual(P('a/trailing.dot.').suffixes, [])
		# self.assertEqual(P('/a/trailing.dot.').suffixes, ['.dot', '.']) # This should be failing upstream
		self.assertEqual(P('/a/trailing.dot.').suffixes, [])
		# self.assertEqual(P('a/..d.o.t..').suffixes, ['.o', '.t', '.', '.']) # This should be failing upstream
		self.assertEqual(P('a/..d.o.t..').suffixes, [])
		self.assertEqual(P('a/inn.er..dots').suffixes, ['.er', '.', '.dots'])
		self.assertEqual(P('photo').suffixes, [])
		self.assertEqual(P('photo.jpg').suffixes, ['.jpg'])
	
	def test_stem_empty(self):
		"""
		Running posix.PurePosixPath.stem through upstream tests (empty)
		"""
		
		P = self.cls
		self.assertEqual(P('').stem, '')
		self.assertEqual(P('.').stem, '.')
	
	def test_stem_common(self):
		"""
		Running posix.PurePosixPath.stem through upstream tests
		"""
		
		P = self.cls
		self.assertEqual(P('..').stem, '..')
		self.assertEqual(P('/').stem, '')
		self.assertEqual(P('a/b').stem, 'b')
		self.assertEqual(P('a/b.py').stem, 'b')
		self.assertEqual(P('a/.hgrc').stem, '.hgrc')
		self.assertEqual(P('a/.hg.rc').stem, '.hg')
		self.assertEqual(P('a/b.tar.gz').stem, 'b.tar')
		# self.assertEqual(P('a/trailing.dot.').stem, 'trailing.dot') # This should be failing upstream
		self.assertEqual(P('a/trailing.dot.').stem, 'trailing.dot.')
		# self.assertEqual(P('a/..d.o.t..').stem, '..d.o.t.') # This should be failing upstream
		self.assertEqual(P('a/..d.o.t..').stem, '..d.o.t..')
		self.assertEqual(P('a/inn.er..dots').stem, 'inn.er.')
		self.assertEqual(P('photo').stem, 'photo')
		self.assertEqual(P('photo.jpg').stem, 'photo')