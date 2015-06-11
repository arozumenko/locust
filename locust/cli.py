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

"""CLI module for bagent."""
#pylint W:  3, 0: Redefining built-in 'exit' (redefined-builtin)
# so we import sys
import sys
import locust.serviceutils as lutil
from locust.api import Agent
from locust import PCKG_NAME, EXIT_CODE
from locust.common.cli_commands_generator import cli_main
from locust.common import IS_LINUX, IS_WINDOWS, IS_OSX
from locust.common import is_sudoer, check_folder
from os.path import join

if IS_WINDOWS:
    from locust.winservice import LocustWinServiceUtil as Service
    from locust.winservice import LocustService as runner
elif IS_LINUX or IS_OSX:
    from locust.serviceutils.unixserviceutil import LocustService as Service
    from locust.webservice import run as runner
else:
    print "ERROR: Not supported os.\nAborting..."
    sys.exit(EXIT_CODE)


def main():
    """Main method."""
    if not is_sudoer(stderr=True):
        sys.exit(EXIT_CODE)

    paths = (lutil.LOG_OUT_PATH.format(name=PCKG_NAME),
             lutil.LOG_ERR_PATH.format(name=PCKG_NAME),
             lutil.LOG_PATH.format(name=PCKG_NAME))
    for path in paths:
        check_folder(path)
    install_options = {'log_out_path': paths[0],
                       'log_err_path': paths[1],
                       'log_path': join(paths[2], PCKG_NAME + '.log'),
                       'autostart': False,
                       'standalone': True}

    class Lservice(Service):
        """ The bagent module service util."""

        def service_install(self, standalone=True):
            """Install the bagent module as supervisor service.

            Args:
              standalone (bool): Webservice starts immediately if true else
                registration require.

            """
            #pylint: disable=W0142
            super(Lservice, self).service_install(**{'standalone': standalone})

    #pylint: disable=W0142
    try:
        cli_main([(Lservice(runner, PCKG_NAME, **install_options), False),
                  (Agent(), True)], sys.argv)
    except TypeError as ex:
        print 'ERROR: Got unexpected behaviour ' + str(ex.message)
        sys.exit(EXIT_CODE)

if __name__ == '__main__':
    main()
