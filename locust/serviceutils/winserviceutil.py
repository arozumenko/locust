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

"""Service util functionality.

 This module provides  functionality that allows create, monitor
 and control a number of any locust processes by pywin32 on
 Windows operating systems.

 """

__author__ = 'Mykhailo Makovetskiy - makovetskiy@gmail.com'
import sys
import os
#pylint: disable=F0401
import win32service
import win32event
import winerror
import servicemanager
import win32serviceutil as winsrvutil
import servicemanager
from time import sleep
from sys import stdout

from locust.serviceutils import MODULE_CFG_PATH
import locust.serviceutils.baseserviceutil as baseutil


class ErrMsg(object):
    """Service error messages."""
    #pylint: disable=R0903
    operation = ('ERROR: An error occurred during the current '
                 'operation.\n.  Error code - {code}.\n '
                 'See http://msdn.microsoft.com/en-us/library/windows'
                 '/desktop/ms681381(v=vs.85).aspx for detail '
                 'information')

    rdy_installed = ('ERROR: The service {service} is already '
                     'installed. You must uninstall it before.\n')

    not_installed = ('ERROR: The specified service {service} '
                     'does not exist as an installed service.'
                     ' Install it first.\n')

    srv_disabled = ('ERROR: The specified service {service} '
                    'is disabled. Enable it first.\n')

    srv_stopped = ('ERROR: The specified service {service} is '
                   'stopped now. Start it before.\n')

    srv_active = ('ERROR: The specified service {service} is '
                  'running now. Stop it before.\n')

    unex_action = ('Service {service} is not {operation}. '
                   'Current status - "{status}" For more '
                   'information see windows system log.\n')

    unexpected_status = ('Given status {status} is unexpected. '
                         'See MSDN documetation for more information'
                         'about windows service status.\n')


class InfMsg(object):
    """Service info messages."""
    #pylint: disable=R0903
    changed_cfg = 'Config of the {service} is changed.\n'
    starting_service = 'Starting service {service}.\n'
    started_service = 'Service {service} is started.\n'
    stopping_service = 'Stop service {service}.\n'
    stopped_service = 'Service {service} is stopped.\n'
    install_service = 'Install service {name}.\n'
    installed_s_service = 'Service {name} successful installed.\n'
    removing_service = 'Removing service {name}.\n'
    removed_s_service = 'The service {name} is removed.\n'
    disabling_service = 'Disabling service {name}.\n'
    disabled_s_service = 'The Service {name} is disabled.\n'
    restarting_service = 'Restarting service {service}.\n'

    statuses = {win32service.SERVICE_STOPPED:  ('The service {name} is '
                                                'not running.\n'),
                win32service.SERVICE_STOP_PENDING: ('The service {name} '
                                                    'is stopping.\n'),
                win32service.SERVICE_START_PENDING: ('The service {name}'
                                                     ' is starting.\n'),
                win32service.SERVICE_RUNNING: ('The service {name} is '
                                               'running.\n'),
                win32service.SERVICE_PAUSED: ('The service {name} is '
                                              'paused.\n'),
                win32service.SERVICE_PAUSE_PENDING: ('The service {name}'
                                                     ' pause is pending.\n'),
                win32service.SERVICE_CONTINUE_PENDING: ('The service '
                                                        '{name} continue '
                                                        'is pending.\n')}


