from __future__ import print_function

import unittest
import os

import aspectlib
from aspectlib.test import override_result

class AOPTestCase(unittest.TestCase):
    def test_mock_builtin(self):
        with aspectlib.weave(open, override_result('foobar')):
            self.assertEqual(open('???'), 'foobar')

        self.assertNotEqual(open(__file__), 'foobar')

    #def test_fork(self):
    #    def test_mock_builtin(self):
    #        with aspectlib.weave(os.fork, override_result('foobar')):
    #            pid = os.fork()
    #            if not pid:
    #                os._exit()
    #            self.assertEqual(pid, 'foobar')
    #
    #        self.assertNotEqual(open(__file__), 'foobar')
