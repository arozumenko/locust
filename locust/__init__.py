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

"""Locust init module."""
import sys
from os.path import join
from inspect import ismodule
from socket import gethostbyname, gethostname

from configobj import ConfigObj

from locust.serviceutils.serviceconfig import confobj_to_bservice_utiltmpl
from locust.common import init_module
from locust import serviceutils as lutil


PCKG_NAME = __package__
# -----------------------------------------------------------------------------
# Initialize global variables are depended on config values
#       to avoid misunderstanding at static code inspection.
# -----------------------------------------------------------------------------
LOGGING_LEVEL = LOG_PATH = WDOG_HOST = WDOG_PORT = AGENT_IP = PRJ_ID = 'init'
AGENT_HSTNM = AGENT_KEY = INF_ID = LOCUST_INFO = STANDALONE = 'init'
WEB_SRV_CFG = 'init'

# -----------------------------------------------------------------------------
#                      Predefine module config template
# -----------------------------------------------------------------------------
HOSTNAME = gethostname()
IP = gethostbyname(HOSTNAME)

# -----------------------------------------------------------------------------
#                      Define module config template
# -----------------------------------------------------------------------------
DEF_CFG = ConfigObj()
DEF_CFG['webserver'] = {
    'host': '0.0.0.0',
    'port': 6969}

DEF_CFG['general'] = {
    'log_out_path': '{log_out_path}',
    'log_err_path': '{log_err_path}'}

DEF_CFG['logging'] = {
    'path': '{log_path}',
    'level': 'error'}

# -----------------------------------------------------------------------------
#                      Define supervisor config template
# -----------------------------------------------------------------------------
SUPERV_CFG = ConfigObj()
SUPERV_CFG['program:{service_name}'] = {
    'command': 'python {service_path}',
    'user': 'root',
    'autostart': '{autostart}',
    # If false, the process will never be autorestarted.
    #
    # If unexpected, the process will be restart when the program exits with an
    # exit code that is not one of the exit codes associated with this process
    # configuration (see exitcodes in supervisord documentation).
    #
    # If true, the process will be unconditionally restarted when it exits
    # without regard to its exit code.
    'autorestart': 'unexpected',
    # If the autorestart parameter is set to unexpected, and the process exits
    # in any other way than as a result of a supervisor stop request,
    # supervisord will restart the process if it exits with an exit code that
    # is not defined in this list.
    # Default: 0,2
    # Required: No.
    # Introduced: supervisor ver 3.0
    'exitcodes': [0, 2],
    'redirect_stderr': 'true',
    'stderr_logfile': join('{log_err_path}', 'err.log'),
    'stdout_logfile': join('{log_out_path}', 'out.log'),
    'stdout_logfile_maxbytes': '100MB',
    'stdout_logfile_backups': '30',
    'stdout_capture_maxbytes': '1MB'}

# -----------------------------------------------------------------------------
#                Add default config to bserviceutil storage
# -----------------------------------------------------------------------------
lutil.CONFIG_STORAGE.add(PCKG_NAME, {
    'supervisord': confobj_to_bservice_utiltmpl(SUPERV_CFG),
    'config': confobj_to_bservice_utiltmpl(DEF_CFG)})

# -----------------------------------------------------------------------------
#               Setting real values for default module config
# -----------------------------------------------------------------------------
DEF_CFG['logging']['path'] = join(
    lutil.LOG_PATH.format(name=PCKG_NAME), PCKG_NAME + '.log')

DEF_CFG['general'] = {
    'log_out_path': lutil.LOG_OUT_PATH.format(name=PCKG_NAME),
    'log_err_path': lutil.LOG_ERR_PATH.format(name=PCKG_NAME)}

# -----------------------------------------------------------------------------
#        Setting global variables independent of the configuration file
# -----------------------------------------------------------------------------
SEND_TIMEOUT = 10
ATTEMPT = 3
EXIT_CODE = 2

# -----------------------------------------------------------------------------
#           Load module config and set depended global variables
# -----------------------------------------------------------------------------

def load_config():
    """Load locust module config and initialise global variables."""
    try:
        init_module(PCKG_NAME, lutil.MODULE_CFG_PATH,
                    [('LOGGING_LEVEL', 'logging/level'),
                     ('LOG_PATH', 'logging/path'),
                     ('WEB_SRV_CFG', 'webserver')])
    except RuntimeError as ex:
        print ex.message
        sys.exit(EXIT_CODE)

load_config()
