"""
Tests for bagent api module

These tests requires bagent installed
"""
#pylint: disable=W0403,too-many-public-methods

import os
import re
import unittest

from random import randrange

from locust.api import Agent
from common import assert_in


GET_PROCESS_STRUCTURE = {
    "status": [str, r'[a-z]*'],
    "node": [str, r'[0-9]*'],
    "endpoint": [str, r'[0-9]*.[0-9]*.[0-9]*.[0-9]*'],
    "name": [str, ''],
    "cmd": [str, ''],
    "pid": [int],
    "uuid": [str, r'[a-z0-9-]*'],
    "cpu": [float],
    "ram": [long]
}


class GetProcessApi(unittest.TestCase):
    """Implements unit tests for get_process method of bagent.api."""

    #Set of tests for PIDs as argument
    def test_get_proc_pid_ret_dict(self):
        """Get process returns dict type."""
        current_pid = os.getpid()
        result = Agent.get_process(pids=[current_pid])
        self.assertEqual(type(result), dict, 'Returned result should be dict')

    def test_get_proc_pid_ret_pid(self):
        """Get process returns requested pid in results"""
        current_pid = os.getpid()
        result = Agent.get_process(pids=[current_pid])
        self.assertEqual(result['list'][0]['pid'],
                         current_pid, 'Requested pid should be in result')

    def test_get_proc_pid_ret_one(self):
        """Get process with one pid returns one result."""
        current_pid = os.getpid()
        result = Agent.get_process(pids=[current_pid])
        self.assertEqual(len(result['list']), 1,
                         'For one pid should be one process')

    def test_get_proc_pid_ret_two(self):
        """Get process with two existing pids must returns two results."""
        current_pid = os.getpid()
        parent_pid = os.getppid()
        result = Agent.get_process(pids=[current_pid, parent_pid])
        self.assertEqual(len(result['list']), 2,
                         'For two pids should be two process')

    def test_get_proc_pid_ret_structure(self):
        """Get process must return all required fields."""
        current_pid = os.getpid()
        parent_pid = os.getppid()
        result = Agent.get_process(pids=[current_pid, parent_pid])
        for proc in result['list']:
            for field in GET_PROCESS_STRUCTURE:
                self.assertTrue(assert_in(field, proc),
                                "{field} not in {result}".format(field=field,
                                                                 result=proc))

    def test_get_proc_pid_ret_types(self):
        """Get process must return all fields with proper data."""
        current_pid = os.getpid()
        parent_pid = os.getppid()
        result = Agent.get_process(pids=[current_pid, parent_pid])
        for proc in result['list']:
            for field in GET_PROCESS_STRUCTURE:
                self.assertEqual(type(proc[field]),
                                 GET_PROCESS_STRUCTURE[field][0],
                                 "{value} of type {type1} is not match"
                                 " {type2}".format(
                                     value=proc[field],
                                     type1=str(type(proc[field])),
                                     type2=str(GET_PROCESS_STRUCTURE[
                                         field][0])))
                if str == GET_PROCESS_STRUCTURE[field][0] and \
                        GET_PROCESS_STRUCTURE[field][1]:
                    self.assertTrue(re.match(GET_PROCESS_STRUCTURE[field][1],
                                             proc[field]),
                                    "{value} is not match {patern}".format(
                                        value=proc[field],
                                        patern=GET_PROCESS_STRUCTURE[field][1]
                                    ))

    def test_get_proc_pid_not_exists(self):
        """Get process must return empty list if pid doesn't exists."""
        pid = 0
        while True:
            pid = randrange(0, 2147483647, 1)
            try:
                os.getsid(pid)
            except OSError:
                break
        result = Agent.get_process(pids=[pid])
        self.assertEqual(len(result['list']), 0,
                         'For not existing process should be '
                         'json with 0 values')

    def test_get_proc_skip_not_exist(self):
        """Get process returns result for existing and ignores not existing."""
        pid = 0
        while True:
            pid = randrange(0, 2147483647, 1)
            try:
                os.getsid(pid)
            except OSError:
                break
        current_pid = os.getpid()
        result = Agent.get_process(pids=[pid, current_pid])
        self.assertEqual(len(result['list']), 1,
                         'For 1 existing process should be '
                         'json with one result')

    # Set of tests for Names as argument
    def test_get_proc_by_name(self):
        """Get process with one pid and name returns same result."""
        current_pid = os.getppid()
        result_pid = Agent.get_process(pids=[current_pid])
        curr_name = result_pid["list"][0]["cmd"]
        result_name = Agent.get_process(names=[curr_name])
        del result_pid['list'][0]['cpu']
        del result_pid['list'][0]['ram']
        del result_pid['list'][0]['uuid']
        del result_name['list'][0]['cpu']
        del result_name['list'][0]['ram']
        del result_name['list'][0]['uuid']
        self.assertTrue(assert_in(result_pid['list'][0], result_name['list']),
                        'Process by name should be returned')

    def test_get_proc_by_name_ret_name(self):
        """Get process by name returns name in results."""
        current_pid = os.getppid()
        result_pid = Agent.get_process(pids=[current_pid])
        curr_name = result_pid["list"][0]["cmd"]
        result_name = Agent.get_process(names=[curr_name])
        self.assertEqual(result_name['list'][0]['cmd'],
                         curr_name, 'Requested name should be in result')

    def test_get_proc_by_name_not_exist(self):
        """Get process with not existing process name."""
        result = Agent.get_process(names=['not existing process'])
        self.assertEqual(len(result['list']), 0,
                         'For not existing process should be '
                         'json with 0 values')

    def test_get_proc_by_name_ast(self):
        """Get process works with * for autocomplete."""
        result = Agent.get_process(names=['*bash'])
        self.assertTrue(len(result['list']) > 0,
                        'Autocomplete should return list of processes')

    def test_get_proc_by_name_two_ast(self):
        """Get process works with two * for autocomplete."""
        result = Agent.get_process(names=['*bas*'])
        self.assertTrue(len(result['list']) > 0,
                        'Autocomplete should return list of processes')

    # Set of tests for Names and PIDs as arguments
    def test_get_proc_by_name_and_pid(self):
        """Get process with pid and name at the same time."""
        current_pid = os.getpid()
        parrent_pid = os.getppid()
        result_pid = Agent.get_process(pids=[parrent_pid])
        curr_name = result_pid["list"][0]["cmd"]
        result = Agent.get_process(pids=[current_pid], names=[curr_name])
        self.assertTrue(len(result['list']) == 1,
                        'pid and names should return both processes')

    def test_get_proc_only_unique_procs(self):
        """Get process only unique processes should be in result"""
        parrent_pid = os.getppid()
        result_pid = Agent.get_process(pids=[parrent_pid])
        curr_name = result_pid["list"][0]["cmd"]
        result = Agent.get_process(pids=[parrent_pid], names=[curr_name])
        pids = []
        for proc in result['list']:
            pids.append(proc['pid'])
        self.assertTrue(len(pids) == len(set(pids)),
                        'Only unique processes should be returned')

    # General tests
    def test_get_proc_no_args(self):
        """Get process call without any arguments."""
        try:
            Agent.get_process()
            raise NotImplementedError("TypeError Must be Risen")
        except TypeError, ex:
            self.assertEqual(ex.message, 'Specify at least one pid or name')


def main():
    """method for invoking unit tests."""
    unittest.main(verbosity=3)

if __name__ == '__main__':
    main()
