#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' Hello from monyze-agent.py '''
__author__ = 'Konstantin Lyakhov'
__contact__ = 'kl@rifco.ru'
__copyright__ = 'Copyright (C) Monyze. All rights reserved.'
__credits__ = ['Konstantin Lyakhov (Skype: komstin)', 'Dmitry Soloviev (Skype: gex_skype)']
__license__ = ''

import logging
import logging.config
import sys
import os
from os.path import basename
import argparse
import shutil
import subprocess
from gevent import joinall
from pssh.clients import ParallelSSHClient
from bs4 import BeautifulSoup
from monyze.config import Config
from monyze.data import Data
from monyze.daemon import Daemon
import requests
import platform

DEBUG = False
if len(sys.argv) > 1:
    if sys.argv[1] == '-dsdlkfskjdgfsdkjgsgdiu':
        DEBUG = True

updating = 0
compilation = 0  # Always zero for prod
deployment_local = 0
deployment_remote = 0
daemon_running = 0

if DEBUG:
    compilation = 1
    compile_remote_upload = 0
    updating = 0
    deployment_local = 1
    deployment_remote = 0
    daemon_running = 0
else:
    updating = 0
    deployment_local = 1
    deployment_remote = 0

init = '''#! /bin/sh

### BEGIN INIT INFO
# Provides:          monyze-service
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Should-Start:      $portmap
# Should-Stop:       $portmap
# X-Start-Before:    nis
# X-Stop-After:      nis
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# X-Interactive:     true
# Short-Description: Monyze-agent
# Description:       Monyze monitoring service
### END INIT INFO

case "$1" in
  start)
    echo "Starting monyze-agent"
    /usr/local/bin/monyze-agent start
    ;;
  stop)
    echo "Stopping monyze-agent"
    /usr/local/bin/monyze-agent stop
    ;;
  stop)
    echo "Stopping monyze-agent"
    /usr/local/bin/monyze-agent restart
    ;;
  *)
    echo "Usage: /etc/init.d/monyze-agent {start|stop|restart}"
    exit 1
    ;;
esac

exit 0
    '''


def parse_xml_credentials():
    credentials_dict = {}
    with open('keys.xml', 'r') as f:
        soup = BeautifulSoup(f, "xml")
        list_of_hosts = soup.find_all('item')
        for i, item in enumerate(list_of_hosts):
            temp_dict = {}
            pos = i + 1
            temp_dict['host'] = item.host.contents[0]
            temp_dict['user'] = item.user.contents[0]
            temp_dict['password'] = item.password.contents[0]
            temp_dict['port'] = item.port.contents[0]
            temp_dict['path_to_private_key'] = item.path_to_private_key.contents[0]
            credentials_dict['item_' + str(pos)] = temp_dict
        # print(credentials_dict)
    return (credentials_dict)


def get_glibc_version():
    pipe = os.popen("bash -c 'getconf GNU_LIBC_VERSION'")
    pipe_str = str(pipe.read())
    glibc = float(pipe_str.split()[1])
    return glibc


def compile():
    subprocess.call(['./clean.sh'])
    subprocess.call(
        [os.path.expanduser('~/.pyenv/versions/3.7.0/bin/pyinstaller'), sys.argv[0], '--additional-hooks-dir=.',
         '-F'])

    if (compile_remote_upload):

        glibc = get_glibc_version()
        if glibc < 2.25:
            dist_filename_bin = '/var/www/dev.monyze.ru/files/linux/upto_2_25/monyze-agent'
        else:
            dist_filename_bin = '/var/www/dev.monyze.ru/files/linux/monyze-agent'

        credentials_dict = parse_xml_credentials()
        for credentials in credentials_dict.values():
            if credentials['host'] == 'dev.monyze.ru':
                hosts = list()
                hosts.append(credentials['host'])
                client = ParallelSSHClient(hosts, user=credentials['user'], port=int(credentials['port']),
                                           pkey=credentials['path_to_private_key'])
                print('Copying monyze-agent to dev.monyze.ru...')
                sys.stdout.flush()
                path_to_monyze_agent = 'dist/monyze-agent'
                filename_bin = 'monyze-agent'
                os.system("scp -i " + credentials['path_to_private_key'] + " -P " + credentials[
                    'port'] + " " + path_to_monyze_agent + " " + credentials['user'] + "@" + credentials[
                              'host'] + ":" + str(
                    basename(path_to_monyze_agent)))
                remote_sudo_cmd_run(client, credentials['password'],
                                    'mv' + ' ' + filename_bin + ' ' + dist_filename_bin)
                remote_sudo_cmd_run(client, credentials['password'], 'chmod 755' + ' ' + dist_filename_bin)


