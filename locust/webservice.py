#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


"""The locust agent webservice module."""

import inspect
import requests
from json import dumps
from gevent.wsgi import WSGIServer
from flask import Flask
from flask_restful import Api, Resource, request
from locust.api import Agent
from locust.validator_runner import ValidatorRunner
from locust.common import create_parser_for_websrv, \
    parse_websrv_kwargs
from locust import WEB_SRV_CFG


__all__ = ['run']

#pylint: disable=C0103
PARSER = create_parser_for_websrv(WEB_SRV_CFG)

#pylint: disable=C0103
APP = Flask(__name__)
API = Api(APP)

RUNNER = None

CMDS = dict(inspect.getmembers(Agent, predicate=inspect.ismethod))
CMDS = dict((k, v) for k, v in CMDS.items() if not k.startswith('_'))


#pylint: disable=W0232
class locust(Resource):
    """ locust request handler"""

    @staticmethod
    def get():
        """GET method for index.


        Returns string messages with list of available methods the locust
        agent and usage example.
        """
        try:
            list_of_commands = dumps(CMDS.keys(), indent=2)
        except TypeError:
            list_of_commands = 'ERROR: UNABLE_TO_GET_COMMANDS'
        cmds = ('Hi there! \n '
                'Basic usage:\n POST:\n'
                '       json_1 = u\'{"command": "get_process" , "arguments":'
                '{"pids": [15870,15913], "names": []},"key":host_key}\'\n\n'
                'RESPONSE:\n    '
                '[{"status": "sleeping", "node": "119004516906817"\n '
                '"endpoint": "127.0.1.1", "name": "python2.7",\n '
                '"cmd": "/usr/bin/python2.7 -u /home/usr/websevice/webservice'
                '.py\n 8086", "pid": 15870,\n '
                '"uuid": "e4d4951a-08d6-11e3-b487-6c3be5f4f741"},\n '
                '{"status": "sleeping", "node": "119004516906817",\n '
                '"endpoint": "127.0.1.1", "name": "firefox",\n '
                '"cmd": "/usr/lib/firefox/firefox", "pid": 15913,\n '
                '"uuid": "e4d52944-08d6-11e3-b487-6c3be5f4f741"}]\n\n '
                'COMMANDS: \n %s') % list_of_commands
        return cmds

    @staticmethod
    def post():
        """Execute a given locust agent command and returns execution result.

        Validate POST data and execute the locust agent command given in POST
        data.


        Returns the result of the execution of a specified locust agent
        command.
        """

        #pylint: disable=W0603
        global RUNNER
        if RUNNER is None:
            RUNNER = ValidatorRunner()
        err, value = RUNNER.validate_and_run(request.data)
        #pylint: disable=E1101
        if err:
            return {"status": err, "value": value}, requests.codes.forbidden
        return value, requests.codes.ok


API.add_resource(locust, '/')


def run(**kwargs):
    """
    Main method for webservice.
    Run the locust flask webservice with defined options
    """
    #pylint: disable=W0142
    opt = parse_websrv_kwargs(WEB_SRV_CFG, **kwargs)
    http_server = WSGIServer(opt, APP)
    http_server.serve_forever()


if __name__ == '__main__':
    options, _ = PARSER.parse_args()
    #pylint: disable=W0142
    run(**vars(options))
