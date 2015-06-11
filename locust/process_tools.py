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


"""Process tools commands."""
from socket import gethostbyname, gethostname, gaierror
from uuid import getnode
from time import time, sleep
from operator import itemgetter
from os import getpid
from fnmatch import fnmatch

import psutil

from locust.common import parse_pids, parse_args_list, message_wrapper


def get_process(pids=None, names=None):
    """
    Return a list of specified local processes.

    Arguments:
        pids - list of process PIDs to get;
        names - list of process names to get.

    Return: a list of process dicts.
    """
    if not pids and not names:
        processes = [process for process in psutil.process_iter()]
    else:
        pids = parse_pids(pids)
        names = parse_args_list(names)
        processes = [psutil.Process(pid) for pid in pids if
                     psutil.pid_exists(pid)]
        if names and not pids:
            # Do not add current python process to result list.
            cur_pid = getpid()
            local_processes = [proc for proc in psutil.process_iter() if
                               proc.pid != cur_pid]
            for name in names:
                for process in local_processes:
                    try:
                        if fnmatch(process.name(), name) or fnmatch(
                                ' '.join(process.cmdline()), name):
                            processes.append(process)
                    except psutil.AccessDenied:
                        pass
    result = []
    for process in processes:
        try:
            try:
                hostname = gethostbyname(gethostname())
            except gaierror:
                hostname = gethostbyname('localhost')
            temp = {
                'pid': process.pid,
                'name': process.name(),
                'status': str(process.status()),
                'cmd': ' '.join(process.cmdline()),
                'node': str(getnode()),
                'endpoint': hostname
            }
            if pids or names:
                temp['cpu'] = process.cpu_percent() / psutil.cpu_count()
                temp['ram'] = long(process.memory_info()[0]) / 1024
            if temp not in result:
                result.append(temp)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print 'NoSuchProcess or AccessDenied exception occurred'
    return result


def list_process():
    """
    Return a list of all local processes.

    Arguments: None.

    Return: a list of process dicts.
    """
    return get_process()


def kill_process(names=None, pids=None):
    """
    Kill local processes by names and PIDS.

        Arguments:
            names - list of processes names to kill;
            pids - list of process PIDs to kill;

    Return:
        [{process1_dict}, {process2_dict}, ..., {processN_dict}]
    """
    if not names and not pids:
        return message_wrapper('Please, provide processes PIDs or names.',
                               status='error')
    pids = parse_pids(pids)
    names = parse_args_list(names)
    processes = _list_presented_processes(names, pids)
    return _kill_process_list(processes)


def _kill_process_list(processes):
    """
    Kill local processes by list of processes.

        Arguments:
            processes - list of dictionaries to kill.
                        The dictionaries should contain name, pid,
                        status of process.

    Return: [{process1_dict}, {process2_dict}, ..., {processN_dict}]
    """
    for process in processes:
        if process['status'] == 'present':
            try:
                _kill_process_by_pid(process['pid'])
                end_time = time() + 60
                while True:
                    try:
                        psutil.Process(process['pid'])
                    except psutil.NoSuchProcess:
                        process['status'] = 'killed'
                        break
                    sleep(3)
                    if time() > end_time:
                        process['status'] = 'not_killed'
                        break
            except psutil.NoSuchProcess:
                process['status'] = 'killed_by_another_process'
    return processes


def _kill_process_by_pid(pid):
    """
    Kill local process by pid

        Arguments:
            pid - PID of process to kill
    """
    process = psutil.Process(pid)
    process.kill()


def _list_presented_processes(names, pids):
    """
    Create list of dictionaries with processes names, PIDs and statuses.

        Arguments:
            names - list of proc names to check availability in the local node;
            pids - list of proc PIDs to check availability in the local node;

    Return: [{process1_dict}, {process2_dict}, ..., {processN_dict}]
    """
    cur_pid = getpid()
    local_processes = [process for process in psutil.process_iter() if
                       process.pid != cur_pid]
    process_to_kill = []

    for name in set(names):
        name_flag = True
        for process in local_processes:
            if fnmatch(process.name(), name) or fnmatch(
                    ' '.join(process.cmdline()), name):
                pids.append(process.pid)
                name_flag = False
        if name_flag:
            process_to_kill.append(
                {'pid': None, 'name': name, 'status': 'not_found'})

    for pid in set(pids):
        pid_flag = True
        for process in local_processes:
            if pid == process.pid:
                process_to_kill.append(
                    {'pid': process.pid, 'name': process.name(),
                     'status': 'present'})
                pid_flag = False
        if pid_flag:
            process_to_kill.append(
                {'pid': pid, 'name': None, 'status': 'not_found'})

    return sorted(process_to_kill, key=itemgetter('pid'))


