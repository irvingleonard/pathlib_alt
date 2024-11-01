#!python
"""
Testing the posix.PurePosixPath.match class method and relatives
"""

from unittest import TestCase

from pathlib_.posix import PurePosixPath

class TestMatch(TestCase):
	"""
	Testing the posix.PurePosixPath.match class method
	"""
	
	@classmethod
	def setUpClass(cls):
		"""
		Initial values
		"""
		
		cls.cls = PurePosixPath
	
	def test_match_empty(self):
		"""
		Running posix.PurePosixPath.match through upstream tests (empty)
		"""
		
		P = self.cls
		self.assertRaises(ValueError, P('a').match, '')
	
	def test_match_common(self):
		"""
		Running posix.PurePosixPath.match through upstream tests
		"""
		
		P = self.cls
		# Simple relative pattern.
		self.assertTrue(P('b.py').match('b.py'))
		self.assertTrue(P('a/b.py').match('b.py'))
		self.assertTrue(P('/a/b.py').match('b.py'))
		self.assertFalse(P('a.py').match('b.py'))
		self.assertFalse(P('b/py').match('b.py'))
		self.assertFalse(P('/a.py').match('b.py'))
		self.assertFalse(P('b.py/c').match('b.py'))
		# Wildcard relative pattern.
		self.assertTrue(P('b.py').match('*.py'))
		self.assertTrue(P('a/b.py').match('*.py'))
		self.assertTrue(P('/a/b.py').match('*.py'))
		self.assertFalse(P('b.pyc').match('*.py'))
		self.assertFalse(P('b./py').match('*.py'))
		self.assertFalse(P('b.py/c').match('*.py'))
		# Multi-part relative pattern.
		self.assertTrue(P('ab/c.py').match('a*/*.py'))
		self.assertTrue(P('/d/ab/c.py').match('a*/*.py'))
		self.assertFalse(P('a.py').match('a*/*.py'))
		self.assertFalse(P('/dab/c.py').match('a*/*.py'))
		self.assertFalse(P('ab/c.py/d').match('a*/*.py'))
		# Absolute pattern.
		self.assertTrue(P('/b.py').match('/*.py'))
		self.assertFalse(P('b.py').match('/*.py'))
		self.assertFalse(P('a/b.py').match('/*.py'))
		self.assertFalse(P('/a/b.py').match('/*.py'))
		# Multi-part absolute pattern.
		self.assertTrue(P('/a/b.py').match('/a/*.py'))
		self.assertFalse(P('/ab.py').match('/a/*.py'))
		self.assertFalse(P('/a/b/c.py').match('/a/*.py'))
		# Multi-part glob-style pattern.
		self.assertFalse(P('/a/b/c.py').match('/**/*.py'))
		self.assertTrue(P('/a/b/c.py').match('/a/**/*.py'))
		# Case-sensitive flag
		self.assertFalse(P('A.py').match('a.PY', case_sensitive=True))
		self.assertTrue(P('A.py').match('a.PY', case_sensitive=False))
		self.assertFalse(P('c:/a/B.Py').match('C:/A/*.pY', case_sensitive=True))
		self.assertTrue(P('/a/b/c.py').match('/A/*/*.Py', case_sensitive=False))
		# Matching against empty path
		self.assertFalse(P('').match('*'))
		self.assertFalse(P('').match('**'))
		self.assertFalse(P('').match('**/*'))
	
	def test_match_posix(self):
		"""
		Running posix.PurePosixPath.match through upstream tests (POSIX)
		"""
		
		P = self.cls
		self.assertFalse(P('A.py').match('a.PY'))


