#!python
"""
Testing the glob_.translate function
"""

from os.path import join as os_path_join
from re import compile as re_compile
from unittest import TestCase

from pathlib_.glob_ import translate as glob_translate

class TestGlobTranslate(TestCase):
	"""
	Tests for the glob_.translate function
	"""
	
	def test_translate_matching(self):
		match = re_compile(glob_translate('*')).match
		self.assertIsNotNone(match('foo'))
		self.assertIsNotNone(match('foo.bar'))
		self.assertIsNone(match('.foo'))
		match = re_compile(glob_translate('.*')).match
		self.assertIsNotNone(match('.foo'))
		match = re_compile(glob_translate('**', recursive=True)).match
		self.assertIsNotNone(match('foo'))
		self.assertIsNone(match('.foo'))
		self.assertIsNotNone(match(os_path_join('foo', 'bar')))
		self.assertIsNone(match(os_path_join('foo', '.bar')))
		self.assertIsNone(match(os_path_join('.foo', 'bar')))
		self.assertIsNone(match(os_path_join('.foo', '.bar')))
		match = re_compile(glob_translate('**/*', recursive=True)).match
		self.assertIsNotNone(match(os_path_join('foo', 'bar')))
		self.assertIsNone(match(os_path_join('foo', '.bar')))
		self.assertIsNone(match(os_path_join('.foo', 'bar')))
		self.assertIsNone(match(os_path_join('.foo', '.bar')))
		match = re_compile(glob_translate('*/**', recursive=True)).match
		self.assertIsNotNone(match(os_path_join('foo', 'bar')))
		self.assertIsNone(match(os_path_join('foo', '.bar')))
		self.assertIsNone(match(os_path_join('.foo', 'bar')))
		self.assertIsNone(match(os_path_join('.foo', '.bar')))
		match = re_compile(glob_translate('**/.bar', recursive=True)).match
		self.assertIsNotNone(match(os_path_join('foo', '.bar')))
		self.assertIsNone(match(os_path_join('.foo', '.bar')))
		match = re_compile(glob_translate('**/*.*', recursive=True)).match
		self.assertIsNone(match(os_path_join('foo', 'bar')))
		self.assertIsNone(match(os_path_join('foo', '.bar')))
		self.assertIsNotNone(match(os_path_join('foo', 'bar.txt')))
		self.assertIsNone(match(os_path_join('foo', '.bar.txt')))
	
	def test_translate(self):
		def fn(pat):
			return glob_translate(pat, seps='/')
		
		self.assertEqual(fn('foo'), r'(?s:foo)\Z')
		self.assertEqual(fn('foo/bar'), r'(?s:foo/bar)\Z')
		self.assertEqual(fn('*'), r'(?s:[^/.][^/]*)\Z')
		self.assertEqual(fn('?'), r'(?s:(?!\.)[^/])\Z')
		self.assertEqual(fn('a*'), r'(?s:a[^/]*)\Z')
		self.assertEqual(fn('*a'), r'(?s:(?!\.)[^/]*a)\Z')
		self.assertEqual(fn('.*'), r'(?s:\.[^/]*)\Z')
		self.assertEqual(fn('?aa'), r'(?s:(?!\.)[^/]aa)\Z')
		self.assertEqual(fn('aa?'), r'(?s:aa[^/])\Z')
		self.assertEqual(fn('aa[ab]'), r'(?s:aa[ab])\Z')
		self.assertEqual(fn('**'), r'(?s:(?!\.)[^/]*)\Z')
		self.assertEqual(fn('***'), r'(?s:(?!\.)[^/]*)\Z')
		self.assertEqual(fn('a**'), r'(?s:a[^/]*)\Z')
		self.assertEqual(fn('**b'), r'(?s:(?!\.)[^/]*b)\Z')
		self.assertEqual(fn('/**/*/*.*/**'),
						 r'(?s:/(?!\.)[^/]*/[^/.][^/]*/(?!\.)[^/]*\.[^/]*/(?!\.)[^/]*)\Z')
	
	def test_translate_include_hidden(self):
		def fn(pat):
			return glob_translate(pat, include_hidden=True, seps='/')
		
		self.assertEqual(fn('foo'), r'(?s:foo)\Z')
		self.assertEqual(fn('foo/bar'), r'(?s:foo/bar)\Z')
		self.assertEqual(fn('*'), r'(?s:[^/]+)\Z')
		self.assertEqual(fn('?'), r'(?s:[^/])\Z')
		self.assertEqual(fn('a*'), r'(?s:a[^/]*)\Z')
		self.assertEqual(fn('*a'), r'(?s:[^/]*a)\Z')
		self.assertEqual(fn('.*'), r'(?s:\.[^/]*)\Z')
		self.assertEqual(fn('?aa'), r'(?s:[^/]aa)\Z')
		self.assertEqual(fn('aa?'), r'(?s:aa[^/])\Z')
		self.assertEqual(fn('aa[ab]'), r'(?s:aa[ab])\Z')
		self.assertEqual(fn('**'), r'(?s:[^/]*)\Z')
		self.assertEqual(fn('***'), r'(?s:[^/]*)\Z')
		self.assertEqual(fn('a**'), r'(?s:a[^/]*)\Z')
		self.assertEqual(fn('**b'), r'(?s:[^/]*b)\Z')
		self.assertEqual(fn('/**/*/*.*/**'), r'(?s:/[^/]*/[^/]+/[^/]*\.[^/]*/[^/]*)\Z')
	
	def test_translate_recursive(self):
		def fn(pat):
			return glob_translate(pat, recursive=True, include_hidden=True, seps='/')
		
		self.assertEqual(fn('*'), r'(?s:[^/]+)\Z')
		self.assertEqual(fn('?'), r'(?s:[^/])\Z')
		self.assertEqual(fn('**'), r'(?s:.*)\Z')
		self.assertEqual(fn('**/**'), r'(?s:.*)\Z')
		self.assertEqual(fn('***'), r'(?s:[^/]*)\Z')
		self.assertEqual(fn('a**'), r'(?s:a[^/]*)\Z')
		self.assertEqual(fn('**b'), r'(?s:[^/]*b)\Z')
		self.assertEqual(fn('/**/*/*.*/**'), r'(?s:/(?:.+/)?[^/]+/[^/]*\.[^/]*/.*)\Z')
	
	def test_translate_seps(self):
		def fn(pat):
			return glob_translate(pat, recursive=True, include_hidden=True, seps=['/', '\\'])
		
		self.assertEqual(fn('foo/bar\\baz'), r'(?s:foo[/\\]bar[/\\]baz)\Z')
		self.assertEqual(fn('**/*'), r'(?s:(?:.+[/\\])?[^/\\]+)\Z')
