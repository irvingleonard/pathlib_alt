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
