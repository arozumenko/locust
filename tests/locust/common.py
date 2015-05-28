"""Module for common methods for locust tests"""


def assert_in(item, iterable):
    """Check is item in iterable"""
    if item in iterable:
        return True
    else:
        return False
