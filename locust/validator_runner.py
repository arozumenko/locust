#  Copyright (c) 2014 Artem Rozumenko (artyom.rozumenko@gmail.com)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Validator runner module."""
from sys import exc_info
from json import dumps, loads
from os import path
from hashlib import sha256
from traceback import format_exception
from locust.serviceutils import MODULE_CFG_PATH
from locust.api import Agent
from locust import LOGGING_LEVEL

#pylint: disable=W0703, R0903
class ValidatorRunner(object):
    """Validator class."""

    def __init__(self):
        self.api = Agent()
        try:
            file_open = open(path.join(MODULE_CFG_PATH, '.key'), 'r')
            key = file_open.read()
            file_open.close()
            self.key = sha256(key).hexdigest()
        except OSError:
            pass

    #pylint: disable=R0911
    def validate_and_run(self, data):
        """
        Example of data to validate and run
        json_1 = u'{"command": "get_process" ,
        "arguments": {"pids": [8193], "names": []} }'
        """
        err = ''

        try:
            try:
                data = loads(data)
            except ValueError as ex:
                err = "bad_request"
                value = "Data has wrong format. Exception: %s" % ex
                return err, value
            try:
                key = data['key']
                if key != self.key:
                    raise NameError('Auth Failed')
            except NameError:
                err = "authorization_failed"
                value = "Authorisation failed"
                return err, value
            try:
                command = data['command']
            except KeyError as ex:
                err = "bad_request"
                value = "There is no 'command' field or data has wrong " \
                        "format Exception: %s.  Data: %s" % (ex, data)
                return err, value
            try:
                if 'arguments' in data:
                    arguments = data['arguments']
                    #pylint: disable=W0142
                    result = getattr(self.api, command)(**arguments)
                else:
                    result = getattr(self.api, command)()
                #Here we return correct result:
                return err, result
            except AttributeError as ex:
                err = "wrong_command"
                value = "Wrong command name. Command: %s Data: %s " \
                        "Exception: %s" % (command, data, ex)
                return err, value
            except TypeError as ex:
                err = "wrong_parameters"
                value = "Wrong value was passed to method. Command: %s . " \
                        "Data: %s . Exception: %s" % (command, data, ex)
                return err, value
        #pylint: disable=W0702
        except:
            err = "unexpected_error"
            value = "this is strange"
            if LOGGING_LEVEL == 'debug':
                value = "Exception: {exc}. Incoming values: {data}".format(
                    exc=format_exception(*exc_info()), data=data)
            return err, value
