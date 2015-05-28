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

"""Service util functionality. """

__author__ = 'Mykhailo Makovetskiy - makovetskiy@gmail.com'
import os
import sys
from subprocess import Popen
from time import sleep
from copy import deepcopy

from configobj import ConfigObj

import locust.serviceutils.baseserviceutil as baseutil
from locust.serviceutils import (SUPERVISORD_CONF_PATH, SUPERVISORD_CONF_EXT,
                                 CONFIG_STORAGE, EXIT_CODE)
from locust.serviceutils.baseserviceutil import ErrMsg as BaseErrMsg


SUPERV_CMD_TMPL = {'add': 'supervisorctl add {name}',
                   'avail': 'supervisorctl avail',
                   'remove': 'supervisorctl remove {name}',
                   'start': 'supervisorctl start {name}',
                   'stop': 'supervisorctl stop {name}',
                   'status': 'supervisorctl status {name}',
                   'restart': 'supervisorctl restart {name}',
                   'reload': 'supervisorctl reload',
                   'reread': 'supervisorctl reread',
                   'update': 'supervisorctl update'}


#pylint: disable=R0903
class ErrMsg(object):
    """Service error messages."""

    bad_super_cmd = ('Supervisor application does not contains given '
                     'command = {cmd}.\n Available command:\n{cmds}\n')

    srv_no_installed = ('ERROR: The service {name} is not installed. '
                        'Run command install before\n')


#pylint: disable=R0921
class UnixServiceUtil(baseutil.BaseServiceUtil):
    """ Unix service util class.

    Provides  functionality that allows to create, monitor and control a
    number of any locust processes by supervisor on UNIX-like operating
    systems.

    Note:
      UnixServiceUtil subclasess can realise the following methods:
       enable(self) - Enable autostart locust service at
                          supervisor start.
       disable(self) - Disable autostart locust service at supervisor
                       start.

    """
    def __init__(self, runner, name):
        """UnixServiceUtil constructor.

        Args:
          runner (types.ClassType, types.FunctionType): Object that run
            mainloop cycle  of an service.
          name (str): Name of a service in supervisor.

        """
        super(UnixServiceUtil, self).__init__(runner, name)
        self.cmds = dict((k, v.format(name=name)) for k, v
                         in SUPERV_CMD_TMPL.items())

        self.super_conf_path = SUPERVISORD_CONF_PATH
        self.super_conf_ext = SUPERVISORD_CONF_EXT

    def _check_supervisord_path(self):
        """Check if Supervisor is installed properly."""
        if self.super_conf_path is None:
            sys.stderr.write(('The Supervisord config does not exist or'
                              'wrong. The Supervisord application is not '
                              'installed or not configured properly.'))
            sys.exit(EXIT_CODE)

    def _create_supervisord_config(self, **kwargs):
        """Create a locust module supervisor configuration file.

        Templates is placed in global CFG_TML object. CFG_TML is
        instance of ServiceConfig class from serviceconfig.

        Args:
          **kwargs: Format template arguments.

        """

        self._check_supervisord_path()
        self._create_config('supervisord', self.super_conf_path,
                            self.super_conf_ext, **kwargs)

    def _remove_supervisord_conf(self):
        """Remove a locust module supervisor configuration file."""
        self._check_supervisord_path()
        cfg_file = os.path.join(self.super_conf_path,
                                self.name + self.super_conf_ext)
        self._rm(cfg_file, del_empty_par_dir=False)

    def _is_installed(self, stderr=True):
        """Checks if a locust service is installed in supervisor.

        Args:
          stderr (bool): Set quiet check validation if False.

        Returns:
          bool: True if a locust service is installed.
        """
        echo = self._avail_srv()
        installed = True if self.name in echo else False
        if not installed and stderr:
            sys.stderr.write(ErrMsg.srv_no_installed.format(name=self.name))
        return installed

    def _runsupervisor_cmd(self, command, stderr=True):
        """Run supervisor shell command.

        Args:
          command (str): supervisor command.
          stderr (bool): Set quiet check validation if False.

        Returns:
          str: Supervisor command output.
        """
        cmd = str(command)
        if cmd not in self.cmds:
            commands = '\n'.join(SUPERV_CMD_TMPL.keys())
            sys.stderr.write(ErrMsg.bad_super_cmd.format(cmd=cmd,
                                                         cmds=commands))
            return
        try:
            echo = Popen(self.cmds[command].split(' '), stdout=-1,
                         stderr=-2)
            echo = echo.communicate()[0]
        except OSError as err:
            msg = ('ERROR: During run command - {cmd} shell returns error '
                   '- {err}.\n')
            sys.stderr.write(msg.format(cmd=command, err=str(err.message)))
            sys.exit(EXIT_CODE)
        if stderr:
            sys.stdout.write(str(echo))
        return echo

    def _avail_srv(self):
        """Return available supervisor process.

        Returns:
          str: Supervisor available command output.

         """
        return self._runsupervisor_cmd('avail', stderr=False)

    def _add_srv(self):
        """Add process to the supervisor .

        Returns:
          str: Supervisor add command output.

         """
        return self._runsupervisor_cmd('add')

    def _reread(self):
        """Update configs all process controlled by supervisor.

        Configs updates without process restart.

        Returns:
          str: Supervisor reread command output.

        """
        return self._runsupervisor_cmd('reread')

    def _remove(self):
        """Remove a locust service from supervisor.

        Returns:
          str: Supervisor remove command output.

        """
        return self._runsupervisor_cmd('remove')

    def _reload(self):
        """Remove a locust process from supervisor.

        Returns:
          str: Supervisor reread command output.

        """
        return self._runsupervisor_cmd('reload')

    def _is_running(self):
        """Checks if a supervisor locust service running.

        Returns:
          bool: True if service running.
        """
        return 'RUNNING' in self._runsupervisor_cmd('status', stderr=False)

    def _is_stopped(self):
        """Checks if a supervisor locust service stopped.

        Returns:
          bool: True if service stopped.
        """
        return 'Stopped' in self._runsupervisor_cmd('status', stderr=False)

    def service_install(self, **kwargs):
        """Install a locust service into supervisor.

        Args:
          **kwargs: Format templates arguments.
        """

        if self._is_installed(stderr=False):
            self.service_remove()
        if not os.path.exists(self.key_path):
            return "Create a secret key first"
        self._create_module_config(**kwargs)
        self._create_supervisord_config(**kwargs)

        self._reread()
        self._add_srv()
        self._reload()

    def _update(self):
        """Restarts the service whose configuration has changed.

        Configs updates without process restart.

        Returns:
          str: Supervisor update command output.

        """
        return self._runsupervisor_cmd('update')

    def service_stop(self):
        """Stop running locust service.

        Returns:
          str: Supervisor stop command output.

        """
        return self._runsupervisor_cmd('stop')

    def service_start(self):
        """Start running locust service.

        Returns:
          str: Supervisor start command output.

        """
        return self._runsupervisor_cmd('start')

    def service_restart(self):
        """Restart service without making configuration changes.

        It stops, and re-starts all managed applications.

        Returns:
          str: Supervisor start command output.

        """
        return self._runsupervisor_cmd('restart')

    def service_status(self):
        """Get status of a installed locust service.

        Returns:
          str: Supervisor status command output.

        """
        return self._runsupervisor_cmd('status')

    def service_remove(self):
        """Remove a locust service ."""
        if self._is_installed():
            if self._is_running():
                self.service_stop()
            self._remove()
            self._remove_supervisord_conf()
            self._remove_secure_key()
            self._remove_module_conf()
            self._reload()


