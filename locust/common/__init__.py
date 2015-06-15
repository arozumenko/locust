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

"""Helper module."""
import sys
# ----------------------------------------------------------------------------
#                             Platforms
# ----------------------------------------------------------------------------

# Windows-based system.
CURR_PLATFORM = str(sys.platform).lower()
IS_WINDOWS = 'win32' in CURR_PLATFORM
# Standard Linux 2+ system.
IS_LINUX = any(name in CURR_PLATFORM for name in ('linux', 'freebsd'))
IS_OSX = 'darwin' in CURR_PLATFORM
IS_SOLARIS = 'solar==' in CURR_PLATFORM

from sys import modules
from optparse import OptionParser
from configobj import ConfigObj, Section
from copy import deepcopy
from types import (MethodType as Mt, FunctionType as Ft, ClassType as Ct,
                   ModuleType as Mdt)
from inspect import isfunction, ismethod, getmembers, getargspec
from os import path, makedirs, remove, getuid
from sys import stdout
from glob import glob
from functools import wraps

def is_sudoer(stderr=False):
    """Check is user sudoer"""
    try:
        sudoer = getuid() == 0
    except AttributeError:
        #pylint: disable=F0401,E0611
        from ctypes.windll.shell32 import IsUserAnAdmin
        sudoer = IsUserAnAdmin() != 0

    if not sudoer and stderr:
        stdout.write(('ERROR: This program must be run with Administartor '
                      'privileges.\nAborting.\n'))
    return sudoer


def convert_timeout(timeout, def_timeout=60):
    """Checks is timeout is numeric and return it, otherwise
    returns DEF_TIMEOUT."""
    try:
        return float(timeout)
    except (TypeError, ValueError):
        return def_timeout


def sudo_require(func):
    """decorator for admin verifying"""
    @wraps(func)
    def wrapped(*args, **kwargs):
        """decorator wrapper"""
        if is_sudoer():
            return func(*args, **kwargs)
        return message_wrapper(message='This function must be run by Admin',
                               status='error')
    return wrapped


def validate_ip(ipv):
    """Check is given ip valid.

        Args:
          ipv (str): ip.

        Returns:
          bool : True if given ip valid.

        Examples:
            validate_ip('0.0.0.0') ==> True
            validate_ip('foo') ==> False
    """
    import iptools
    return iptools.ipv4.validate_ip(ipv) or iptools.ipv6.validate_ip(ipv)


def validate_port(port):
    """Validate a IPv4 port.

    Args:
      ipv (str): ip.

    Returns:
      bool : True if given port valid.

    Examples:
        validate_port('9000') ==> True
        validate_port('foo') ==> False
        validate_port('1000000') ==> False
    """
    try:
        return 0 <= int(port) <= 65535
    except ValueError:
        return False


def parse_pids(pids, delp=','):
    """Parse pids and return a list of integers."""
    if not pids:
        return []
    if isinstance(pids, int):
        pids = [pids]
    elif isinstance(pids, basestring) and pids.isdigit():
        pids = [int(pids)]
    elif isinstance(pids, basestring) and str(delp) in pids:
        pids = str(pids).split(str(delp))
    elif pids and not isinstance(pids, list):
        raise TypeError(
            'Can\'t parse "pids" argument. Type: %s. Value: %s.' % (
                type(pids), pids))
    return [int(each) for each in pids]


def parse_args_list(args, delp=','):
    """Parse a string of arguments to a list."""
    result = []
    if isinstance(args, basestring):
        if str(delp) in args:
            result.extend(str(args).split(str(delp)))
        else:
            result = [args]
    elif isinstance(args, list):
        result = args[:]
    elif args:
        raise TypeError('Can\'t parse arguments. Type: %s. Value: %s.' % (
            type(args), args))
    return result


def parse_kwargs(kwargs):
    """Parse a string of keyword arguments to a dictionary."""
    result = {}
    if isinstance(kwargs, basestring):
        result.update(eval(kwargs))
    elif isinstance(kwargs, dict):
        result.update(kwargs)
    else:
        raise TypeError(
            'Can\'t parse keyword arguments. Type: %s. Value: %s.' % (
                type(kwargs, kwargs)))
    return result


def check_folder(folder_path):
    """Create folder if not exists."""
    if not path.exists(folder_path):
        makedirs(folder_path)