def remote_cmd_run(client, cmd):
    output = client.run_command(cmd)
    host_output = output[client.hosts[0]]
    for line in host_output.stdout:
        print(line)


def remote_sudo_cmd_run(client, password, cmd):
    output = client.run_command(cmd, sudo=True)
    host_output = output[client.hosts[0]]
    host_output.stdin.write(password + '\n')
    host_output.stdin.flush()
    for line in host_output.stdout:
        print(line)


def deploy_remote_all():
    try:
        credentials_dict = parse_xml_credentials()
        for credentials in credentials_dict.values():
            deploy_remote(credentials['host'], credentials['user'], credentials['password'], credentials['port'],
                          credentials['path_to_private_key'])
    except Exception as error:
        print('No keys.xml file! Can not deploy remote!')
        # print('Caught this error: ' + repr(error))


def deploy_remote(host, user, password, port, path_to_private_key):
    path_to_monyze_agent = sys.argv[0]
    if DEBUG:
        path_to_monyze_agent = 'dist/monyze-agent'
    filename_bin = str(basename(path_to_monyze_agent))
    filename_sh = '/etc/init.d/monyze-agent'
    dist_filename_bin = '/usr/local/bin/' + filename_bin
    hosts = list()
    hosts.append(host)

    try:
        # client = ParallelSSHClient(hosts, user=user, password=password, port=int(port), pkey=path_to_private_key)
        client = ParallelSSHClient(hosts, user=user, port=int(port), pkey=path_to_private_key)

        print('Copying monyze-agent to remote hosts...')
        sys.stdout.flush()

        # deploy ELF monyze-agent
        os.system(
            "scp -i " + path_to_private_key + " -P " + port + " " + path_to_monyze_agent + " " + user + "@" + host + ":" + str(
                basename(path_to_monyze_agent)))
        remote_sudo_cmd_run(client, password, 'mv' + ' ' + filename_bin + ' ' + dist_filename_bin)
        remote_sudo_cmd_run(client, password, 'chmod 755' + ' ' + dist_filename_bin)

        # deploy shell monyze-agent
        greenlets = client.copy_file(filename_sh, str(basename(filename_sh)))
        joinall(greenlets, raise_error=True)
        remote_sudo_cmd_run(client, password, 'mv ' + str(basename(filename_sh)) + ' ' + filename_sh)
        remote_sudo_cmd_run(client, password, 'chmod 755' + ' ' + filename_sh)
        remote_sudo_cmd_run(client, password, 'update-rc.d monyze-agent defaults')
        remote_sudo_cmd_run(client, password, 'service monyze-agent restart')
    except Exception as error:
        print('Can not deploy on host: %s' % host)
        print('Caught this error: ' + repr(error))


