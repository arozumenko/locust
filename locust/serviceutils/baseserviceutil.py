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

"""Base functionality of all service util modules.

 This module provides base functionality that allows to create,
 This module provides base functionality that allows to create,
 monitor and control a number of any locust processes
 by supervisor on UNIX-like operating systems or by pywin32 on
 Windows operating systems.
 """
__author__ = 'Mykhailo Makovetskiy - makovetskiy@gmail.com'

import sys
import os
import shutil
import stat
import inspect
from hashlib import sha256
from uuid import uuid4

from configobj import ConfigObj
from locust.common import is_sudoer
from locust.serviceutils import CONFIG_STORAGE
from locust.serviceutils import MODULE_CFG_PATH, EXIT_CODE

class ErrMsg(object):
    """Service error messages."""
    #pylint: disable=R0903
    cfg_tmpl_key = ('ERROR: Coud not get config template {cfg} of'
                    ' the service {name}.\n')

    cfg_file_exist = 'Config file at {path} does not exist.\n'

    cfg_section_exist = ('Given configuration file {path} does not '
                         'contains section {sec}\n')

    cfg_option_exist = ('Given configuration file {path} does not '
                        'contains option {opt} in section {sec}\n')

    runner_type_err = ('arg runner must be a class instance or function.'
                       ' Given runner type is {typ}.\n')


