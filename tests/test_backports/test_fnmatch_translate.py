#!python
"""
Testing the glob_.translate function
"""

from unittest import TestCase

from pathlib_.fnmatch_ import translate

class TranslateTestCase(TestCase):

    def test_translate(self):
        import re
        self.assertEqual(translate('*'), r'(?s:.*)\Z')
        self.assertEqual(translate('?'), r'(?s:.)\Z')
        self.assertEqual(translate('a?b*'), r'(?s:a.b.*)\Z')
        self.assertEqual(translate('[abc]'), r'(?s:[abc])\Z')
        self.assertEqual(translate('[]]'), r'(?s:[]])\Z')
        self.assertEqual(translate('[!x]'), r'(?s:[^x])\Z')
        self.assertEqual(translate('[^x]'), r'(?s:[\^x])\Z')
        self.assertEqual(translate('[x'), r'(?s:\[x)\Z')
        # from the docs
        self.assertEqual(translate('*.txt'), r'(?s:.*\.txt)\Z')
        # squash consecutive stars
        self.assertEqual(translate('*********'), r'(?s:.*)\Z')
        self.assertEqual(translate('A*********'), r'(?s:A.*)\Z')
        self.assertEqual(translate('*********A'), r'(?s:.*A)\Z')
        self.assertEqual(translate('A*********?[?]?'), r'(?s:A.*.[?].)\Z')
        # fancy translation to prevent exponential-time match failure
        t = translate('**a*a****a')
        self.assertEqual(t, r'(?s:(?>.*?a)(?>.*?a).*a)\Z')
        # and try pasting multiple translate results - it's an undocumented
        # feature that this works
        r1 = translate('**a**a**a*')
        r2 = translate('**b**b**b*')
        r3 = translate('*c*c*c*')
        fatre = "|".join([r1, r2, r3])
        self.assertTrue(re.match(fatre, 'abaccad'))
        self.assertTrue(re.match(fatre, 'abxbcab'))
        self.assertTrue(re.match(fatre, 'cbabcaxc'))
        self.assertFalse(re.match(fatre, 'dabccbad'))