def update():
    try:
        glibc = get_glibc_version()
        if glibc < 2.25:
            r = requests.get("http://dev.monyze.ru/files/linux/upto_2_25/monyze-agent", stream=True)
        else:
            r = requests.get("http://dev.monyze.ru/files/linux/monyze-agent", stream=True)

        if r.status_code == 200:
            if os.path.exists('monyze-agent'):
                os.remove('monyze-agent')
            with open('monyze-agent', 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            f.close()
            path_to_monyze_agent = os.path.abspath('monyze-agent')
            deploy_local(path_to_monyze_agent)
    except Exception as error:
        print('Can not update!')
        print('Caught this error: ' + repr(error))


def deploy_local(path_to_monyze_agent):
    try:
        if DEBUG:
            path_to_monyze_agent = 'dist/monyze-agent'
        # path_to_monyze_agent = sys.argv[0]
        dist_to_monyze_agent = '/usr/local/bin/' + str(basename(path_to_monyze_agent))
        subprocess.call(['chown', os.environ['SUDO_USER'] + ':' + os.environ['SUDO_USER'], path_to_monyze_agent])
        subprocess.call(['chmod', '+x', path_to_monyze_agent])
        # print(path_to_monyze_agent)
        # print(dist_to_monyze_agent)
        if os.path.exists(dist_to_monyze_agent):
            # pass
            # print('dist_to_monyze_agent exist!')
            os.remove(dist_to_monyze_agent)
        shutil.copy(path_to_monyze_agent, dist_to_monyze_agent)
    except Exception as error:
        print('Can not copy agent file!')
        print('Caught this error: ' + repr(error))
        return

    with open('/etc/init.d/monyze-agent', 'w') as agent:
        agent.write(init)
    os.chmod('/etc/init.d/monyze-agent', 755)
    subprocess.call(['update-rc.d', 'monyze-agent', 'defaults'])  # defaults means 2 3 4 5 runlevel
    subprocess.call(['service', 'monyze-agent', 'restart'])
    print('The service is started. You can check by the command: sudo service monyze-agent status')


def data_init(config):
    data = Data(config)
    return data


def config_init():
    config = Config('/etc/monyze-agent/config.pkl')
    return config


def daemon_init():
    daemon = Daemon('/var/run/monyze-agent.pid')
    return daemon


def daemon_start(daemon, config, logger, data):
    print(daemon.get_pid())
    if not daemon.get_pid() or DEBUG:
        logger.info("Running the daemon")
        print('Running the daemon')
        daemon.start(config, data)
    else:
        print('The daemon is already running')
        logger.info("The daemon is already running. Exit")


def daemon_stop(daemon, logger):
    if not daemon.get_pid():
        logger.info("The daemon is not running, there's nothing to stop. Exit")
    else:
        logger.info("Stopping the daemon")
        daemon.stop()


def daemon_restart(daemon, logger, config, data):
    if not daemon.get_pid():
        logger.info("The daemon is not running, restart is not possible. Exit")
    else:
        logger.info("Restarting the daemon")
        daemon.restart(config, data)


def daemon_run():
    logger = logging_init()
    daemon = daemon_init()
    config = config_init()
    data = data_init(config)

    if (sys.argv[1] == 'start') or (len(sys.argv) < 2) or (sys.argv[1] == '-dsdlkfskjdgfsdkjgsgdiu'):
        daemon_start(daemon, config, logger, data)

    if sys.argv[1] == 'stop':
        daemon_stop(daemon, logger)

    if sys.argv[1] == 'restart':
        daemon_restart(daemon, logger, config, data)

    print('Invalid argument!')
    logger.info('Stopping')


def logging_init():
    logConfig = {
        "version": 1,
        "handlers": {
            "fileHandler": {
                "class": "logging.FileHandler",
                "formatter": "myFormatter",
                "filename": "/var/log/monyze-agent.log"
            }
        },
        "loggers": {
            "monyze": {
                "handlers": ["fileHandler"],
                "level": "INFO"
            }
        },
        "formatters": {
            "myFormatter": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    }
    logging.config.dictConfig(logConfig)
    logger = logging.getLogger("monyze.main")
    logger.info("\n*** Starting: %s" % sys.argv[1])
    return logger


def main():
    ''' The main entry point of the Monyze monitoring agent '''

    # print(sys.version)
    # subprocess.call(['which', 'pyinstaller'])
    # subprocess.call(['ls', '-l'])

    if sys.argv[0] == '/usr/local/bin/monyze-agent' or daemon_running:
        daemon_run()
        return

    parser = argparse.ArgumentParser(prog='monyze', add_help=False,
                                     description='Without arguments - the service starts (sudo)',
                                     epilog='More info - on the site https://monyze.ru')
    parser.add_argument("-h", "--help", action='store_true', help="Show hint")
    parser.add_argument("-v", "--version", action='store_true', help="Show version")
    parser.add_argument("-t", "--timeout", help="Set monitoring time interval in seconds (sudo)", type=int)
    parser.add_argument("-u", "--userId", help="Set userId (sudo)")
    parser.add_argument("-U", "--update", action='store_true', help="Updating monyze-agent")
    parser.add_argument("-c", "--config", action='store_true', help="Show configuration")
    parser.add_argument("-C", "--computerId", help="Set computerId (sudo)")
    if DEBUG:
        parser.add_argument("-dsdlkfskjdgfsdkjgsgdiu", "--debug", action='store_true',
                            help="Debug mode. It should not be in prod")
    try:
        args = parser.parse_args()
    except BaseException:
        print('Invalid argument!')
        return

    if args.help:
        parser.print_help()
        return

    config = config_init()

    if args.version:
        print('Agent Version: %s' % config.version)
        return

    if args.config:
        print(config)
        return

    if os.getuid():
        print('Administrator rights are required! Try using the command sudo.')
        return

    if args.timeout:
        config.timeout = args.timeout
        config.store()
        print('New timeout: %s sec. was set.' % args.timeout)
        return

    if args.userId:
        config.userId = args.userId
        config.store()
        print('Новый userId: %s was set.' % args.userId)
        return

    if args.computerId:
        config.computerId = args.computerId
        config.store()
        print('New computerId: %s was set.' % args.computerId)
        return

    if args.update:
        print('Starting update...')
        update()
        return

    if compilation:
        compile()

    if deployment_local:
        deploy_local(sys.argv[0])

    if updating:
        update()

    if deployment_remote:
        deploy_remote_all()


if __name__ == '__main__':
    main()
