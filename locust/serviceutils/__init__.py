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

"""Global configuration parameters of the serviceutils module."""

__author__ = 'Mykhailo Makovetskiy - makovetskiy@gmail.com'

import os
import sys
from locust.common import IS_LINUX, IS_OSX, IS_WINDOWS

MODULE_CFG_PATH = None
#-----------------------------------------------------------------------------
EXIT_CODE = 2


from locust.serviceutils.serviceconfig import ServiceConfig


if IS_LINUX or IS_OSX:
    def get_supeprvisord_conf_path():
        """Get path and file extension of the supervisor services.
        Returns:
          tuple:Path to the supervisor service configs directory and
           extension of configuration files of the supervisor services.

        """
        from supervisor.options import Options
        from ConfigParser import ConfigParser, NoSectionError, NoOptionError
        sprv_opt = Options()
        sprv_cfg_path = sprv_opt.default_configfile()
        if not sprv_cfg_path:
            msg = ('ERROR: No config file of supervisord service found '
                   'at given path ({paths}). The Supervisord application '
                   'is not installed or not configured properly.'
                   'All locust service functionality are working wrong.\n')
            sys.stderr.write(msg.format(paths=', '.join(sprv_opt.searchpaths)))
            sys.stderr.write("For help, use %s -h\n" % 'sudo supervisord')
            return None, None

        cfg_parcer = ConfigParser()
        cfg_parcer.read(sprv_cfg_path)
        try:
            cfg_path, cfg_file_ext = os.path.split(cfg_parcer.get('include',
                                                                  'files'))
        except (NoSectionError, NoOptionError) as err:
            msg = ('ERROR:The Supervisord application is not installed or '
                   'not configured properly. Configuration file {path} '
                   'does not contain section - "include" or option - '
                   '"files".\nError message is - {msg}.\nAll locust '
                   'service functionality are working wrong.\n')
            sys.stderr.write(msg.format(path=sprv_cfg_path, msg=err.message))
            return None, None

        cfg_path = os.path.join(os.path.dirname(sprv_cfg_path), cfg_path)
        return cfg_path, os.path.splitext(cfg_file_ext)[1]

    SUPERVISORD_CONF_PATH, SUPERVISORD_CONF_EXT = get_supeprvisord_conf_path()

    MODULE_CFG_PATH = '/etc/locust/'

    LOG_PATH = '/var/log/locust/{name}'
    LOG_OUT_PATH = '/var/log/locust/{name}/out'
    LOG_ERR_PATH = '/var/log/locust/{name}/err'
elif IS_WINDOWS:
    # pylint: disable=F0401
    from winpaths import get_common_appdata
    MODULE_CFG_PATH = os.path.join(get_common_appdata(), 'locust')
    LOG_PATH = os.path.join(MODULE_CFG_PATH, '{name}')

CONFIG_STORAGE = ServiceConfig()
EXIT_CODE = 2
