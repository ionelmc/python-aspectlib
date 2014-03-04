from __future__ import print_function

import unittest

import aspectlib
from aspectlib.test import mock

class AOPTestCase(unittest.TestCase):
    def test_mock_builtin(self):
        with aspectlib.weave(open, mock(returns='foobar')):
            self.assertEqual(open('???'), 'foobar')

        self.assertNotEqual(open(__file__), 'foobar')

    #def test_fork(self):
    #    with aspectlib.weave('os.fork', mock(returns='foobar')):
    #        pid = os.fork()
    #        if not pid:
    #            os._exit()
    #        self.assertEqual(pid, 'foobar')
    #
    #    pid = os.fork()
    #    if not pid:
    #        os._exit()
    #    self.assertNotEqual(pid, 'foobar')
