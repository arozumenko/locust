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


"""Node tools command."""

from os import system, path, sep
from time import time, sleep
from threading import Thread
from inspect import isfunction

from locust.common import (parse_args_list, message_wrapper, sudo_require,
                           convert_timeout)
from locust.common import IS_WINDOWS


if IS_WINDOWS:
    #pylint: disable=F0401
    from win32api import GetSystemDirectory as sys_path
else:
    #pylint: disable=E0611
    from netifaces import interfaces


def _run_thread(target, args=None, ret_msg=''):
    """Run given function in separate Thread """
    assert isfunction(target), "Target should be a function"
    args = args or ()
    assert isinstance(args, tuple), "Args should be a tuple or empty"
    thread = Thread(target=target, args=args)
    thread.start()
    return message_wrapper(ret_msg)


@sudo_require
def shutdown_node():
    """Shutdown local node."""
    return _run_thread(_shutdown_node, ret_msg='Node is shut down')


def _shutdown_node():
    """Shutdown local node."""
    sleep(3)
    if IS_WINDOWS:
        system("shutdown /p /f")
    else:
        system("shutdown -h now")


@sudo_require
def restart_node():
    """Restart local node."""
    return _run_thread(_restart_node, ret_msg='Node is restarted')


def _restart_node():
    """Restart local node in thread."""
    sleep(3)
    if IS_WINDOWS:
        system("shutdown /r /f")
    else:
        system("shutdown -r now")


@sudo_require
def disable_network_adapters(adapters=None, timeout=0):
    """
    Disable network adapters.

        Arguments:
            adapters - list of network adapters to disable.
                        If list is empty, all adapters will be disabled.
            timeout - amount of seconds while network adapters will be disabled
                        Default value - 0.
    """
    timeout = convert_timeout(timeout, def_timeout=0)
    adapters = parse_args_list(adapters)
    return _run_thread(_disable_network_adapters, args=(adapters, timeout),
                       ret_msg='Network adapter is disabled')


@sudo_require
def enable_network_adapters(adapters=None):
    """
    Enable network adapters.

        Arguments:
            adapters - list of network adapters to disable.
                        If list is empty, all adapters will be enabled.
    """
    loc_adapters = parse_args_list([] if adapters is None else adapters)
    result = True
    if IS_WINDOWS:
        cmd_ptrn = 'wmic path win32_networkadapter ' \
                   'where PhysicalAdapter=True call enable'
        if loc_adapters:
            cmd_ptrn = 'netsh interface set interface name="{name}" ' \
                       'admin=enabled'
    else:
        cmd_ptrn = 'ifconfig {name} up'
        # Ubuntu bug: https://bugs.launchpad.net/ubuntu/
        # +source/gnome-settings-daemon/+bug/1072518
        # os.system('service networking restart')
        if not loc_adapters:
            loc_adapters = interfaces()

    if loc_adapters:
        for adapter in loc_adapters:
            retcode = system(cmd_ptrn.format(name=adapter))
            if retcode != 0:
                result = False
    else:
        #compare operation return bool value
        result = 0 == system(cmd_ptrn)

    if result:
        return message_wrapper('Network adapter is enabled')
    return message_wrapper('Network adapter is not enabled', status='error')


def _disable_network_adapters(adapters=None, timeout=0):
    """
    Disable network adapters.

        Arguments:
            adapters - list of network adapters to disable.
                        If list is empty, all adapters will be disabled.
            timeout - amount of seconds while network adapters will be disabled
                        Default value - 0.
    """
    sleep(3)
    if IS_WINDOWS:
        cmd_ptrn = 'wmic path win32_networkadapter ' \
                   'where PhysicalAdapter=True call disable'
        if adapters:
            cmd_ptrn = 'netsh interface set interface name="{name}" ' \
                       'admin=disabled'
    else:
        cmd_ptrn = 'ifconfig {name} down'
        if not adapters:
            adapters = interfaces()

    if adapters:
        for adapter in adapters:
            system(cmd_ptrn.format(name=adapter))
    else:
        system(cmd_ptrn)

    if timeout:
        sleep(timeout)
        enable_network_adapters(adapters)


@sudo_require
def list_network_adapters():
    """
    Return list of network adapters.

    Argument:
        None
    Return:
        List of network adapters dicts.
    """
    if IS_WINDOWS:
        #pylint: disable=F0401
        from wmi import WMI
        query = "select * from Win32_NetworkAdapter where PhysicalAdapter=TRUE"
        result = WMI().query(query)
        net_adapters = [i.NetConnectionID for i in result if i.PhysicalAdapter]
    else:
        net_adapters = interfaces()
    return net_adapters


@sudo_require
def blink_networking(enable_network_timeout, disable_network_timeout,
                     adapters=None, timeout=30):
    """
    Blink network adapters.

    Arguments:
        adapters - list of network adapters to blink;
                   If list is empty, all adapters will be disabled;
        enable_network_timeout - timeout when adapters will be enable;
        disable_network_timeout - timeout when adapters will be disable;
        work_time - duration of blink networking.

    Example:
        butcher-agent blink networking 10 5 --adapters=eth0 --work_time=30

    """
    adapters = parse_args_list(adapters)
    timeout = convert_timeout(timeout, def_timeout=0)
    enable_network_timeout = convert_timeout(enable_network_timeout,
                                             def_timeout=1)
    disable_network_timeout = convert_timeout(disable_network_timeout,
                                              def_timeout=1)
    return _run_thread(_blink_networking, args=(enable_network_timeout,
                                                disable_network_timeout,
                                                adapters, timeout),
                       ret_msg='Network blinking is started')


def _blink_networking(enable_network_timeout, disable_network_timeout,
                      adapters=None, timeout=0):
    """
    Blink network adapters.

        Arguments:
            adapters - list of network adapters to blink.
                        If list is empty, all adapters will be disabled.
            enable_network_timeout - timeout when adapters will be enable
            disable_network_timeout - timeout when adapters will be disable
            timeout - amount of seconds while adapters will be disabled.
                        Default value - 0.
    """
    sleep(3)
    if timeout:
        end_time = time() + timeout
    else:
        end_time = time()
    while True:
        _disable_network_adapters(adapters=adapters,
                                  timeout=disable_network_timeout)
        sleep(enable_network_timeout)
        if time() > end_time:
            break
    return message_wrapper('Network blinking is finished')


@sudo_require
def block_dnsname(dnsname, timeout=30):
    """
    Redirect dnsname to localhost

        Arguments:
            dnsname - list of DNS names that will be redirected to localhost
            timeout - how long changes will take affect (Default: 30 sec)
    """
    dnsname = parse_args_list(dnsname)
    timeout = convert_timeout(timeout, def_timeout=30)
    return _run_thread(_block_dnsname, args=(dnsname, timeout),
                       ret_msg='Redirect dnsname to localhost is started')


def _block_dnsname(dnsname, timeout):
    """
    Redirect dnsname to localhost

        Arguments:
            dnsname - list of DNS names that will be redirected to localhost
            timeout - how long changes will take affect
    """
    args = ['etc', 'hosts']
    if IS_WINDOWS:
        args = [sys_path(), 'drivers'] + args
    else:
        args.insert(0, sep)
    #pylint: disable=W0142
    host_path = path.join(*args)
    with open(host_path, 'a+') as open_file:
        hosts_value = open_file.read()
        open_file.seek(0, 2)
        open_file.writelines(['\n127.0.0.1    ' + each for each in dnsname])
    sleep(timeout)
    #return previous values
    with open(host_path, 'w') as open_file:
        open_file.write(hosts_value)