class LocustService(UnixServiceUtil):
    """The locust agent Unix supervisor service util."""
    TIMEOUT_DELTA = 0.5  # second

    def __init__(self, runner, name, **kwargs):
        """Constructor.

        Args:
          runner (types.ClassType, types.FunctionType): Object that run
            mainloop cycle  of an service.
          name (str): Name of a service in supervisor.
          kwargs (dict): Install options.

        """
        self.install_opt = kwargs or {}
        super(LocustService, self).__init__(runner, name)
        self.install_opt['service_name'] = self.name
        self.install_opt['service_path'] = self.runner_path

    # pylint: disable=W0221
    def service_install(self, **kwargs):
        """Install a locust module as supervisor service.

        Args:
          **kwargs: Custom install options.

        """
        inst_opt = deepcopy(self.install_opt)
        inst_opt.update(kwargs)

        # pylint: disable=W0142
        print super(LocustService, self).service_install(**inst_opt)

    def _change_supervisor_autostart(self, value):
        """ Change autostart parameter in supervisor config file."""
        cfg_path = os.path.join(self.super_conf_path,
                                self.name + self.super_conf_ext)
        section = CONFIG_STORAGE.get_config(self.name, 'supervisord')
        if not section:
            sys.stderr.write(BaseErrMsg.cfg_tmpl_key.format(
                cfg=self.name, name='supervisord'))
            sys.exit(EXIT_CODE)
        section = section[0]['section'].format(service_name=self.name)
        self._change_cfg_prm(cfg_path, section, 'autostart', value)

    def service_disable(self):
        """Disable autostart the locust agent service."""
        if self._is_installed():
            if self._is_running():
                self.service_stop()
            self._change_supervisor_autostart('false')

    def service_enable(self):
        """Enable autostart the locust agent service."""
        if self._is_installed():
            if self._is_running():
                self.service_stop()
            self._change_supervisor_autostart('true')
            self.service_start()

    def service_start(self):
        """Start the locust agent service."""
        if self._is_installed(stderr=False):
            mconf = os.path.join(self.mod_conf_path,
                                 self.name + self.mod_conf_ext)
            msg = 'Config file {path} does not exist'.format(
                path=mconf)
            assert os.path.exists(mconf), msg
            mconf = ConfigObj(mconf)
            if not self._is_running():
                kwargs = deepcopy(self.install_opt)
                kwargs.update(
                    {'log_out_path': mconf['general']['log_out_path'],
                     'log_err_path': mconf['general']['log_err_path'],
                     'autostart': True})
                if not os.path.exists(kwargs['log_out_path']):
                    os.makedirs(kwargs['log_out_path'])

                if not os.path.exists(kwargs['log_err_path']):
                    os.makedirs(kwargs['log_err_path'])
                # pylint: disable=W0142
                self._create_supervisord_config(**kwargs)
            super(LocustService, self).service_start()
            print 'checking status...'
            # Timeout before check real service status should be more then
            # 'startsecs'(default value is 1 sec) option value  described in
            # process supervisor config file;
            # This functionality has moved to the end of class bserviceutil
            # since other modules may not need it.
            timeout = mconf['startsecs'] if 'startsecs' in mconf else 1.0
            timeout += self.TIMEOUT_DELTA
            sleep(timeout)
            self.service_status()

    def service_restart(self):
        """Restart the locust agent service."""
        self.service_stop()
        self.service_start()
