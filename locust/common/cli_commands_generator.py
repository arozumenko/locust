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

"""Common module for all cli generators."""
import sys
from inspect import getargspec, getdoc, ismethod
from json import dumps
from optparse import OptionParser
from locust.common import get_list_pb_methods

__all__ = ['cli_main']


#pylint: disable=R0914
def populate_opt_parser(parser, method):
    """
    Populate OptionParser instance with method's arguments.

    Arguments:
        parser - an OptionParser instance;
        method - an API method object.

    """
    args_ignore = ['self']
    args, _, _, defaults = getargspec(method)
    args = [v for v in args if v not in args_ignore]

    defaults = defaults or []
    if defaults:
        required_args = args[:-len(defaults)]
        optional_args = args[-len(defaults):]
    else:
        required_args = args
        optional_args = []

    defaults = list(defaults)
    docstring = getdoc(method) or 'Information is not exists.'
    parser.set_usage('\n  %prog ' + method.__name__.replace('_', ' '))
    for arg in required_args:
        parser.usage += ' <%s>' % arg
        parser.add_option('--%s' % arg, default=False)
    for option, default in zip(optional_args, defaults):
        action, option_type, callback = 'store', 'str', None
        for opt in docstring.splitlines():
            if opt.strip().startswith(option):
                opt_hlp = opt.replace(option, '', 1).strip(' -:;,.')
                break
        else:
            opt_hlp = ''

        if isinstance(default, bool):
            action = 'store_' + str(not default).lower()
            option_type = None
        elif isinstance(default, list):
            # pylint: disable=W0613
            def parse_list(prs_option, opt, value, prs_parser):
                """ some strange method for parsing """
                setattr(prs_parser.values, prs_option.dest, value.split(','))

            callback = parse_list
            action = 'callback'
        parser.add_option('--%s' % option, default=default, help=opt_hlp,
                          type=option_type, action=action, callback=callback)
        parser.usage += ' [--%s=%s]' % (option, default)
    parser.usage += '\n\nDescription:\n  ' + docstring


#pylint: disable=R0914
def cli_main(apis, argv, exit_code=2):
    """ main for cli commands method """
    api_list = apis if isinstance(apis, list) else [(apis, True)]
    cmds = [parse_api_provider(api, argv, std) for (api, std) in api_list]

    # Print a list of available COMMANDS if a valid command
    # was not supplied for all api providers.
    if all(isinstance(cmd, list) for cmd in cmds):
        opt_parser = OptionParser()
        opt_parser.set_usage(
            '\n  %prog [options] command <args> [command-options]')
        opt_parser.usage += '\n\nCommands:\n '
        for cmd in cmds:
            usg = [x.replace('_', ' ') for x in cmd]
            opt_parser.usage += ' ' + '\n  '.join(usg) + '\n '
        opt_parser.print_help()
        sys.exit(exit_code)

    cmds = [cmd for cmd in cmds if not isinstance(cmd, list)]

    for stderr, name, cmd, cmd_argv in cmds:
        opt_parser = OptionParser()
        populate_opt_parser(opt_parser, cmd)
        options, args = opt_parser.parse_args(cmd_argv)

        # Remove default values from options dictionary
        # to avoid errors when calling command.
        options = dict(
            set(vars(options).items()) - set(opt_parser.defaults.items()))

        try:
            #pylint: disable=W0142
            res = dumps(cmd(*args, **options), indent=2)
            if stderr:
                print res
        except TypeError as ex:
            # Print user-friendly error message in case of incorrect
            # arguments amount.
            #pars_err =
            mgs = str(ex.message)
            if any(m in mgs for m in ['takes', 'got']):
                mgs = mgs[mgs.find('()') + 2:]
                msg_tmpl = '"%{command} {msg}" command'
                mgs = msg_tmpl.format(command=name, msg=mgs)
                # If command is a method: decrease numbers by 1
                # (i.e. remove 'self' argument).
                if ismethod(cmd):
                    mgs = ''.join([str(int(each) - 1) if each.isdigit() else
                                   each for each in mgs])
                opt_parser.error(mgs)
            elif any(x in mgs for x in ('Specify at least', 'Authorization')):
                opt_parser.error(mgs)
            else:
                raise


def parse_api_provider(api, argv, stderr=True):
    """Parse commandline arguments for the given api provider.

        Args:
          api (class, instance): API provider object.
          arg (list): command line arguments.
          stderr (bool): Set quiet check validation if False.

        Returns:
          dict : Contains stderr for api provider and command runner
           if any api provider command presents in commandline
           arguments or dictionary with api provider commands.
    """
    commands = get_list_pb_methods(api)
    for key, command in commands.items():
        name_len = len(key.split('_')) + 1
        if key == '_'.join(argv[1:name_len]):
            return stderr, key.replace('_', ' '), command, argv[name_len:]
    return sorted(commands.keys())