def parse_websrv_kwargs(def_opt, **kwargs):
    """Form and validate flask start option.

    Args:
      def_opt: dictionary that contains default values for flask args.
      **kwargs: Dictionary that contain flask start options.

    Returns:
      tuple: settings tuple (<host>, <port>).
    """
    err_msg = {
        'wrong_host': ('ERROR: Wrong format of given host address {addr}. '
                       'Use default value - {val}'),
        'wrong_port': ('ERROR: Wrong port value {port} is given. '
                       'Use default value - {val}'),

        'wrong_def_opt_type': ('ERROR: def_opt parameter should be a '
                               'dictionary. Given type is {typ}'),
        'wrong_def_opt_con': ('ERROR: def_opt parameter should contains '
                              'values all following keys - {keys}')
    }

    wt_opt_keys = ['host', 'port']

    if not isinstance(def_opt, dict):
        raise TypeError(err_msg['wrong_def_opt_type'].format(
            typ=type(def_opt)))
    msg = err_msg['wrong_def_opt_con'].format(keys=' '.join(wt_opt_keys))
    assert all(k in wt_opt_keys for k in def_opt.keys()), msg

    get_val = lambda x: kwargs[x] if x in kwargs else def_opt[x]
    opt = {
        'host': get_val('host'),
        'port': int(get_val('port'))}

    if not validate_ip(opt['host']):
        print err_msg['wrong_host'].format(addr=opt['host'],
                                           val=def_opt['host'])
        opt['host'] = def_opt['host']

    if not validate_port(opt['port']):
        print err_msg['wrong_port'].format(port=opt['port'],
                                           val=def_opt['port'])
        opt['port'] = def_opt['port']
    opt['port'] = int(opt['port'])
    return tuple(opt.values())


def create_parser_for_websrv(def_opt):
    """Creates options parser for flask module of a locust package.

    Args:
      def_opt: dictionary that contains default values for flask args.

    Returns:
      OptionParser: OptionParser instance.
    """
    err_msg = {
        'wrong_def_opt_type': ('ERROR: def_opt parameter should be a '
                               'dictionary. Given type is {typ}'),
        'wrong_def_opt_con': ('ERROR: def_opt parameter must contain '
                              'values only for following keys - {keys}')
    }

    wt_opt_keys = ['host', 'port']
    if not isinstance(def_opt, dict):
        raise TypeError(err_msg['wrong_def_opt_type'].format(
            typ=type(def_opt)))
    msg = err_msg['wrong_def_opt_con'].format(keys=' '.join(wt_opt_keys))
    assert all(k in wt_opt_keys for k in def_opt.keys()), msg

    parser = OptionParser()

    parser.add_option('--host', dest='host', action='store',
                      default=def_opt['host'],
                      help='Setting hostname to listen on.')

    parser.add_option('--port', dest='port', action='store',
                      default=def_opt['port'], type='int',
                      help='The webserver port')
    return parser


def message_wrapper(message, status='success'):
    """
    System message wrapper.

    Argument:
        message - any message for processing
        status - status according message
    Return:
        RESTful format message
    """
    return dict(list=list([dict(message=message, status=status)]))


def load_config(cfg_path, default_cfg, std=False):
    """load config file into ConfigObj instance.

    Args:
      cfg_path (str): Path to the configuration file.
      default_cfg (confobj.ConfigObj): ConfigObj instance with default
        values

    Returns:
      ConfigObj: ConfigObj instance.
    """
    assert isinstance(default_cfg, ConfigObj), ('The "default_cfg"'
                                                'must be instance of '
                                                'ConfigObj')
    if not (path.exists(cfg_path) and path.isfile(cfg_path)):
        msg = ('Configuration file at {path} is not exist.'
               'Try to use default parameters.\n')
        print msg.format(path=cfg_path)
        if std:
            for section in default_cfg.sections:
                print '[{sect}]'.format(sect=section)
                for k, val in default_cfg[section].items():
                    print ' = '.join([str(k), str(val)])
        return deepcopy(default_cfg)
    return ConfigObj(cfg_path)