def suspend_process(names=None, pids=None):
    """
    Suspend local processes by names and PIDS.

        Arguments:
            names - list of processes names to suspend;
            pids - list of process PIDs to suspend;

    Return: [{process1_dict}, {process2_dict}, ..., {processN_dict}]
    """
    if not names and not pids:
        return message_wrapper('Please, provide processes PIDs or names.',
                               status='error')
    pids = parse_pids(pids)
    names = parse_args_list(names)
    processes = _list_presented_processes(names, pids)
    return _suspend_process_list(processes)


def _suspend_process_list(processes):
    """
    Suspend local processes by list of processes.

        Arguments:
            processes - list of dictionaries to suspend.
                        The dictionaries should contain name, pid,
                        status of process.

    Return: [{process1_dict}, {process2_dict}, ..., {processN_dict}]
    """
    for process in processes:
        if psutil.Process(process['pid']).status() == 'stopped':
            process['status'] = 'was_stopped'

    for process in processes:
        if process['status'] == 'present':
            if psutil.Process(process['pid']).status() == 'stopped':
                process['status'] = 'stopped_by_another_process'
            else:
                try:
                    _suspend_process_by_pid(process['pid'])
                    end_time = time() + 60
                    while True:
                        if psutil.Process(
                                process['pid']).status() == 'stopped':
                            process['status'] = 'stopped'
                            break
                        sleep(3)
                        if time() > end_time:
                            process['status'] = 'not_stopped'
                            break
                except psutil.NoSuchProcess:
                    process['status'] = 'killed_by_another_process'
    return processes


def _suspend_process_by_pid(pid):
    """
    Suspend local process by pid

        Arguments:
            pid - PID of process to suspend
    """
    process = psutil.Process(pid)
    process.suspend()


def resume_process(names=None, pids=None):
    """
    Resume local processes by names and PIDS.

        Arguments:
            names - list of processes names to resume;
            pids - list of process PIDs to resume;

    Return: [{process1_dict}, {process2_dict}, ..., {processN_dict}]
    """
    if not names and not pids:
        return message_wrapper('Please, provide processes PIDs or names.',
                               status='error')
    pids = parse_pids(pids)
    names = parse_args_list(names)
    processes = _list_presented_processes(names, pids)
    return _resume_process_list(processes)


def _resume_process_list(processes):
    """
    Resume local processes by list of processes.

        Arguments:
            processes - list of dictionaries to resume.
                        The dictionaries should contain name, pid,
                        status of process.

    Return: [{process1_dict}, {process2_dict}, ..., {processN_dict}]
    """
    for process in processes:
        if psutil.Process(
                process['pid']).status() == 'running' or psutil.Process(
                process['pid']).status() == 'sleeping':
            process['status'] = 'was_resumed'

    for process in processes:
        if process['status'] == 'present':
            if psutil.Process(
                    process['pid']).status() == 'running' or psutil.Process(
                    process['pid']).status() == 'sleeping':
                process['status'] = 'resumed_by_another_process'
            else:
                try:
                    _resume_process_by_pid(process['pid'])
                    end_time = time() + 10
                    while True:
                        if psutil.Process(process[
                            'pid']).status() == 'running' or psutil.Process(
                                process['pid']).status() == 'sleeping':
                            process['status'] = 'resumed'
                            break
                        sleep(3)
                        if time() > end_time:
                            process['status'] = 'not_resumed'
                            break
                except psutil.NoSuchProcess:
                    process['status'] = 'killed_by_another_process'
    return processes


def _resume_process_by_pid(pid):
    """
    Resume local process by pid

        Arguments:
            pid - PID of process to resume.
    """
    process = psutil.Process(pid)
    process.resume()
