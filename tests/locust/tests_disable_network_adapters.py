"""
Tests for locust api module

These tests requires locust installed
"""
#pylint: disable=W0403,C0103,too-many-public-methods

import unittest
from subprocess import call
from netifaces import interfaces
from locust.api import Agent
from time import time, sleep


STATUSES = {'success': 'success',
            'error': 'error'}

MESSAGES = {'success': 'Network adapter is disabled',
            'error': 'Network adapter is not disabled'}

HOSTNAME = 'google.com'


def is_network_enabled():
    """Ping a host to check if network is enabled """
    cmd_ptrn = 'ping -c {packets} {hostname} '
    cmd_ptrn = cmd_ptrn.format(packets=1, hostname=HOSTNAME)
    result = not bool(call(cmd_ptrn, shell=True))
    sleep(1)
    return result


def wait_for_network_disabled(seconds=30):
    """Wait until network is disabled"""
    then = time() + seconds
    while then > time():
        if not is_network_enabled():
            return True
    return False


def wait_for_network_enabled(seconds=30):
    """Wait until network is enabled"""
    then = time() + seconds
    while then > time():
        if is_network_enabled():
            return True
    return False


def check_network_interface_is_up(interface_name):
    """Check if netiface is up using 'ip' console command"""
    cmd_ptrn = "ip a|grep ': {interface}:.*state UP'"
    cmd_ptrn = cmd_ptrn.format(interface=interface_name)
    response = 0 == call(cmd_ptrn, shell=True)
    return response


def get_active_adapter():
    """ Returns first active adapter from the list of adapters"""
    for adapter in interfaces():
        if check_network_interface_is_up(adapter):
            return adapter


