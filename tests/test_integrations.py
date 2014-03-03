from __future__ import print_function

import unittest

import aspectlib
from aspectlib.test import override_result

class AOPTestCase(unittest.TestCase):
    if not aspectlib.PYPY:
        def test_mock_builtin(self):
            with aspectlib.weave(open, override_result('foobar')):
                self.assertEqual(open('???'), 'foobar')

            self.assertNotEqual(open(__file__), 'foobar')
