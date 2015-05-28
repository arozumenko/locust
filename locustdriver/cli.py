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

"""Remote CLI module for Locust Client."""
from os import environ
from argparse import ArgumentParser
from urllib2 import urlopen, HTTPError
from json import dumps


#pylint: disable=R0912
def main():
    """Main method in CLI method."""
    parser = ArgumentParser()
    parser.add_argument('-a', '--address', dest='address',
                        help='address of Locust Agent')
    parser.add_argument('-k', '--key', dest='key',
                        help='secret key for particular node')
    options, args = parser.parse_known_args()
    for arg in args:
        if arg.startswith('--'):
            option = arg[:arg.index('=')] if '=' in arg else arg
            parser.add_argument(option)
    all_options, args = parser.parse_known_args()
    command_options = dict((k, v) for k, v in all_options.__dict__.items() if
                           k not in options.__dict__)
    if not options.address:
        if environ.get('LOCUST_AGENT'):
            options.address = environ['LOCUST_AGENT']
        else:
            parser.error('Agent address is not specified. '
                         'Please provide -a|--address option '
                         'or set environment variable LOCUST_AGENT.')
    if not options.key:
        if environ.get('LOCUST_KEY'):
            options.key = environ['LOCUST_KEY']
        else:
            parser.error('Secret key is not specified. '
                         'Please provide -k | --key option '
                         'or set environment variable LOCUST_KEY.')

    if 'http' not in options.address:
        options.address = 'http://' + options.address
    command = []
    arguments = {}
    arguments.update(command_options)
    for arg in args:
        if '=' in arg:
            option, value = arg.split('=')
            arguments[option] = value
        else:
            command.append(arg)
    data = {}
    if command:
        data['command'] = '_'.join(command)
        if arguments:
            data['arguments'] = arguments
        data['key'] = options.key
    try:
        data = dumps(data) if data else None
        print urlopen(options.address, data).read()
    except HTTPError as error:
        print error
        print error.read()

if __name__ == '__main__':
    main()
