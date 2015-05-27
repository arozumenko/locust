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

"""API point for cli command."""

from subprocess import Popen, PIPE
from time import sleep

from locust.process_tools import (list_process, get_process, kill_process,
                                  resume_process, suspend_process)
from locust.node_tools import (shutdown_node, restart_node,
                               disable_network_adapters,
                               enable_network_adapters,
                               list_network_adapters, blink_networking,
                               block_dnsname)
from locust.resource_tools import burn_cpu, burn_ram, burn_disk


class Agent(object):
    """
    Main API class to interact with system.
    All methods should return python objects according to JSON specification.
    """

    @staticmethod
    def get_process(pids=None, names=None):
        """
        Return a list of specified local processes.

        Arguments:
            pids - list of process PIDs to get;
            names - list of process names to get.

        Return:
            {list: [{process1_dict}, {process2_dict}, ..., {processN_dict}]}.

        Example:
            butcher-agent get process --pids=2993,2852 --names=firefox

        """
        if not pids and not names:
            raise TypeError('Specify at least one pid or name')
        result = get_process(pids, names)
        return dict(list=result)

    @staticmethod
    def kill_process(pids=None, names=None):
        """
        Kill specified local processes and return the result.

        Arguments:
            pids - list of process PIDs to kill;
            names - list of process names to kill.

        Return:
            {list: [{process1_dict}, {process2_dict}, ..., {processN_dict}]}.

        Example:
            butcher-agent kill process --pids=2993,2852 --name=firefox
        """
        if not pids and not names:
            raise TypeError('Specify at least one pid or name')
        result = kill_process(names, pids)
        return dict(list=result)

    @staticmethod
    def list_process():
        """
        Return a list of all local processes.

        Arguments:
            None.

        Return:
            {list: [{process1_dict}, {process2_dict}, ..., {processN_dict}]}.
        """
        result = list_process()
        return dict(list=result)

    @staticmethod
    def resume_process(pids=None, names=None):
        """
        Resume specified local processes.

        Arguments:
            pids - list of process PIDs to resume;
            names - list of process names to resume.

        Return:
            {list: [{process1_dict}, {process2_dict}, ..., {processN_dict}]}.
        """
        if not pids and not names:
            raise TypeError('Specify at least one pid or name')
        result = resume_process(names, pids)
        return dict(list=result)

    @staticmethod
    def suspend_process(pids=None, names=None):
        """
        Suspend specified local processes.

        Arguments:
            pids - list of process PIDs to suspend;
            names - list of process names to suspend.

        Return:
            {list: [{process1_dict}, {process2_dict}, ..., {processN_dict}]}.
        """
        if not pids and not names:
            raise TypeError('Specify at least one pid or name')
        result = suspend_process(names, pids)
        return dict(list=result)

    @staticmethod
    def shutdown_node():
        """Shutdown local node."""
        return shutdown_node()

    @staticmethod
    def restart_node():
        """Restart local node."""
        return restart_node()

    @staticmethod
    def disable_network_adapters(adapters, timeout=30):
        """
        Disable network adapters.

        Arguments:
            adapters - list of network adapters to disable;
            timeout - duration of disabling network adapters. If not
                      specified - adapter(s) will be disable permanently.
        """
        return disable_network_adapters(adapters, timeout)

    @staticmethod
    def enable_network_adapters(adapters=None):
        """
        Enable network adapters.

        Arguments:
            adapters - list of network adapters to disable. All by default.
        """
        return enable_network_adapters(adapters)

    @staticmethod
    def list_network_adapters():
        """ Return list of network adapters. """
        return list_network_adapters()

    @staticmethod
    def blink_networking(enable_network_timeout,
                         disable_network_timeout,
                         adapters=None, work_time=30):
        """
        Blink network adapters.

        Arguments:
            adapters - list of network adapters to blink.
                       If list is empty, all adapters will be blink;
            enable_network_timeout - timeout when adapters will be enable;
            disable_network_timeout - timeout when adapters will be disable;
            work_time - duration of blink networking.

        Example:
            butcher-agent blink networking 10 5 --adapters=eth0 --work_time=30

        """
        return blink_networking(enable_network_timeout,
                                disable_network_timeout,
                                adapters=adapters, timeout=work_time)

    @staticmethod
    def burn_cpu(timeout=30):
        """
        Burn CPU.

        Arguments:
            timeout: - time of CPU to be burned (Default: 30 sec)
        :return:
            Returns message that burning started.
        """
        return burn_cpu(timeout=timeout)

    @staticmethod
    def burn_ram(timeout=30):
        """
        RAM overflow

        Arguments:
            timeout: - time of RAM to be overflowed (Default: 30 sec)
        Return:
            Returns message that overflowing started.
        """
        return burn_ram(timeout=timeout)

    @staticmethod
    def burn_disk(timeout=30, file_size='1k', thread_limit='200'):
        """Burn HDD command.

        Arguments:
            timeout - length of time in seconds to burn HDD (Default: 30 sec);
            file_size - file size to be created in thread;
            thread_limit - thread limit count per process;
        Return:
            Returns message that burn HDD is started.
        """
        return burn_disk(timeout=timeout, file_size=file_size,
                         thread_limit=thread_limit)

    @staticmethod
    def exec_command(cmd, result_should_contain=None,
                     result_should_not_contain=None):
        """
        execute shell/batch command on host.

        Arguments:
            cmd - String representation of command to be executed (e.g. 'pwd')
            result_should_contain - optional argument to pass string
                                    that must be in result;
            result_should_not_contain - optional argument to pass string
                                        that must be not presented in result.

        Example:
            butcher-agent exec command 'pwd' --result_should_contain='home'
        """
        # http://stackoverflow.com/questions/14280372/pylint-false-positive-
        # e1101-instance-of-popen-has-no-poll-member
        #pylint: disable=E1101
        res = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        for _ in range(60):
            if not res.poll():
                break
            sleep(0.5)
        else:
            res.kill()
        data = res.communicate()
        data_result = data[0]
        data_result += data[1]
        result = {
            "cmd": cmd,
            "result": data[0][:-1],
            "error": data[1]
        }

        chk = lambda x: x in data_result
        if result_should_contain:
            result['result_should_contain'] = chk(result_should_contain)
        if result_should_not_contain:
            result['result_should_not_contain'] = not chk(
                result_should_not_contain)
        return result

    @staticmethod
    def block_dnsname(dnsname, timeout=30):
        """
        Redirect dnsname to localhost

        Arguments:
            dnsname - list of DNS names that will be redirected to localhost
            timeout - how long changes will take affect
        """
        return block_dnsname(dnsname, timeout=timeout)