#pylint: disable=R0921
class BaseLocustService(winsrvutil.ServiceFramework):
    """A locust service base class.

    Provides all base functionality to start any locust service as
    windows service.

    BaselocustService is subclass of the old style class
    win32serviceutil.ServiceFramework.
    So we we old-fashioned way and refer to the base class
    explicitly by name (which also means you have to pass self
    explicitly). For more information see
    http://docs.python.org/2/reference/datamodel.html and
    http://stackoverflow.com/questions/1713038/
    super-fails-with-error-typeerror-argument-1-must-be-type-not
    -classobj

    Note: A BaseLocustService subclass must realise the following
      methods for correct work:
        * svc_start(self) - Start a locust service mainloop
        * svc_stop(self) - Stop a locust service mainloop
        * svc_pause(self) - Pause a locust service mainloop
        * svc_continue(self) - Pause a locust module mainloop.
        * svc_shutdown(self) - Pause a locust module mainloop.

    """
    _svc_name_ = 'thebaselocust'  # should be redefined in subclass
    _svc_display_name_ = 'The Base Locust service'  # Should be redefined in
                                                     # subclasses
    _svc_description_ = 'The Base Locust service'   # Should be redefined in
                                                     # subclasses
    _svc_reg_class_ = ''   # Should be redefined in subclasses

    def __init__(self, args):
        """Constructor."""
        winsrvutil.ServiceFramework.__init__(self, args)
        self.ev_stop = win32event.CreateEvent(None, 0, 0, None)
        self.ev_resume = win32event.CreateEvent(None, 0, 0, None)

    @staticmethod
    def log_info(msg):
        """Store information to log."""
        servicemanager.LogInfoMsg(str(msg))

    @staticmethod
    def log_msg(error_type, event_id, inserts):
        """Store error to log."""
        servicemanager.LogMsg(error_type, event_id, inserts)

    #pylint: disable=C0103
    def SvcDoRun(self):
        """Called  at windows service start. Start service mainloop."""
        # Pylint is disabled because windows module check in linux
        #pylint: disable=E1101
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        # Write 'started' event to the event log.
        self.log_msg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                     servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        # Call method which start service
        self.svc_start()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        win32event.WaitForSingleObject(self.ev_stop, win32event.INFINITE)

    #pylint: disable=C0103
    def SvcStop(self):
        """Stop a locust module mainloop at windows service stop.

       """
        # Pylint is disabled because windows module check in linux
        #pylint: disable=E1101
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.ev_stop)
        self.svc_stop()
        # Write 'stopped' event to the event log.
        self.log_msg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                     servicemanager.PYS_SERVICE_STOPPED, (self._svc_name_, ''))
        # Does not use code below in windows 2000 and upper
        # self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        # because application stops without problems, but reports
        # following error id = 6 msg The handle is invalid.

    #pylint: disable=C0103
    def SvcPause(self):
        """Pause windows service."""
        # Pylint is disabled because windows module check in linux
        #pylint: disable=E1101
        self.ReportServiceStatus(win32service.SERVICE_PAUSE_PENDING)
        self.svc_pause()
        # Pylint is disabled because windows module check in linux
        #pylint: disable=E1101
        self.ReportServiceStatus(win32service.SERVICE_PAUSED)

        self.log_info("The %s service has paused." % self._svc_name_)

    #pylint: disable=C0103
    def SvcContinue(self):
        """Continue windows service."""
        # Pylint is disabled because windows module check in linux
        #pylint: disable=E1101
        self.ReportServiceStatus(win32service.SERVICE_CONTINUE_PENDING)
        win32event.SetEvent(self.ev_resume)
        self.svc_continue()
        # Pylint is disabled because windows module check in linux
        #pylint: disable=E1101
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        servicemanager.LogInfoMsg(
            "The %s service has resumed." % self._svc_name_)

    #pylint: disable=C0103
    def SvcShutdown(self):
        """Shutdown windows service."""
        # Pylint is disabled because windows module check in linux
        #pylint: disable=E1101
        self.ReportServiceStatus(win32service.SERVICE_PAUSE_PENDING)
        self.svc_shutdown()
        # Pylint is disabled because windows module check in linux
        #pylint: disable=E1101
        self.ReportServiceStatus(win32service.SERVICE_PAUSED)
        servicemanager.LogInfoMsg(
            "The %s service has paused." % self._svc_name_)


