#!python
"""
Testing the posix.PurePosixPath.joinpath class method
"""

from unittest import TestCase

from pathlib_.posix import PurePosixPath


class PurePosixPathInsaneVersion(PurePosixPath):
	"""PurePosixPath
	This version matches the behavior of the one upstream. This allows to check against upstream tests.
	"""
	
	JOINPATH_INSANE_BEHAVIOR = True


class TestJoinpath(TestCase):
	"""
	Testing the posix.PurePosixPath.joinpath class method
	"""
	
	@classmethod
	def setUpClass(cls):
		"""
		Initial values
		"""
		
		cls.cls = PurePosixPathInsaneVersion
	
	def test_join_common(self):
		"""
		Running posix.PurePosixPath.joinpath through upstream tests
		"""
		
		P = self.cls
		p = P('a/b')
		pp = p.joinpath('c')
		self.assertEqual(pp, P('a/b/c'))
		self.assertIs(type(pp), type(p))
		pp = p.joinpath('c', 'd')
		self.assertEqual(pp, P('a/b/c/d'))
		pp = p.joinpath('/c')
		self.assertEqual(pp, P('/c'))
	
	def test_join_posix(self):
		"""
		Running posix.PurePosixPath.joinpath through upstream tests (POSIX)
		"""
		
		P = self.cls
		p = P('//a')
		pp = p.joinpath('b')
		self.assertEqual(pp, P('//a/b'))
		pp = P('/a').joinpath('//c')
		self.assertEqual(pp, P('//c'))
		pp = P('//a').joinpath('/c')
		self.assertEqual(pp, P('/c'))