#pylint: disable=R0903
class BaseServiceUtil(object):
    """ Base serviceutils class."""
    def __init__(self, runner, name):
        """BaseServiceUtil constructor.

        Args:
          runner (types.ClassType, types.FunctionType, types.MethodType):
            Object that run mainloop cycle of a locust module.
          name (str): Name of a service in service control
            (supervisor or pywin32).

        Note: BaseServiceUtil must realise the following method to
          provide public interface for service manipulation:
            * install - Install a locust service
              - create all locust module configs and save it to defined
                  places.
            - register locust module as supervisor process if need it.
              + create supervisor process config for locust module
                      and copy them to supervisor config directory.
              + add locust module to supervisor processes list.
                - other needed action.
            * remove - Uninstall a locust service.
              - If module is running under supervisor.
                + Stop runnig module supervisor process.
                + Remove supervisor process config of locust module
                + reload supervisor daemon.
              - remove all locust module configs.

        Note1: BaseServiceUtil should realise the following method to
          provide public interface for service manipulation if module
          using supervisor to daemonizing:
            * stop - Stop a locust service.
            * start - Start a locust service.
            * status - Get status of a locust service.
            * restart - Restart a locust service.

        """
        if not is_sudoer(stderr=True):
            sys.exit(EXIT_CODE)

        isclass = inspect.isclass(runner)
        isfunction = inspect.isfunction(runner)
        ismethod = inspect.ismethod(runner)
        hasclass = hasattr(runner, '__class__')

        if not (isclass or isfunction or ismethod or hasclass):
            raise TypeError(ErrMsg.runner_type_err.format(
                typ=str(type(runner))))
        self.name = str(name)

        if isclass or isfunction:
            module = runner.__module__
        elif ismethod:
            module = runner.__self__.__module__
        else:
            module = runner.__class__.__module__
        self._makedir(MODULE_CFG_PATH, stderr=True)
        self.runner_path = sys.modules[module].__file__
        self.runner_path = os.path.abspath(self.runner_path)
        self.key_path = os.path.abspath(os.path.join(MODULE_CFG_PATH, '.key'))
        self.mod_conf_path = MODULE_CFG_PATH
        self.mod_conf_ext = '.conf'

    def create_key(self, key_name):
        print "Auth token: %s" % self._create_secure_key(key_name=key_name)

    def _create_config(self, cfg_name, cfg_path, cfg_ext='.conf',
                       override=True, **kwargs):
        """Create a configuration file based on template.

        Templates is placed in global CFG_TML object. CFG_TML is
        instance of ServiceConfig class from serviceconfig.

        Args:
          cfg_name (str): key of a config template. Define which
            template is used to creation config file.
             For example a servce contain two config
          cfg_path (str): Path to cindig file directory like
             '/etc/locust/'
          cfg_ext (str, optional): Configuration file extension.
          override (bool):
          **kwargs: Format template arguments.

        """

        cfg_path = self._makedir(cfg_path, stderr=True)

        if not (CONFIG_STORAGE.isconfigvalid(self.name) and cfg_path):
            sys.exit(EXIT_CODE)

        tmpl = CONFIG_STORAGE.get_config(self.name, cfg_name)
        if not tmpl:
            sys.stderr.write(ErrMsg.cfg_tmpl_key.format(cfg=self.name,
                                                        name=cfg_name))
            sys.exit(EXIT_CODE)
        file_name = os.path.join(cfg_path, self.name + cfg_ext)
        if os.path.isfile(file_name) and not override:
            return
        config = ConfigObj()
        for sect in tmpl:
            sect_name = sect['section'].format(**kwargs)
            sect_opts = sect['options']
            config[sect_name] = {}
            for sect_opt in sect_opts:
                opt_name = str(sect_opt[0])
                if isinstance(opt_name, str):
                    opt_name = opt_name.format(**kwargs)
                opt_val = sect_opt[1]
                if isinstance(opt_val, str):
                    opt_val = opt_val.format(**kwargs)
                config[sect_name][opt_name] = opt_val
        config.filename = file_name
        config.write()

    def _remove_secure_key(self):
        """Remove secure key file"""
        if os.path.exists(self.key_path):
            self._rm(self.key_path)

    def _create_secure_key(self, key_name=None):
        """Create file that contains secure key.

        Create two files:
          First file contains secure key based on uuid4 and is located
            at python module path.
          Second file is located in user home directory and contains
            sha256 crypted key based on uuid4. This key use as public
            key.

        """

        key = key_name if key_name else str(uuid4())
        old_key = None
        if os.path.exists(self.key_path):
            file_open = open(self.key_path)
            old_key = file_open.read()
            file_open.close()
        if old_key != key:
            file_open = open(self.key_path, 'w')
            file_open.write(key)
            file_open.close()
        key_token = sha256(key).hexdigest()
        usr_key_path = os.path.join(os.path.expanduser('~'), 'keyfile')

        file_open = open(usr_key_path, 'w+')
        file_open.write(sha256(key).hexdigest())
        file_open.close()
        # Read write access code from stat for file is preferred to UNIX
        # file system access codes because we can use it in windows.
        #  For example os.chmod(path, 600) in window set file as
        #  read-only and we can not overwrite him.
        os.chmod(usr_key_path, stat.S_IWRITE | stat.S_IREAD)
        return key_token

    def _create_module_config(self, override=False, **kwargs):
        """Create a locust module supervisor configuration file.

        Templates is placed in global CFG_TML object. CFG_TML is
        instance of ServiceConfig class from serviceconfig.

        Args:
          **kwargs: Format template arguments.

        """
        self._create_config('config', self.mod_conf_path, self.mod_conf_ext,
                            override=override, **kwargs)

    def _remove_module_conf(self):
        """Remove a locust configuration file."""
        cfg_file = os.path.join(self.mod_conf_path,
                                self.name + self.mod_conf_ext)
        self._rm(cfg_file)

    @staticmethod
    def _rm(path='', del_empty_par_dir=True):
        """Remove given file or directory."""
        base_path = os.path.dirname(path)
        is_file = os.path.isfile(path)
        if os.path.exists(path):
            os.remove(path)
            if is_file and not os.listdir(base_path) and del_empty_par_dir:
                shutil.rmtree(base_path)

    @staticmethod
    def _makedir(path='', stderr=False):
        """Create directory."""
        tmp_path = path
        if tmp_path and not os.path.exists(tmp_path):
            try:
                os.makedirs(tmp_path)
            except OSError:
                if stderr:
                    msg = 'ERROR: Could not create directory - {path}\n'
                    msg = msg.format(path=tmp_path)
                    sys.stderr.write(msg)
                tmp_path = ''
        return tmp_path

    @staticmethod
    def _change_cfg_prm(cfg_path, section, option, value):
        """Change value in given configuration file.

        Args:
          cfg_path (str): Full absolute path to the configuration file.
          section (str): Section in configuration file.
          option (str): Option name.
          value : option value

        Raises:
          AssertionError: Raises in following situations:
           - configuration file doesn't exist
           - Given section does not exist in configuration file.
           - Given option does not exist in given section of
             configuration fil.e

        """
        assert os.path.exists(cfg_path), ErrMsg.cfg_file_exist.format(
            path=cfg_path)

        cfg = ConfigObj(cfg_path)
        assert section in cfg, ErrMsg.cfg_section_exist.format(path=cfg_path,
                                                               sec=section)

        assert option in cfg[section], ErrMsg.cfg_option_exist.format(
            path=cfg_path, opt=option, sec=section)

        cfg[section][option] = value
        cfg.write()
