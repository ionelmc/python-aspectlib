from __future__ import print_function

import warnings
import unittest
import os

import aspectlib
from aspectlib.test import mock, record

class AOPTestCase(unittest.TestCase):
    def test_mock_builtin(self):
        with aspectlib.weave(open, mock('foobar')):
            self.assertEqual(open('???'), 'foobar')

        self.assertNotEqual(open(__file__), 'foobar')

    def test_record_warning(self):
        with aspectlib.weave('warnings.warn', record):
            warnings.warn('crap')
            self.assertEqual(warnings.warn.calls, [(None, ('crap',), {})])

    def test_fork(self):
        with aspectlib.weave('os.fork', mock('foobar')):
            pid = os.fork()
            if not pid:
                os._exit(0)
            self.assertEqual(pid, 'foobar')

        pid = os.fork()
        if not pid:
            os._exit(0)
        self.assertNotEqual(pid, 'foobar')