#pylint: disable=R0913
def init_module(mname, mpath, mglobals, mdefcfgname='DEF_CFG',
                sep='/', postactions=None):
    """ Initialize given global variables in given module from config file.

    Args:
      mname (str): A Python module name.
      mpath (srt): Path to a module configuration file.
      mglobals (list): List of tuples that contains pairs
        (<glob_var_name>, <path_to_value_in_conf>, <conv_method(optional)>)
        that must be initialised. Optional <conv_method> is
        type conversion method from ConfigObj like as_bool.
      mdefcfgname (str): A module default config name.
      sep (str): The <path_to_value_in_conf> separator in "mglobals" parameter.
      postactions (list): List of functions or methods that must be
        run after module initialisation.

    Returns:
      Value from dictionary.

    Raises:
      RuntimeError: Raise if <path_to_value_in_conf> in "mglobals" parameter
        is wrong.
    """
    if mname not in modules:
        raise RuntimeError('Could not get reference to the module ' + mname)
    mod = modules[mname]
    if mdefcfgname not in dir(mod):
        msg = 'Module {name} does not contains attribute "{cfgname}"'
        raise RuntimeError(msg.format(name=mname, cfgname=mdefcfgname))
    cfg = getattr(mod, mdefcfgname)
    if not isinstance(cfg, ConfigObj):
        msg = ('Wrong type of attribute "{aname}" in module {mname}.'
               'The attribute "{aname}" should be a instance of'
               'confobj.ConfObj. Current type is {atype}')
        raise TypeError(msg.format(
            aname=mdefcfgname, mname=mname, atype=str(type(cfg))))
    cfg = load_config(path.join(mpath, mname + '.conf'), cfg)
    for attr_def in mglobals:
        attr, apath = attr_def[0], attr_def[1]
        attr_type_conv = attr_def[2] if len(attr_def) == 3 else None
        try:
            setattr(mod, attr, get_dict_by_path(cfg, apath, sep=sep,
                                                conv_methd=attr_type_conv))
        except KeyError as ex:
            raise RuntimeError(ex.message)
    if isinstance(postactions, list) and postactions:
        for action in postactions:
            if isfunction(action) or ismethod(action):
                action(mod)
    return cfg


#pylint: disable=fixme
#TODO: Create class that extend ConfObj with method get_by_path
def get_dict_by_path(dicty, dpath, conv_methd=None, sep='/'):
    """ Returns value from  given dictionary by path defined in string.

    Args:
      dicty (dict): Source dictionary.
      dpath (srt): Path to required value,
      conv_methd (str): Type conversion method from ConfigObj like as_bool.
                        Conversion wil be ignored if given method is not
                        present in ConfigObj.
      sep (str): Path separator.

    Returns:
      Value from dictionary.

    Raises:
      KeyError: Raise if path in given dictionary is wrong.
    """
    conv_methods = ['as_bool', 'as_int', 'as_float', 'as_list']
    if not isinstance(dicty, (dict, ConfigObj)):
        raise TypeError(('ERROR: Type of parameter "dicty" should be a '
                         'dictionary. Current type is') + str(type(dicty)))
    dpath = str(dpath).split(sep)
    assert bool(dpath), 'Parameter "path" can not be empty.'
    dplen = len(dpath) - 1
    result = deepcopy(dicty)
    curpath = ''
    for index, item in enumerate(dpath):
        curpath += str(item) + sep
        if item not in result:
            raise KeyError('ERROR: Could not get value by path ' + curpath)
        cv_method = None
        if (index == dplen and conv_methd in conv_methods and
                isinstance(result, Section)):
            cv_method = getattr(result, conv_methd)
        result = cv_method(item) if cv_method else result[item]
        if index != dplen and not isinstance(result, (dict, ConfigObj)):
            raise KeyError('ERROR: Path "{}" is wrong'.format(curpath))
    return result


def get_list_pb_methods(obj):
    """ Return public members of given object as dictionary {name: members}.

    Args:
      obj (types.ClassType, types.ModuleTypes, class instance): Given object.

    Returns:
      Dictionary like {name: members} that contains all public members of a
        given object.

    Raises:
      AssertionError: Raise if given object is not class, module or class
        instance..
    """

    assert isinstance(obj, (type, Ct, Mdt)) or hasattr(obj, '__class__')
    is_pub = lambda x: not(x.startswith('_') or x.endswith('_'))
    is_pub_mth = lambda x: isinstance(x, (Mt, Ft)) and is_pub(x.__name__)
    return dict(list(set(getmembers(obj, predicate=is_pub_mth))))


def clean_servicestatus(service):
    """Remove shelve files"""
    servs = service if isinstance(service, (list, tuple)) else tuple([service])
    for serv in servs:
        for each in glob(serv + '*'):
            remove(each)


def get_func_argument(func, args, kwargs, arg_name):
    """Returns function argument value by name.

    Arguments:
        func - reference to function
        args - function positional arguments
        kwargs - function keyword arguments
        arg_name - argument name to get value from function arguments

    Returns:
        argument value
    """
    # if parameter in kwargs return it
    if arg_name in kwargs:
        return kwargs.get(arg_name)
    # inspect function to get args names list
    argspec = getargspec(func)
    if arg_name in argspec.args:
        # get index in names list and return value from args list
        return args[argspec.args.index(arg_name)]
    return None
