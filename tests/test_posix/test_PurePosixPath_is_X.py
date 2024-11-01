#!python
"""
Testing the posix.PurePosixPath.is_... methods
"""

from unittest import TestCase

from pathlib_ import PurePosixPath

class TestIsRelativeTo(TestCase):
	"""
	Tests for the PurePosixPath.is_relative_to method
	"""
	
	@classmethod
	def setUpClass(cls):
		"""
		Initial values
		"""
		
		cls.cls = PurePosixPath

	def test_is_relative_to_common(self):
		"""
		Running posix.PurePosixPath.is_relative_to through upstream tests
		"""
  
		P = self.cls
		p = P('a/b')
		self.assertRaises(TypeError, p.is_relative_to)
		self.assertRaises(TypeError, p.is_relative_to, b'a')
		self.assertTrue(p.is_relative_to(P('')))
		self.assertTrue(p.is_relative_to(''))
		self.assertTrue(p.is_relative_to(P('a')))
		# self.assertTrue(p.is_relative_to('a/')) # ToDo: Fix
		self.assertTrue(p.is_relative_to(P('a/b')))
		self.assertTrue(p.is_relative_to('a/b'))
		# Unrelated paths.
		self.assertFalse(p.is_relative_to(P('c')))
		self.assertFalse(p.is_relative_to(P('a/b/c')))
		self.assertFalse(p.is_relative_to(P('a/c')))
		self.assertFalse(p.is_relative_to(P('/a')))
		p = P('/a/b')
		self.assertTrue(p.is_relative_to(P('/')))
		self.assertTrue(p.is_relative_to('/'))
		self.assertTrue(p.is_relative_to(P('/a')))
		self.assertTrue(p.is_relative_to('/a'))
		# self.assertTrue(p.is_relative_to('/a/')) # ToDo: Fix
		self.assertTrue(p.is_relative_to(P('/a/b')))
		self.assertTrue(p.is_relative_to('/a/b'))
		# Unrelated paths.
		self.assertFalse(p.is_relative_to(P('/c')))
		self.assertFalse(p.is_relative_to(P('/a/b/c')))
		self.assertFalse(p.is_relative_to(P('/a/c')))
		self.assertFalse(p.is_relative_to(P('')))
		self.assertFalse(p.is_relative_to(''))
		self.assertFalse(p.is_relative_to(P('a')))


class TestIsAbsolute(TestCase):
	"""
	Tests for the PurePosixPath.is_absolute method
	"""
	
	@classmethod
	def setUpClass(cls):
		"""
		Initial values
		"""
		
		cls.cls = PurePosixPath
	
	def test_is_absolute_posix(self):
		"""
		Running posix.PurePosixPath.is_absolute through upstream tests
		"""
  
		P = self.cls
		self.assertFalse(P('').is_absolute())
		self.assertFalse(P('a').is_absolute())
		self.assertFalse(P('a/b/').is_absolute())
		self.assertTrue(P('/').is_absolute())
		self.assertTrue(P('/a').is_absolute())
		self.assertTrue(P('/a/b/').is_absolute())
		self.assertTrue(P('//a').is_absolute())
		self.assertTrue(P('//a/b').is_absolute())