"""
Tests for locust api module

These tests requires locust installed
"""
#pylint: disable=W0403,C0103,too-many-public-methods
import re
import unittest

from locust.api import Agent
from common import assert_in


LIST_PROCESS_STRUCTURE = {
    "status": [str, r'[a-z]*'],
    "node": [str, r'[0-9]*'],
    "endpoint": [str, r'[0-9]*.[0-9]*.[0-9]*.[0-9]*'],
    "name": [str, ''],
    "cmd": [str, ''],
    "pid": [int],
    "uuid": [str, r'[a-z0-9-]*'],
}


class ListProcessApi(unittest.TestCase):
    """Implements unit tests for list_process method of bagent.api."""

    #Set of tests for PIDs as argument
    def test_list_proc_pid_ret_dict(self):
        """List process returns dict type."""
        result = Agent.list_process()
        self.assertEqual(type(result), dict, 'Returned result should be dict')

    def test_list_proc_ret_structure(self):
        """List process must return all required fields."""
        result = Agent.list_process()
        for proc in result['list']:
            for field in LIST_PROCESS_STRUCTURE:
                self.assertTrue(assert_in(field, proc),
                                "{field} not in {result}".format(field=field,
                                                                 result=proc))

    def test_list_proc_pid_ret_types(self):
        """List process must return all fields with proper data."""
        result = Agent.list_process()
        for proc in result['list']:
            for field in LIST_PROCESS_STRUCTURE:
                self.assertEqual(type(proc[field]),
                                 LIST_PROCESS_STRUCTURE[field][0],
                                 "{value} of type {type1} is not match"
                                 " {type2}".format(
                                     value=proc[field],
                                     type1=str(type(proc[field])),
                                     type2=str(LIST_PROCESS_STRUCTURE[
                                         field][0])))
                if str == LIST_PROCESS_STRUCTURE[field][0] and \
                        LIST_PROCESS_STRUCTURE[field][1]:
                    self.assertTrue(re.match(LIST_PROCESS_STRUCTURE[field][1],
                                             proc[field]),
                                    "{value} is not match {patern}".format(
                                        value=proc[field],
                                        patern=LIST_PROCESS_STRUCTURE[field][1]
                                    ))

    def test_list_proc_only_unique_procs(self):
        """List process only unique processes should be in result"""
        result = Agent.list_process()
        pids = []
        for proc in result['list']:
            pids.append(proc['pid'])
        self.assertTrue(len(pids) == len(set(pids)),
                        'Only unique processes should be returned')


def main():
    """method for invoking unit tests."""
    unittest.main(verbosity=3)

if __name__ == '__main__':
    main()
