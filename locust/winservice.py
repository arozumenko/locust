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

""" The locust agent service on Windows operating systems."""

import os
#pycharm: disable=F0401
import win32service
import servicemanager
import win32serviceutil as winsrvutil
from configobj import ConfigObj
from threading import Thread

import locust.webservice as bserver
from locust import PCKG_NAME
from locust.serviceutils import MODULE_CFG_PATH
from locust.serviceutils.winserviceutil import BaseLocustService, \
    WinServiceUtil


class ErrMsg(object):
    """Service error messages."""
    #pylint: disable=R0903
    cfg_not_exst = 'Configuration file {path} does not exist.'


class LocustService(BaseLocustService):
    """A locust service base class.

    Provides all functionality to start locust agent service as
    windows service.

    LocustService is subclass of the old style class
    win32serviceutil.ServiceFramework.
    So we we old-fashioned way and refer to the base class
    explicitly by name (which also means you have to pass self
    explicitly). For more information see
    http://docs.python.org/2/reference/datamodel.html and
    http://stackoverflow.com/questions/1713038/
    super-fails-with-error-typeerror-argument-1-must-be-type-not
    -classobj
    """
    _svc_name_ = PCKG_NAME
    _svc_display_name_ = 'The Locust agent'
    _svc_description_ = 'The Locust Web Service'

    def __init__(self, args):
        """Constructor."""
        BaseLocustService.__init__(self, args)
        self.app = bserver
        self.app_thread = None

    def svc_start(self):
        """Start a locust agent webservice."""
        cfg_file = os.path.join(MODULE_CFG_PATH, self._svc_name_ + '.conf')

        if not os.path.exists(cfg_file):
            mgs = ErrMsg.cfg_not_exst.format(path=cfg_file)
            self.log_msg(servicemanager.EVENTLOG_ERROR_TYPE,
                         servicemanager.PYS_SERVICE_STARTING, mgs)
            raise RuntimeError(mgs)

        config = ConfigObj(cfg_file)
        kwargs = config['flask']

        kwargs['use_reloader'] = False
        kwargs['debug'] = False
        kwargs['autostart'] = True
        self.app_thread = Thread(target=self.app.run, kwargs=kwargs)
        self.app_thread.start()

    def svc_stop(self):
        """Stop a locust agent webservice."""
        if isinstance(self.app_thread, Thread):
            self.app_thread.join(1)

    @staticmethod
    def svc_pause():
        """Pause a locust agent webservice."""
        pass

    @staticmethod
    def svc_continue():
        """Continue a locust agent webservice."""
        pass

    @staticmethod
    def svc_shutdown():
        """Shutdown a locust agent webservice."""
        pass


class LocustWinServiceUtil(WinServiceUtil):
    """ The locust windows service util class."""

    def __init__(self, runner, name):
        """BaseServiceUtil constructor.

        Args:
          runner (types.ClassType, types.FunctionType): Object that run
            mainloop cycle  of an service.
          name (str): Name of a service in service control
            (supervisor or pywin32).

        """
        super(LocustWinServiceUtil, self).__init__(runner, name)

    #pylint: disable=W0221
    def service_install(self, standalone=None):
        """Install a locust agent web service as windows service."""
        standalone = (1 if standalone else 0)
        kwargs = {
            'log_out_path': '',
            'log_err_path': '',
            'start_type': win32service.SERVICE_DEMAND_START,
            'standalone': standalone}
        #pylint: disable=W0142
        self._create_module_config(**kwargs)
        super(LocustWinServiceUtil, self).service_install(**kwargs)


if __name__ == '__main__':
    winsrvutil.HandleCommandLine(LocustService)
