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

MESSAGES = {'success': 'Network adapter is enabled',
            'error': 'Network adapter is not enabled'}

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


def enable_network_adapters_if_disabled():
    """Enables all network adapters if disabled"""
    if not wait_for_network_enabled():
            Agent.enable_network_adapters()
            wait_for_network_enabled()


def disable_adapters(adapters=None):
    """ Disables specified adapter or list of adapters.
    Disables all if no adapters provided.
    Returns error message in case of error """

    time_to_be_disabled = 0

    result = Agent.disable_network_adapters(adapters, time_to_be_disabled)

    if 0 == result['list'][0]['status'].find('error'):
        return 'Error while disabling adapters. Result: {}'.format(result)

    if not wait_for_network_disabled():
        return 'Error while disabling adapters. Network is still enabled.' \
            ' Result: {}'.format(result)

    if wait_for_network_enabled():
        return 'Error while disabling adapters. Network was enabled. ' \
            'But it should stay disabled. Result: {}'.format(result)


class EnableNetworkAdaptersApi(unittest.TestCase):
    """Implements unit tests
     for enable_network_adapters method of bagent.api."""

    wrong_status = 'Expected status: {expected}. Current status: {actual}'
    wrong_message = 'Expected message: {expected}. Current message: {actual}'

    def test_enable_one_network_adapter(self):
        """Enables an active adapter, that was disabled previously"""

        adapter = get_active_adapter()

        disable_adapters_error = disable_adapters(adapter)

        self.assertFalse(disable_adapters_error, msg=disable_adapters_error)

        self.assertTrue(wait_for_network_disabled(),
                        'Initially Network is enabled.')

        result = Agent.enable_network_adapters(adapter)
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

        self.assertTrue(wait_for_network_enabled(),
                        'Network was not enabled')

    def test_enable_all_network_adapters_empty_list(self):
        """Enables all adapters, that was disabled previously
        List of adapters is empty """

        adapter = None

        disable_adapters_error = disable_adapters(adapter)

        self.assertFalse(disable_adapters_error, msg=disable_adapters_error)

        self.assertTrue(wait_for_network_disabled(),
                        'Initially Network is enabled.')

        result = Agent.enable_network_adapters(adapter)
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

        self.assertTrue(wait_for_network_enabled(),
                        'Network was not enabled')

    def test_enable_all_network_adapters(self):
        """Enables all adapters, that was disabled previously"""

        adapter = interfaces()

        disable_adapters_error = disable_adapters(adapter)

        self.assertFalse(disable_adapters_error, msg=disable_adapters_error)

        self.assertTrue(wait_for_network_disabled(),
                        'Initially Network is enabled.')

        result = Agent.enable_network_adapters(adapter)
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

        self.assertTrue(wait_for_network_enabled(),
                        'Network was not enabled')

    def test_enable_non_existing_network_adapters(self):
        """ Trying to use adapter name that does not exist"""

        adapter = 'this_adapter_does_not_exist'

        disable_adapters_error = disable_adapters()

        self.assertFalse(disable_adapters_error, msg=disable_adapters_error)

        self.assertTrue(wait_for_network_disabled(),
                        'Initially Network is enabled.')

        result = Agent.enable_network_adapters(adapter)
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

        self.assertFalse(wait_for_network_enabled(),
                         'Network was enabled. But it should stay disabled.')

        enable_network_adapters_if_disabled()

    def setUp(self):
        enable_network_adapters_if_disabled()

    @classmethod
    def tearDownClass(cls):
        enable_network_adapters_if_disabled()


def main():
    """method for invoking unit tests."""
    unittest.main(verbosity=3)

if __name__ == '__main__':
    main()