class WinServiceUtil(baseutil.BaseServiceUtil):
    """ Windows service util class."""
    def __init__(self, runner, name):
        """BaseServiceUtil constructor.

        Args:
          runner (types.ClassType, types.FunctionType): Object that run
            mainloop cycle  of an service.
          name (str): Name of a service in service control
            (supervisor or pywin32).

        """
        super(WinServiceUtil, self).__init__(runner, name)
        if not issubclass(runner, BaseLocustService):
            raise ValueError(('arg "runner" must be a subclass of the '
                              'BaseLocustService class'))
        self.runner = runner
        #pylint: disable=W0212
        self.runner._svc_name_ = name

        srv_name = self.runner.__name__
        self.runner._svc_reg_class_ = '{name}.{srvname}'.format(
            name=os.path.splitext(self.runner_path)[0], srvname=srv_name)
        self.mod_conf_path = MODULE_CFG_PATH

    def _err_operation_msg(self, error, stderr=True):
        """Returns informative message by winerror.

        Args:
          error: winerror code.
          stderr (bool): Set quiet operation mode.

        Returns:
          str: Error informative message.

        """
        if error == winerror.ERROR_SERVICE_DOES_NOT_EXIST:
            msg = ErrMsg.not_installed.format(service=self.name)
        elif error == winerror.ERROR_SERVICE_DISABLED:
            msg = ErrMsg.srv_disabled.format(service=self.name)
        elif error == winerror.ERROR_SERVICE_NOT_ACTIVE:
            msg = ErrMsg.srv_stopped.format(service=self.name)
        elif error == winerror.ERROR_SERVICE_ALREADY_RUNNING:
            msg = ErrMsg.srv_active.format(service=self.name)
        else:
            msg = ErrMsg.operation.format(code=error)

        if stderr:
            sys.stderr.write(msg)
        return msg

    def _is_srv_installed(self, stderr=True):
        """Check if is a locust service installed as windows service.

        Args:
          stderr (bool): Set quiet operation mode.

        Returns:
          bool: True if a locust service installed as windows service.

        """

        is_inst, err = self._get_srv_status(stderr=False)
        if is_inst == -1:
            is_inst = not err == winerror.ERROR_SERVICE_DOES_NOT_EXIST
            if stderr:
                sys.stderr.write(self._err_operation_msg(err, stderr=False))
        return is_inst

    def _get_srv_status(self, stderr=True):
        """Get status of a installed locust service.

        See http://msdn.microsoft.com/en-us/library/windows/desktop/
        ms685996(v=vs.85).aspx for more complicated information about
        status code.

        Args:
          stderr (bool): Set quiet operation mode.


        Returns:
          tuple: Service status and error message.

        """

        err = None
        try:
            status = winsrvutil.QueryServiceStatus(self.name)[1]
        except win32service.error as err:
            status, err = -1, err[0]
            self._err_operation_msg(err, stderr=stderr)
        return status, err

    def _check_srv_status(self, status, stderr=True):
        """Check is current service status equal to given value,


        Args:
          status: Service status.
          stderr (bool): Set quiet operation mode.

        Returns:
          bool: True if service status equal given value.

        """

        checked = False
        if status is not None and -1 != status:
            result, err = self._get_srv_status(stderr=stderr)
            if not err:
                checked = (result == status)
        return checked

    def _is_srv_running(self, stderr=False):
        """Checks if a locust service running.

        Returns:
          bool: True if service running.
        """
        return self._check_srv_status(win32service.SERVICE_RUNNING,
                                      stderr=stderr)

    def _is_srv_stopped(self, stderr=False):
        """Checks if a locust service stopped.

        Returns:
          bool: True if service stopped.
        """
        return self._check_srv_status(win32service.SERVICE_STOPPED,
                                      stderr=stderr)

    def _change_service_config(self, start_type, **kwargs):
        """Change service startup option."""
        if self._is_srv_installed():
            try:
                #pylint: disable=W0212
                desk = self.runner._svc_description_
                winsrvutil.ChangeServiceConfig(self.runner._svc_reg_class_,
                                               self.runner._svc_name_,
                                               startType=start_type,
                                               description=desk,
                                               **kwargs)

                sys.stdout.write(InfMsg.changed_cfg.format(service=self.name))
            except win32service.error as err:
                sys.stderr.write(self._err_operation_msg(err[0]))

    def _continuos_check_status(self, status, counter=20, interval=0.1):
        """Check is current service status equal to given value,

         Status checks  during defined time interval.


        Args:
          status: Service status.
          counter (int): Loop counter
          interval (float): Pause time.

        Returns:
          bool: True if service status equal given value.

        """
        for _ in xrange(counter):
            if self._check_srv_status(status, stderr=False):
                return True
            sleep(interval)
        return False

    def service_start(self):
        """Start running a locust service."""
        if self._is_srv_installed():
            try:
                sys.stdout.write(InfMsg.starting_service.format(
                    service=self.name))
                winsrvutil.StartService(self.name)
                check = self._continuos_check_status(
                    win32service.SERVICE_RUNNING)

                if not check:
                    sys.stderr.write(ErrMsg.unex_action.format(
                        service=self.name,
                        operation='started',
                        status=self.service_status(stderr=False)))
                else:
                    sys.stdout.write(InfMsg.started_service.format(
                        service=self.name))
            except win32service.error as err:
                sys.stdout.write(self._err_operation_msg(err[0], stderr=False))

    def service_stop(self):
        """Stop running a locust service."""
        if self._is_srv_installed():
            try:
                sys.stdout.write(InfMsg.stopping_service.format(
                    service=self.name))
                winsrvutil.StopService(self.name)
                check = self._continuos_check_status(
                    win32service.SERVICE_STOPPED)

                if not check:
                    sys.stderr.write(ErrMsg.unex_action.format(
                        service=self.name,
                        operation='started',
                        status=self.service_status(stderr=False)))
                else:
                    sys.stdout.write(InfMsg.stopped_service.format(
                        service=self.name))
            except win32service.error as err:
                sys.stderr.write(self._err_operation_msg(err[0], stderr=False))

    def service_install(self, **kwargs):
        """Install a locust service as windows service.

        Args:
          **kwargs: Format templates arguments.

        """
        if self._is_srv_installed(stderr=False):
            sys.stderr.write(ErrMsg.rdy_installed.format(service=self.name))
        else:
            try:
                sys.stdout.write(InfMsg.install_service.format(
                    name=self.name))
                if not os.path.exists(self.key_path):
                    return "Create a secret key first"
                self._create_module_config(**kwargs)
                start_type = kwargs.pop('start_type',
                                        win32service.SERVICE_AUTO_START)
                #pylint: disable=W0212
                winsrvutil.InstallService(
                    self.runner._svc_reg_class_,
                    self.runner._svc_name_,
                    self.runner._svc_display_name_,
                    startType=start_type,
                    description=self.runner._svc_description_)
                sys.stdout.write(InfMsg.installed_s_service.format(
                    name=self.name))
                self.service_start()
            except win32service.error as err:
                sys.stderr.write(self._err_operation_msg(err[0]))

    def service_remove(self):
        """Uninstall service"""
        if self._is_srv_installed():
            stdout.write(InfMsg.removing_service.format(name=self.name))
            if self._is_srv_running():
                self.service_stop()
            try:
                winsrvutil.RemoveService(self.name)
                self._remove_module_conf()
            except win32service.error as err:
                sys.stderr.write(self._err_operation_msg(err[0]))
            sys.stdout.write(InfMsg.removed_s_service.format(
                name=self.name))

    def service_disable(self):
        """Disable a locust service"""
        sys.stdout.write(InfMsg.disabling_service.format(name=self.name))
        if self._is_srv_installed():
            if self._is_srv_running():
                self.service_stop()
            self._change_service_config(win32service.SERVICE_DISABLED,
                                        delayedstart=False)
            sys.stdout.write(InfMsg.disabled_s_service.format(
                name=self.name))

    def service_setstartauto(self):
        """Set autostart a locust service."""
        if self._is_srv_installed():
            self._change_service_config(win32service.SERVICE_AUTO_START,
                                        delayedstart=False)
        if self._is_srv_stopped():
            self.service_start()

    def service_setstartautodelayed(self):
        """Set delayed autostart a locust service."""
        if self._is_srv_installed():
            self._change_service_config(win32service.SERVICE_AUTO_START,
                                        delayedstart=True)
        if self._is_srv_stopped():
            self.service_start()

    def service_setstartmanual(self):
        """Set manual start of a locust service."""
        if self._is_srv_installed():
            self.service_stop()
            self._change_service_config(win32service.SERVICE_DEMAND_START,
                                        delayedstart=False)

    #pylint: disable=W0221
    def service_status(self, stderr=True):
        """Get status of a installed locust service.

        Args:
          stderr (bool): Set quiet operation mode.

        Returns:
          str: Supervisor status command output.

        """
        status, err = self._get_srv_status(stderr=False)
        if status in InfMsg.statuses:
            msg = InfMsg.statuses[status].format(name=self.name)
        elif status == -1:
            msg = self._err_operation_msg(err)
        else:
            msg = ErrMsg.unexpected_status.format(status=status)
        if stderr:
            sys.stdout.write(msg)
        return msg

    def service_restart(self):
        """Restart service."""
        sys.stdout.write(InfMsg.restarting_service.format(
            service=self.name))
        try:
            winsrvutil.RestartService(self.name)
        except win32service.error as err:
            self._err_operation_msg(err[0])

if __name__ == '__main__':
    winsrvutil.HandleCommandLine(BaseLocustService)