class TestFullMatch(TestCase):
	"""
	Testing the posix.PurePosixPath.full_match class method
	"""
	
	@classmethod
	def setUpClass(cls):
		"""
		Initial values
		"""
		
		cls.cls = PurePosixPath
	
	def test_upstream_common(self):
		"""
		Running posix.PurePosixPath.full_match through upstream tests
		"""
		
		P = self.cls
		# Simple relative pattern.
		self.assertTrue(P('b.py').full_match('b.py'))
		self.assertFalse(P('a/b.py').full_match('b.py'))
		self.assertFalse(P('/a/b.py').full_match('b.py'))
		self.assertFalse(P('a.py').full_match('b.py'))
		self.assertFalse(P('b/py').full_match('b.py'))
		self.assertFalse(P('/a.py').full_match('b.py'))
		self.assertFalse(P('b.py/c').full_match('b.py'))
		# Wildcard relative pattern.
		self.assertTrue(P('b.py').full_match('*.py'))
		self.assertFalse(P('a/b.py').full_match('*.py'))
		self.assertFalse(P('/a/b.py').full_match('*.py'))
		self.assertFalse(P('b.pyc').full_match('*.py'))
		self.assertFalse(P('b./py').full_match('*.py'))
		self.assertFalse(P('b.py/c').full_match('*.py'))
		# Multi-part relative pattern.
		self.assertTrue(P('ab/c.py').full_match('a*/*.py'))
		self.assertFalse(P('/d/ab/c.py').full_match('a*/*.py'))
		self.assertFalse(P('a.py').full_match('a*/*.py'))
		self.assertFalse(P('/dab/c.py').full_match('a*/*.py'))
		self.assertFalse(P('ab/c.py/d').full_match('a*/*.py'))
		# Absolute pattern.
		self.assertTrue(P('/b.py').full_match('/*.py'))
		self.assertFalse(P('b.py').full_match('/*.py'))
		self.assertFalse(P('a/b.py').full_match('/*.py'))
		self.assertFalse(P('/a/b.py').full_match('/*.py'))
		# Multi-part absolute pattern.
		self.assertTrue(P('/a/b.py').full_match('/a/*.py'))
		self.assertFalse(P('/ab.py').full_match('/a/*.py'))
		self.assertFalse(P('/a/b/c.py').full_match('/a/*.py'))
		# Multi-part glob-style pattern.
		self.assertTrue(P('a').full_match('**'))
		self.assertTrue(P('c.py').full_match('**'))
		self.assertTrue(P('a/b/c.py').full_match('**'))
		self.assertTrue(P('/a/b/c.py').full_match('**'))
		self.assertTrue(P('/a/b/c.py').full_match('/**'))
		self.assertTrue(P('/a/b/c.py').full_match('/a/**'))
		self.assertTrue(P('/a/b/c.py').full_match('**/*.py'))
		self.assertTrue(P('/a/b/c.py').full_match('/**/*.py'))
		self.assertTrue(P('/a/b/c.py').full_match('/a/**/*.py'))
		self.assertTrue(P('/a/b/c.py').full_match('/a/b/**/*.py'))
		self.assertTrue(P('/a/b/c.py').full_match('/**/**/**/**/*.py'))
		self.assertFalse(P('c.py').full_match('**/a.py'))
		self.assertFalse(P('c.py').full_match('c/**'))
		self.assertFalse(P('a/b/c.py').full_match('**/a'))
		self.assertFalse(P('a/b/c.py').full_match('**/a/b'))
		self.assertFalse(P('a/b/c.py').full_match('**/a/b/c'))
		self.assertFalse(P('a/b/c.py').full_match('**/a/b/c.'))
		self.assertFalse(P('a/b/c.py').full_match('**/a/b/c./**'))
		self.assertFalse(P('a/b/c.py').full_match('**/a/b/c./**'))
		self.assertFalse(P('a/b/c.py').full_match('/a/b/c.py/**'))
		self.assertFalse(P('a/b/c.py').full_match('/**/a/b/c.py'))
		# Case-sensitive flag
		self.assertFalse(P('A.py').full_match('a.PY', case_sensitive=True))
		self.assertTrue(P('A.py').full_match('a.PY', case_sensitive=False))
		self.assertFalse(P('c:/a/B.Py').full_match('C:/A/*.pY', case_sensitive=True))
		self.assertTrue(P('/a/b/c.py').full_match('/A/*/*.Py', case_sensitive=False))
		# Matching against empty path
		self.assertFalse(P('').full_match('*'))
		self.assertTrue(P('').full_match('**'))
		self.assertFalse(P('').full_match('**/*'))
		# Matching with empty pattern
		self.assertTrue(P('').full_match(''))
		self.assertTrue(P('.').full_match('.'))
		self.assertFalse(P('/').full_match(''))
		self.assertFalse(P('/').full_match('.'))
		self.assertFalse(P('foo').full_match(''))
		self.assertFalse(P('foo').full_match('.'))
