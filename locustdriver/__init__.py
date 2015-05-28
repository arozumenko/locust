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

"""Locust Driver module."""
#pylint: disable=too-many-arguments,too-many-locals,unused-argument
from urllib2 import urlopen, HTTPError, Request
from hashlib import sha256
from json import dumps, loads
from time import sleep


DEF_TIMEOUT = 60


class LocustDriver(object):
    """
    {"nodes":{"zzzz":"yyy.yyy.yyy.yyy"}
    "node_groups":{"group1":["zzzz","yyyy"]}
    "keys":{"zzzzz":"yyyyyyy"}}
    """

    def __init__(self, nodes=None):
        self.nodes = nodes if nodes else {}

    #------------------------------------------------------------------
    # Driver section
    #------------------------------------------------------------------
    def add_node(self, node_name='', node_ip='', node_group='', key=''):
        """Adding node for tests."""
        def add(_node_name, _node_ip, _node_group, _key):
            """Internal method for adding nodes parameters to self.nodes."""
            if _node_group in self.nodes['node_groups']:
                self.nodes['node_groups'][_node_group].append(_node_name)
            else:
                self.nodes['node_groups'][_node_group] = [_node_name]
            self.nodes['nodes'][_node_name] = _node_ip
            self.nodes['keys'][_node_name] = _key

        if not self.nodes:
            self.nodes = {
                'nodes': {},
                'node_groups': {},
                'keys': {}
            }
        add(node_name, node_ip, node_group, key)

    def _prepare_nodes(self, nodes=None, node_groups=None):
        """ prepare nodes before test execution """
        if not self.nodes:
            raise NameError('Nodes not initialized')
        output = {}
        node_groups = [node_groups] if not isinstance(node_groups, list) else \
            node_groups
        nodes = [nodes] if not isinstance(nodes, list) else nodes
        if node_groups:
            for each in node_groups:
                if each in self.nodes['node_groups']:
                    for every in self.nodes['node_groups'][each]:
                        output[every] = self.nodes['nodes'][every]
        if nodes:
            for each in nodes:
                if each in self.nodes['nodes'] and each not in output:
                    output[each] = self.nodes['nodes'][each]
        if not (nodes or node_groups):
            output = self.nodes['nodes']
        print output
        return output

    @staticmethod
    def _send_command(ip_address, data):
        """Internal send command method."""
        try:
            data = dumps(data) if data else None
            if not ip_address.startswith('http://'):
                ip_address = 'http://' + ip_address
            headers = {"Content-Type": "application/json"}
            request = Request(ip_address, data=data, headers=headers)
            result = urlopen(request).read()
            result = result.replace('true', '1').replace('false', '0')\
                .replace('null', '""')
            return result
        except HTTPError as error:
            return error.read()

    def _basic_cmd(self, command='', nodes=None, node_groups=None, pids=None,
                   names=None, adapters=None, timeout=0,
                   disable_network_timeout=0, enable_network_timeout=0,
                   cmd='', result_should_contain='',
                   result_should_not_contain='', file_size=None,
                   thread_limit=None, dnsname=''):
        """
        Basic command method. It takes bunch of args specific sets is
        applied to specific methods.

        Arguments:
            command - name of method to be executed
            nodes - used for identification of nodes to be run on
            node_groups - used for identification of node_groups to be run on
            pids - pids of processed for *_process commands
            names - names of processed for *_process commands
            adapters - names of adapters for *_network commands
            timeout - for bunch of commands with pauses
            disable_network_timeout - timeout for disabling network
            disable_network_timeout - timeout for enabling network
            cmd - for exec_command
            result_should_contain - validation for in
            result_should_not_contain - validation for not in
            file_size - for burn_hdd
            thread_limit - for burn_hdd

        Returns:
            Execution result
        """
        assert bool(command), 'The "command" parametr couldn\'t be empty.'
        chk = lambda x, y: y and x not in ['self', 'nodes', 'node_groups',
                                           'chk']
        args = dict((k, v) for k, v in locals().items() if chk(k, v))
        data = dict(command=args.pop('command'), arguments=args)

        if not isinstance(nodes, list) and nodes:
            nodes = [nodes]
        work_nodes = self._prepare_nodes(nodes, node_groups)
        result = {}
        for key, value in work_nodes.items():
            data['key'] = sha256(self.nodes['keys'][key]).hexdigest()
            result[key] = loads(self._send_command(value, data))
        print data
        return result

    #------------------------------------------------------------------
    # Process tools section
    #------------------------------------------------------------------
    def get_process(self, nodes=None, node_groups=None, pids=None, names=None):
        """
        Return a list of specified local processes.

        Arguments:
            nodes - list of nodes to execute command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            pids - list of process PIDs to get;
            names - list of process names to get.
        Return:
            {list: [{process1_dict}, {process2_dict}, ..., {processN_dict}]}.
        """
        return self._basic_cmd('get_process', nodes, node_groups, pids, names)

    def wait_for_process(self, nodes=None, node_groups=None, pids=None,
                         names=None, timeout=60):
        """
        Waits for <timeout> seconds for process to appear

        Arguments:
            nodes - list of nodes to execute command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            pids - list of process PIDs to get;
            names - list of process names to get.
            timeout - seconds of wait
        Return:
            {list: [{process1_dict}, {process2_dict}, ..., {processN_dict}]}.
            or
            {list: []}
        """
        for _ in range(timeout):
            proc_list = self._basic_cmd('get_process', nodes, node_groups,
                                        pids, names)
            if isinstance(proc_list, dict) and 'list' in proc_list and \
                    proc_list['list']:
                return proc_list
            sleep(1)
        else:
            return {'list': []}

    def kill_process(self, nodes=None, node_groups=None, pids=None,
                     names=None):
        """
        Kill specified local processes and return the result.

        Arguments:
            nodes - list of nodes to execute command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            pids - list of process PIDs to kill;
            names - list of process names to kill.

        Return:
            {list: [{process1_dict}, {process2_dict}, ..., {processN_dict}]}.
        """
        return self._basic_cmd('kill_process', nodes, node_groups, pids, names)

    def list_process(self, nodes=None, node_groups=None):
        """
        Return a list of all local processes.

        Arguments:
                nodes - list of nodes to execute command
                        (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
                node_groups - list of node groups to execute COMMANDS

        Return:
            A list of process dicts.
        """
        return self._basic_cmd('list_process', nodes, node_groups)

    def resume_process(self, nodes=None, node_groups=None, pids=None,
                       names=None):
        """
        Resume specified local processes.

        Arguments:
            nodes - list of nodes to execute get_process command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            pids - list of process PIDs to resume;
            names - list of process names to resume.

        Return:
            {list: [{process1_dict}, {process2_dict}, ..., {processN_dict}]}.
        """
        return self._basic_cmd('resume_process', nodes, node_groups, pids,
                               names)

    def suspend_process(self, nodes=None, node_groups=None, pids=None,
                        names=None):
        """
        Suspend specified local processes.

        Arguments:
            nodes - list of nodes to execute get_process command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            pids - list of process PIDs to suspend;
            names - list of process names to suspend.

        Return:
            {list: [{process1_dict}, {process2_dict}, ..., {processN_dict}]}.
        """
        return self._basic_cmd('suspend_process', nodes, node_groups, pids,
                               names)

    def exec_command(self, nodes=None, node_groups=None, cmd='',
                     result_should_contain='', result_should_not_contain=''):
        """
        execute shell/batch command on host.

        Arguments:
            nodes - list of nodes to execute get_process command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            cmd - String representation of command to be executed (e.g. 'pwd')
            result_contain - optional argument to pass string
                             that must be in result
            result_not_contain - optional argument to pass string
            that must be not presented in result
        """
        if not cmd:
            raise KeyError('cmd: command is not specified')
        return self._basic_cmd('exec_command', nodes=nodes,
                               node_groups=node_groups, cmd=cmd,
                               result_should_contain=result_should_contain,
                               result_should_not_contain=
                               result_should_not_contain)

    #------------------------------------------------------------------
    # Node tools section
    #------------------------------------------------------------------
    def shutdown_node(self, nodes=None, node_groups=None):
        """
        Shutdown local node.

        Arguments:
                nodes - list of nodes to execute get_process command
                        (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
                node_groups - list of node groups to execute COMMANDS
        """
        return self._basic_cmd('shutdown_node', nodes, node_groups)

    def restart_node(self, nodes=None, node_groups=None):
        """
        Restart local node.

        Arguments:
                nodes - list of nodes to execute get_process command
                        (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
                node_groups - list of node groups to execute COMMANDS
        """
        return self._basic_cmd('restart_node', nodes, node_groups)

    def disable_network_adapters(self, nodes=None, node_groups=None,
                                 adapters=None,
                                 timeout=DEF_TIMEOUT):
        """
        Disable network adapters.

        Arguments:
            nodes - list of nodes to execute get_process command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            adapters - list of network adapters to disable. All by default.
            timeout - amount of seconds while network adapters will be disabled
                      Default: 60.
        """
        return self._basic_cmd('disable_network_adapters', nodes=nodes,
                               node_groups=node_groups, adapters=adapters,
                               timeout=timeout)

    def enable_network_adapters(self, nodes=None, node_groups=None,
                                adapters=None):
        """
        Enable network adapters.

        Arguments:
            nodes - list of nodes to execute get_process command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            adapters - list of network adapters to disable. All by default.
        """
        return self._basic_cmd('enable_network_adapters', nodes=nodes,
                               node_groups=node_groups, adapters=adapters)

    def list_network_adapters(self, nodes=None, node_groups=None):
        """
        Return list of network adapters.
        Arguments:
            nodes - list of nodes to execute get_process command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
        Return: a list of network adapters dicts.
        """
        return self._basic_cmd('list_network_adapters', nodes, node_groups)

    def blink_networking(self, nodes=None, node_groups=None,
                         disable_network_timeout=10, enable_network_timeout=10,
                         adapters=None, timeout=DEF_TIMEOUT):
        """
        Blink network adapters.

        Arguments:
            nodes - list of nodes to execute get_process command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            adapters - list of network adapters to blink.
                        If list is empty, all adapters will be disabled.
            enable_network_timeout - timeout when adapters will be enable
            disable_network_timeout - timeout when adapters will be disable
            timeout - amount of seconds while network will be disabled.
                        Default value - 60.
        """
        return self._basic_cmd('blink_networking', nodes=nodes,
                               node_groups=node_groups,
                               adapters=adapters,
                               timeout=timeout,
                               disable_network_timeout=disable_network_timeout,
                               enable_network_timeout=enable_network_timeout)

    def block_dnsname(self, nodes=None, node_groups=None, dnsname=None,
                      timeout=DEF_TIMEOUT):
        """
        Redirect dnsname to localhost

        Arguments:
            nodes - list of nodes to execute get_process command;
            node_groups - list of node groups to execute COMMANDS;
            dnsname - list of DNS names that will be redirected to localhost;
            timeout - how long changes will take affect. Default timeout=60.
        """
        return self._basic_cmd('block_dnsname', nodes=nodes,
                               node_groups=node_groups, dnsname=dnsname,
                               timeout=timeout)

    #------------------------------------------------------------------
    # Resource tools section
    #------------------------------------------------------------------
    def burn_cpu(self, nodes=None, node_groups=None, timeout=DEF_TIMEOUT):
        """
        Burn CPU method

        Arguments:
            nodes - list of nodes to execute get_process command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            timeout - time of CPU to spin on 100% (default: 60 seconds)
        """
        return self._basic_cmd('burn_cpu', nodes=nodes,
                               node_groups=node_groups, timeout=timeout)

    def burn_ram(self, nodes=None, node_groups=None, timeout=DEF_TIMEOUT):
        """
        Burn RAM method

        Arguments:
            nodes - list of nodes to execute get_process command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            timeout - time of RAM to be occupied on 100% (default: 60 seconds)
        """
        return self._basic_cmd('burn_ram', nodes=nodes,
                               node_groups=node_groups, timeout=timeout)

    def burn_disk(self, nodes=None, node_groups=None, timeout=DEF_TIMEOUT,
                  file_size='1k', thread_limit=200):
        """
        Burn Disk Read/Write operations method

        Arguments:
            nodes - list of nodes to execute get_process command
                    (eg. ["192.168.0.1:8080","192.168.0.1:4444"])
            node_groups - list of node groups to execute COMMANDS
            timeout - time of Disk to be busy (default: 60 seconds)
            file_size - size of files to be created (default: 1k file)
            thread_limit - Number of threads to be spawned simultaneously
            (default: 200)
        """
        return self._basic_cmd('burn_ram', nodes=nodes,
                               node_groups=node_groups, timeout=timeout,
                               file_size=file_size, thread_limit=thread_limit)