class DisableNetworkAdaptersApi(unittest.TestCase):
    """Implements unit tests
     for disable_network_adapters method of bagent.api."""

    time_to_be_disabled_common = 5
    time_delta_for_reconnect_common = 30
    time_to_wait_in_test_common = time_to_be_disabled_common +\
        time_delta_for_reconnect_common

    wrong_status = 'Expected status: {expected}. Current status: {actual}'
    wrong_message = 'Expected message: {expected}. Current message: {actual}'
    was_not_enabled = 'Network was not enabled after {seconds} seconds'
    was_enabled = 'Network was enabled after {seconds} seconds.' \
        'Should be disabled'
    was_disabled = 'Network was disabled. Should stay enabled'

    def test_disable_one_network_adapter(self):
        """Disables an active adapter
             and then enables after specified timeout."""

        time_to_be_disabled = self.time_to_be_disabled_common
        time_to_wait_in_test = self.time_to_wait_in_test_common
        adapter = get_active_adapter()

        self.assertTrue(wait_for_network_enabled(
                        self.time_delta_for_reconnect_common),
                        'Initially Network is disabled.')
        result = Agent.disable_network_adapters(adapter, time_to_be_disabled)
        self.assertEqual(type(result), dict, 'Returned result should be dict')

        status_from_result = result['list'][0]['status']
        message_from_result = result['list'][0]['message']

        self.assertEqual(status_from_result, STATUSES['success'],
                         self.wrong_status.format(
                         expected=STATUSES['success'],
                         actual=status_from_result))

        self.assertEqual(message_from_result, MESSAGES['success'],
                         self.wrong_message.format(
                         expected=MESSAGES['success'],
                         actual=message_from_result))

        self.assertTrue(wait_for_network_disabled(),
                        'Network was not disabled')

        self.assertTrue(wait_for_network_enabled(time_to_wait_in_test),
                        self.was_not_enabled.format(
                        seconds=time_to_wait_in_test))

    def test_disable_all_network_adapters_specify_list_of_adapter(self):
        """Disables all adapters (takes list of adapters as argument)
             and then enables after specified timeout."""

        time_to_be_disabled = self.time_to_be_disabled_common
        time_to_wait_in_test = self.time_to_wait_in_test_common
        adapters = interfaces()

        self.assertTrue(wait_for_network_enabled(
                        self.time_delta_for_reconnect_common),
                        'Initially Network is disabled.')
        result = Agent.disable_network_adapters(adapters, time_to_be_disabled)
        self.assertEqual(type(result), dict, 'Returned result should be dict')

        status_from_result = result['list'][0]['status']
        message_from_result = result['list'][0]['message']

        self.assertEqual(status_from_result, STATUSES['success'],
                         self.wrong_status.format(
                         expected=STATUSES['success'],
                         actual=status_from_result))

        self.assertEqual(message_from_result, MESSAGES['success'],
                         self.wrong_message.format(
                         expected=MESSAGES['success'],
                         actual=message_from_result))

        self.assertTrue(wait_for_network_disabled(),
                        'Network was not disabled')

        self.assertTrue(wait_for_network_enabled(time_to_wait_in_test),
                        self.was_not_enabled.format(
                        seconds=time_to_wait_in_test))

    def test_disable_all_network_adapters_empty_list_of_adapters(self):
        """Disables all adapters ('adapters' parameter is not set)
             and then enables after specified timeout."""

        time_to_be_disabled = self.time_to_be_disabled_common
        time_to_wait_in_test = self.time_to_wait_in_test_common
        adapters = None

        self.assertTrue(wait_for_network_enabled(
                        self.time_delta_for_reconnect_common),
                        'Initially Network is disabled.')
        result = Agent.disable_network_adapters(adapters, time_to_be_disabled)
        self.assertEqual(type(result), dict, 'Returned result should be dict')

        status_from_result = result['list'][0]['status']
        message_from_result = result['list'][0]['message']

        self.assertEqual(status_from_result, STATUSES['success'],
                         self.wrong_status.format(
                         expected=STATUSES['success'],
                         actual=status_from_result))

        self.assertEqual(message_from_result, MESSAGES['success'],
                         self.wrong_message.format(
                         expected=MESSAGES['success'],
                         actual=message_from_result))

        self.assertTrue(wait_for_network_disabled(),
                        'Network was not disabled')

        self.assertTrue(wait_for_network_enabled(time_to_wait_in_test),
                        self.was_not_enabled.format(
                        seconds=time_to_wait_in_test))

    def test_disable_all_network_adapters_no_time_no_adapters(self):
        """Disables all adapters ('adapters' parameter is not set)
             for unlimited time ('time' parameter = 0)."""

        time_to_be_disabled = 0
        time_to_wait_in_test = self.time_to_wait_in_test_common
        adapters = None

        self.assertTrue(wait_for_network_enabled(
                        self.time_delta_for_reconnect_common),
                        'Initially Network is disabled.')
        result = Agent.disable_network_adapters(adapters, time_to_be_disabled)
        self.assertEqual(type(result), dict, 'Returned result should be dict')

        status_from_result = result['list'][0]['status']
        message_from_result = result['list'][0]['message']

        self.assertEqual(status_from_result, STATUSES['success'],
                         self.wrong_status.format(
                         expected=STATUSES['success'],
                         actual=status_from_result))

        self.assertEqual(message_from_result, MESSAGES['success'],
                         self.wrong_message.format(
                         expected=MESSAGES['success'],
                         actual=message_from_result))

        self.assertTrue(wait_for_network_disabled(),
                        'Network was not disabled')

        self.assertFalse(wait_for_network_enabled(time_to_wait_in_test),
                         self.was_enabled.format(seconds=time_to_wait_in_test))

    def test_disable_not_existing_network_adapter(self):
        """ Trying to use name that does not exist.
             Verifying that correct error message is shown."""

        time_to_be_disabled = self.time_to_be_disabled_common
        time_to_wait_in_test = self.time_to_wait_in_test_common
        adapter = 'this_adapter_does_not_exist'

        self.assertTrue(wait_for_network_enabled(
                        self.time_delta_for_reconnect_common),
                        'Initially Network is disabled.')
        result = Agent.disable_network_adapters(adapter, time_to_be_disabled)
        self.assertEqual(type(result), dict, 'Returned result should be dict')

        status_from_result = result['list'][0]['status']
        message_from_result = result['list'][0]['message']

        self.assertEqual(status_from_result, STATUSES['error'],
                         self.wrong_status.format(
                         expected=STATUSES['error'],
                         actual=status_from_result))

        self.assertEqual(message_from_result, MESSAGES['error'],
                         self.wrong_message.format(
                         expected=MESSAGES['error'],
                         actual=message_from_result))

        self.assertFalse(wait_for_network_disabled(time_to_wait_in_test),
                         'Network was disabled. Should stay enabled')


    def setUp(self):
        if not wait_for_network_enabled(self.time_to_wait_in_test_common):
            Agent.enable_network_adapters()
            wait_for_network_enabled(self.time_delta_for_reconnect_common)

    @classmethod
    def tearDownClass(cls):
        if not wait_for_network_enabled(cls.time_to_be_disabled_common):
            Agent.enable_network_adapters()
            wait_for_network_enabled(cls.time_delta_for_reconnect_common)


def main():
    """method for invoking unit tests."""
    unittest.main(verbosity=3)

if __name__ == '__main__':
    main()
