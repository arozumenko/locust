"""
Tests for bagent api module
These tests requires bagent installed
"""
# pylint: disable=W0403,C0103,too-many-public-methods

import unittest
from netifaces import interfaces
from locust.api import Agent


def difference(list1, list2):
    """Returns difference between two lists. Order matters."""
    return [x for x in list1 if x not in list2]


class ListNetworkAdapters(unittest.TestCase):
    """Implements unit tests
     for list_network_adapters method of bagent.api."""

    adapters = interfaces()

    not_in_result = 'Some adapters are not shown in result: {difference} ' \
                    'Result: {result}'
    extra_in_result = 'Extra adapters are shown in result: {difference} ' \
                      'Result: {result}'

    def test_list_network_adapters(self):
        """Receives the list of adapters and evaluates it."""

        self.assertTrue(self.adapters, 'System`s list of adapters is empty')

        result = Agent.list_network_adapters()
        self.assertEqual(type(result), list,
                         'Returned result should be list. Result: {}'.
                         format(result))

        self.assertTrue(result, 'Returned list of adapters is empty')
        adapters_vs_result = difference(self.adapters, result)

        self.assertFalse(adapters_vs_result,
                         self.not_in_result.
                         format(difference=adapters_vs_result,
                                result=result))

        result_vs_adapters = difference(result, self.adapters)

        self.assertFalse(result_vs_adapters,
                         self.extra_in_result.
                         format(difference=result_vs_adapters,
                                result=result))


def main():
    """method for invoking unit tests."""
    unittest.main(verbosity=3)


if __name__ == '__main__':
    main()
