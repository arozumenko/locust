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


"""Resource tools commands."""
from threading import Thread, current_thread, active_count
from time import time, sleep
from random import randrange
from math import sqrt
from multiprocessing import Process, cpu_count, current_process
from os import urandom, remove
from glob import glob
from tempfile import gettempdir
from os.path import join as join_path

from psutil import swap_memory

from locust.common import IS_WINDOWS
from locust.common import message_wrapper, convert_timeout


def burn_cpu(timeout=30):
    """Burn CPU command.
    Start processes with random int.

    Arguments:
    :timeout - length of time in seconds to burn cpu (Default: 30 sec)

    Return:
        feedback
    """
    timeout = convert_timeout(timeout, def_timeout=30)
    for _ in range(cpu_count()):
        thread = Process(target=_burn_cpu, args=[timeout])
        thread.start()
    return message_wrapper('CPU burning started')


def _burn_cpu(timeout=0):
    """Burn CPU command."""
    end_time = time() + timeout
    while time() < end_time:
        sqrt(float(randrange(1, 999999, 1)))


def burn_ram(timeout=30):
    """RAM overflow command.
    Fill Ram with garbage data

    Arguments:
    :timeout - length of time in seconds to burn cpu (Default: 30 sec)

    Return:
        feedback
    """
    timeout = convert_timeout(timeout, def_timeout=30)
    process = Process(target=_burn_ram, args=[timeout])
    process.start()
    return message_wrapper('RAM overflowing has been started')


def _burn_ram(timeout):
    """RAM overflow command."""

    f_ratio = 100
    d_ratio = f_ratio
    fill_ram = ''
    decrease = ''
    spike = ''

    # Start RAM overflow
    # Try to fill all free RAM space
    while True:
        try:
            fill_ram = ' ' * int((float(swap_memory().free) / 100) * f_ratio)
            break
        except (MemoryError, OverflowError):
            f_ratio -= 1

    # Try to fill all left free RAM space (Windows OS specific)
    while True:
        try:
            decrease = ' ' * int((float(swap_memory().free) / 100) * d_ratio)
            break
        except (MemoryError, OverflowError):
            d_ratio -= 1

    end_time = time() + timeout
    while time() < end_time:
        if float(swap_memory().percent) < 90:
            try:
                spike += ' ' * int((float(swap_memory().free) / 100) * 10)
            except (MemoryError, OverflowError):
                spike = ''

    del fill_ram
    del decrease
    del spike


def burn_disk(timeout=30, file_size='1k', thread_limit='200'):
    """Burn HDD command.

    Arguments:
        timeout - length of time in seconds to burn HDD (Default: 30 sec);
        file_size - file size to be created in thread;
        thread_limit - thread limit count per process;
    Return:
        Returns message that burn HDD is started.
    """
    timeout = convert_timeout(timeout, def_timeout=30)
    values = {
        'B': 0,
        'K': 10,
        'M': 20,
    }

    if file_size.isdigit():
        count = file_size
        rate = 'B'
    else:
        rate = file_size[-1:].upper()
        count = file_size[:-1]

    if not (rate in values and count.isdigit()):
        mgs = ('Wrong format of file_size param "{param}". "file_size" '
               'Parameter should have the following format:'
               '"<size_in_digit><Multiplifier>". Correct values for '
               'multiplifier is - {mult}')
        keys = values.keys() + [k.lower() for k in values.keys()]
        raise TypeError(mgs.format(param=file_size, mult=' '.join(keys)))

    if not thread_limit.isdigit():
        raise TypeError('Thread limit parameter should have the following '
                        'format:"<count_in_digit>"')

    file_size = int(int(count) << values[rate])
    end_time = time() + timeout
    for _ in xrange(cpu_count()):
        process = Process(target=_burn_disk,
                          args=[end_time, file_size, int(thread_limit)])
        process.start()
    return message_wrapper('HDD burning has been started')


def _burn_disk(end_time, file_size, thread_limit):
    """Burn HDD command."""

    def _start_write():
        """Write data to temp file."""
        while time() < end_time:
            file_name = current_process().name + '_' + current_thread().name
            file_name = join_path(gettempdir(), file_name)
            try:
                open_file = open(file_name, 'w')
                open_file.write(str(urandom(file_size)))
            except IOError:
                pass
            finally:
                open_file.close()

    if IS_WINDOWS:
        overall_file_limit = 16000
    else:
        import resource
        overall_file_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]

    thread_count = overall_file_limit / cpu_count()
    if thread_count > thread_limit:
        thread_count = thread_limit

    was_threads = active_count()
    for _ in xrange(thread_count):
        thread = Thread(target=_start_write)
        thread.start()

    while active_count() > was_threads:
        sleep(1)

    for each in glob(join_path(gettempdir(), current_process().name + '*')):
        remove(each)
