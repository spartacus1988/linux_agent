# -*- coding: utf-8 -*-
''' Hello from monyze/daemon.py '''

__author__ = 'Konstantin Lyakhov'
__contact__ = 'kl@rifco.ru'
__copyright__ = 'Copyright (C) Monyze. All rights reserved.'
__credits__ = ['Konstantin Lyakhov (Skype: komstin)', 'Dmitry Soloviev (Skype: gex_skype)']
__license__ = ''

import logging
import os
import sys
import time
import atexit
import signal
import requests
import json
from monyze.config_data import Config_data
from signal import signal as sig
from signal import SIGTERM as SGT

DEBUG = False
if len(sys.argv) > 1:
    if sys.argv[1] == '-dsdlkfskjdgfsdkjgsgdiu':
        DEBUG = True


class Daemon:
    ''' Agent daemonizing '''

    def __init__(self, pidfile, stdin='/dev/null',
                 stdout='/dev/null', stderr='/dev/null'):
        self.logger = logging.getLogger("monyze.daemon")
        self.logger.info("Initializing the daemon")

        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

        self.pidfile = pidfile
        self.logger.info("The daemon is initialized")

    def daemonize(self):
        self.fork()
        os.chdir('/')  # смена pwd, чтобы не блокировать текущий
        os.setsid()  # новый сеанс
        os.umask(0)  # права доступа создаваемым файлам
        self.fork()

        sys.stdout.flush()
        sys.stderr.flush()
        self.attach_stream('stdin', mode='r')

        self.attach_stream('stderr', mode='a+')  # в релизе раскомментировать
        self.create_pidfile()

    def attach_stream(self, name, mode):
        temp = getattr(self, name)
        stream = open(temp, mode)
        os.dup2(stream.fileno(), getattr(sys, name).fileno())

    def fork(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Демон запущен
        except OSError as e:
            sys.stderr.write("\nUnable to start: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

    def create_pidfile(self):
        atexit.register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self, config, data):
        if not DEBUG:
            pid = self.get_pid()
            if pid:
                message = "pid-файл %s  already exist. Is the daemon already running?\n"
                sys.stderr.write(message % self.pidfile)
                sys.exit(1)
            print("daemonize start")
            self.daemonize()
            self.logger.info("daemonize done")
        self.send_config(config)
        self.run(config, data)

    def get_pid(self):
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except (IOError, TypeError):
            pid = None
        return pid

    def stop(self, silent=False):
        pid = self.get_pid()

        if not pid:
            if not silent:
                message = "There is no pid-file %s. Is the daemon not running?\n"
                sys.stderr.write(message % self.pidfile)
            return

        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                sys.stdout.write(str(err))
                sys.exit(1)
        self.logger.info("The daemon is stopped")

    def restart(self, config, data):
        self.stop(silent=True)
        self.start(config, data)

    def send_config(self, config):
        cl_cfg_data = Config_data(config)
        config_data_to_send = cl_cfg_data.update()
        url = config.api_url
        # print(url)
        # print(config_data_to_send)
        # print(json.dumps(config_data_to_send, sort_keys=True, indent=4))
        requests.post(url, json.dumps(config_data_to_send))
        # requests.post(url, json.dumps(config_data_to_send).decode('utf-8'))
        self.logger.info(json.dumps(config_data_to_send))

    def run(self, config, data):
        self.logger.info("Daemon started")
        while True:
            try:
                if DEBUG:
                    sys.stdout.flush()
                time.sleep(config.timeout)
            except KeyboardInterrupt as e:
                self.logger.exception("message")
                raise SystemExit('\nAgent is stopped!\n')

            try:
                # If the daemon is killed from the console, then the function atexit is not enough
                sig(SGT, lambda signum, stack_frame: exit(1))
                # self.logger.info("inside  run")

                cur_date = data.update()
                url = config.api_url
                # print(url)
                if DEBUG:
                    pass
                    # print(cur_date)
                    # print(json.dumps(cur_date, sort_keys=True, indent=4))
                requests.post(url, json.dumps(cur_date))
                self.logger.info(json.dumps(cur_date))
            except:
                pass
