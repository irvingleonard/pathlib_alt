#!python
"""
Testing the posix.PurePosixPath.relative_to method
"""

from unittest import TestCase

from pathlib_ import PurePosixPath

class TestPurePosixPathRelativeTo(TestCase):
	"""
	Tests for the PurePosixPath.relative_to method
	"""
	
	@classmethod
	def setUpClass(cls):
		"""
		Initial values
		"""
		
		cls.cls = PurePosixPath
	
	def test_with_once_removed_sibling(self):
		"""
		Test "PurePosixPath.relative_to" with a once removed sibling
		"""
		
		expected_result = PurePosixPath('../../bar/baz')
		self.assertEqual(PurePosixPath('/foo/bar/baz').relative_to('/foo/spam/lobster', walk_up=True), expected_result)
	
	def test_with_relative_sibling(self):
		"""
		Test "PurePosixPath.relative_to" with a once removed sibling
		"""
		
		expected_result = PurePosixPath('../../../foo/bar/baz')
		self.assertEqual(PurePosixPath('foo/bar/baz').relative_to('spam/spam/lobster', walk_up=True), expected_result)
	
	def test_relative_to_common(self):
		P = self.cls
		p = P('a/b')
		self.assertRaises(TypeError, p.relative_to)
		self.assertRaises(TypeError, p.relative_to, b'a')
		self.assertEqual(p.relative_to(P('')), P('a/b'))
		self.assertEqual(p.relative_to(''), P('a/b'))
		self.assertEqual(p.relative_to(P('a')), P('b'))
		self.assertEqual(p.relative_to('a'), P('b'))
		# self.assertEqual(p.relative_to('a/'), P('b')) # ToDo: Fix
		self.assertEqual(p.relative_to(P('a/b')), P(''))
		self.assertEqual(p.relative_to('a/b'), P(''))
		self.assertEqual(p.relative_to(P(''), walk_up=True), P('a/b'))
		self.assertEqual(p.relative_to('', walk_up=True), P('a/b'))
		self.assertEqual(p.relative_to(P('a'), walk_up=True), P('b'))
		self.assertEqual(p.relative_to('a', walk_up=True), P('b'))
		# self.assertEqual(p.relative_to('a/', walk_up=True), P('b')) # ToDo: Fix
		self.assertEqual(p.relative_to(P('a/b'), walk_up=True), P(''))
		self.assertEqual(p.relative_to('a/b', walk_up=True), P(''))
		self.assertEqual(p.relative_to(P('a/c'), walk_up=True), P('../b'))
		self.assertEqual(p.relative_to('a/c', walk_up=True), P('../b'))
		# self.assertEqual(p.relative_to(P('a/b/c'), walk_up=True), P('..')) # ToDo: Fix
		# self.assertEqual(p.relative_to('a/b/c', walk_up=True), P('..')) # ToDo: Fix
		self.assertEqual(p.relative_to(P('c'), walk_up=True), P('../a/b'))
		self.assertEqual(p.relative_to('c', walk_up=True), P('../a/b'))
		# Unrelated paths.
		self.assertRaises(ValueError, p.relative_to, P('c'))
		self.assertRaises(ValueError, p.relative_to, P('a/b/c'))
		self.assertRaises(ValueError, p.relative_to, P('a/c'))
		self.assertRaises(ValueError, p.relative_to, P('/a'))
		self.assertRaises(ValueError, p.relative_to, P("../a"))
		self.assertRaises(ValueError, p.relative_to, P("a/.."))
		self.assertRaises(ValueError, p.relative_to, P("/a/.."))
		self.assertRaises(ValueError, p.relative_to, P('/'), walk_up=True)
		self.assertRaises(ValueError, p.relative_to, P('/a'), walk_up=True)
		# self.assertRaises(ValueError, p.relative_to, P("../a"), walk_up=True) # ToDo: Fix
		# self.assertRaises(ValueError, p.relative_to, P("a/.."), walk_up=True) # ToDo: Fix
		self.assertRaises(ValueError, p.relative_to, P("/a/.."), walk_up=True)
		p = P('/a/b')
		self.assertEqual(p.relative_to(P('/')), P('a/b'))
		self.assertEqual(p.relative_to('/'), P('a/b'))
		self.assertEqual(p.relative_to(P('/a')), P('b'))
		self.assertEqual(p.relative_to('/a'), P('b'))
		# self.assertEqual(p.relative_to('/a/'), P('b')) # ToDo: Fix
		self.assertEqual(p.relative_to(P('/a/b')), P(''))
		self.assertEqual(p.relative_to('/a/b'), P(''))
		self.assertEqual(p.relative_to(P('/'), walk_up=True), P('a/b'))
		self.assertEqual(p.relative_to('/', walk_up=True), P('a/b'))
		self.assertEqual(p.relative_to(P('/a'), walk_up=True), P('b'))
		self.assertEqual(p.relative_to('/a', walk_up=True), P('b'))
		# self.assertEqual(p.relative_to('/a/', walk_up=True), P('b')) # ToDo: Fix
		self.assertEqual(p.relative_to(P('/a/b'), walk_up=True), P(''))
		self.assertEqual(p.relative_to('/a/b', walk_up=True), P(''))
		self.assertEqual(p.relative_to(P('/a/c'), walk_up=True), P('../b'))
		self.assertEqual(p.relative_to('/a/c', walk_up=True), P('../b'))
		# self.assertEqual(p.relative_to(P('/a/b/c'), walk_up=True), P('..')) # ToDo: Fix
		# self.assertEqual(p.relative_to('/a/b/c', walk_up=True), P('..')) # ToDo: Fix
		self.assertEqual(p.relative_to(P('/c'), walk_up=True), P('../a/b'))
		self.assertEqual(p.relative_to('/c', walk_up=True), P('../a/b'))
		# Unrelated paths.
		self.assertRaises(ValueError, p.relative_to, P('/c'))
		self.assertRaises(ValueError, p.relative_to, P('/a/b/c'))
		self.assertRaises(ValueError, p.relative_to, P('/a/c'))
		self.assertRaises(ValueError, p.relative_to, P(''))
		self.assertRaises(ValueError, p.relative_to, '')
		self.assertRaises(ValueError, p.relative_to, P('a'))
		self.assertRaises(ValueError, p.relative_to, P("../a"))
		self.assertRaises(ValueError, p.relative_to, P("a/.."))
		self.assertRaises(ValueError, p.relative_to, P("/a/.."))
		self.assertRaises(ValueError, p.relative_to, P(''), walk_up=True)
		self.assertRaises(ValueError, p.relative_to, P('a'), walk_up=True)
		self.assertRaises(ValueError, p.relative_to, P("../a"), walk_up=True)
		self.assertRaises(ValueError, p.relative_to, P("a/.."), walk_up=True)
		# self.assertRaises(ValueError, p.relative_to, P("/a/.."), walk_up=True) # ToDo: Fix