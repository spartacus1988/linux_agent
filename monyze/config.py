# -*- coding: utf-8 -*-
''' Hello from monyze/config.py '''

__author__ = 'Konstantin Lyakhov'
__contact__ = 'kl@rifco.ru'
__copyright__ = 'Copyright (C) Monyze. All rights reserved.'
__credits__ = [
    'Konstantin Lyakhov (Skype: komstin)', 'Dmitry Soloviev (Skype: gex_skype)']
__license__ = ''

import logging
import datetime
import pickle
import platform
import os
import sys
import socket
import cpuinfo

DEBUG = False
if len(sys.argv) > 1:
    if sys.argv[1] == '-dsdlkfskjdgfsdkjgsgdiu':
        DEBUG = True

logger = logging.getLogger("monyze.config")


class Config:
    ''' Configuration - update, store, restore '''

    def __init__(self, filename):
        logger.info("Initializing the config")
        self.filename = filename
        try:
            self.restore()
        except (IOError, EOFError):
            self.update()

    def get_computerId(self):
        try:
            f = open('keys.key', 'r')
            computerId = f.readline().rstrip('\n')
            f.close()
        except (IOError, ValueError):
            print('Missing key file')
            print('Input id_computer, which was received on the site monyze.ru:')
            computerId = input()
            print('You entered id_computer = ' + computerId)
        return computerId

    def get_userId(self):
        try:
            f = open('keys.key', 'r')
            f.readline()
            userId = f.readline().rstrip('\n')
            f.close()
        except (IOError, ValueError):
            print('Missing key file')
            print('Input userId, which was received on the site monyze.ru:')
            userId = input()
            print('You entered userId = ' + userId)
        return userId

    def get_nodename(self):
        try:
            host = socket.gethostname()
            if host:
                return host
        except (ValueError, RuntimeError):
            pass

        try:
            host = platform.node()
            if host:
                return host
        except (ValueError, RuntimeError):
            pass

        try:
            host = os.uname()[1]
            if host:
                return host
        except (ValueError, RuntimeError):
            pass

        raise Exception('Can not determine hostname of this system')

    def get_os(self):
        return platform.platform()

    def get_cpu_data(self):
        cpu_data = cpuinfo.get_cpu_info()
        return cpu_data['brand']

    def store(self):
        if os.getuid():
            raise SystemExit(
                '\nAdministrator rights are required! Try using the command sudo.\n')
        if not os.path.isdir('/etc/monyze-agent'):
            os.mkdir('/etc/monyze-agent', 755)
        with open(self.filename, 'wb') as f:
            self.stored_at = datetime.datetime.now()
            print(self.__dict__)
            pickle.dump(self, f, 2)
        logger.info("Configuration was stored")

    def restore(self):
        with open(self.filename, 'rb') as f:
            store = pickle.load(f)
            for key, value in store.__dict__.items():
                self.__dict__[key] = value
            self.restored_at = datetime.datetime.now()
        logger.info("Config was restored")

    def update(self):
        if os.getuid():
            print('Administrator rights are required! Try using the command sudo.')
            raise SystemExit('Administrator rights are required! Try using the command sudo.')
        self.name = 'monyze-agent'
        self.description = 'Monyze monitoring agent'
        self.computerId = self.get_computerId()
        self.userId = self.get_userId()
        self.nodename = self.get_nodename()
        self.bits = platform.architecture()[0]
        self.cpu_model = self.get_cpu_data()
        self.os = self.get_os()
        self.timeout = 1
        self.url = 'http://monyze.ru/'
        if DEBUG:
            self.api_url = 'http://dev.monyze.ru/api.php'
        else:
            self.api_url = 'http://dev.monyze.ru/api.php'
        self.version = '0.0.7'
        self.osSystem = platform.system()
        self.osRelease = platform.release()
        self.osVersion = platform.version()
        self.machine = platform.machine()
        self.store()
        logger.info("Configuration created")

    def __str__(self):
        stored_values = self.__dict__
        lines = []
        width = max(len(key) for key in stored_values)
        for key in sorted(stored_values.keys()):
            value = stored_values[key]
            if isinstance(value, datetime.datetime):
                value = value.isoformat()
            lines.append('{0} : {1!r}'.format(key.ljust(width), value))
        #        return '\n' + '\n'.join(lines) + '\n'
        return '\n'.join(lines)

    def __repr__(self):
        return '{0}({1!r})'.format(self.__class__.__name__, self.filename)
