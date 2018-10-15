# -*- coding: utf-8 -*-
''' Hello from monyze/config_data.py '''

__author__ = 'Konstantin Lyakhov'
__contact__ = 'kl@rifco.ru'
__copyright__ = 'Copyright (C) Monyze. All rights reserved.'
__credits__ = ['Konstantin Lyakhov (Skype: komstin)', 'Dmitry Soloviev (Skype: gex_skype)']
__license__ = ''

import logging
import netifaces
import psutil
import json
import os
import re
import sys
import subprocess
from bs4 import BeautifulSoup

DEBUG = False
if len(sys.argv) > 1:
    if sys.argv[1] == '-dsdlkfskjdgfsdkjgsgdiu':
        DEBUG = True


class Config_data:
    ''' config data - get, update '''

    def __init__(self, config):
        self.logger = logging.getLogger("monyze.config_data")
        self.logger.info("Initializing config_data")
        self.computerId = config.computerId
        self.userId = config.userId
        self.cpu_model = config.cpu_model
        self.bits = config.bits
        self.nodename = config.nodename
        self.os = config.os
        self.icon = 'f17c'

    def get_sensors_temperatures(self):
        dev_temp_list = list()
        if not hasattr(psutil, "sensors_temperatures"):
            print("platform not supported sensors_temperatures")
        temps = psutil.sensors_temperatures()
        if not temps:
            print("no temps detected")
            return None
        for name, entries in temps.items():
            dev_temp_list.append(name)
            #print(name)
            for entry in entries:
                pass
                #print("     %-20s %s C" % (entry.label or name, entry.current))
        #print(temps)
        return dev_temp_list

    def get_sensors_fans(self):
        if not hasattr(psutil, "sensors_fans"):
            print("platform not supported sensors_fans")
        self.fans = psutil.sensors_fans()
        if not self.fans:
            print("no fans detected")
            return
        for name, entries in self.fans.items():
            print(name)
            for entry in entries:
                print("    %-20s %s RPM" % (entry.label or name, entry.current))
        print(self.fans)
        return self.fans

    def get_network(self):
        self.network_devices = {}
        device = {}
        netpos = 0
        model = "Unknown"
        speed = "Unknown"
        lshw_xml = subprocess.getoutput('lshw -class network -xml')

        # Parse the XML.
        output = BeautifulSoup(lshw_xml, "xml")
        list_of_devices = output.list.children

        for i, node in enumerate(list_of_devices):
            try:
                devpos = i + 1
                speed_nodes = node.find_all('setting', attrs={"id": "speed"})
                device['Interface'] = node.logicalname.contents[0]
                device['Vendor'] = node.vendor.contents[0]
                if speed_nodes:
                    device['Speed'] = speed_nodes[0]['value']
                device['Prodact'] = node.product.contents[0]
                self.network_devices['dev_' + str(devpos)] = device
            except AttributeError:
                pass

        self.network = {}
        #print(netifaces.interfaces())
        for i, interface in enumerate(netifaces.interfaces()):
            if not re.match(r'lo', interface):
                #print(interface)
                try:
                    netpos = netpos + 1
                    #print(netpos)
                    net = netifaces.ifaddresses(interface)[netifaces.AF_INET]
                    #print(net)

                    for device in self.network_devices.values():
                        #print(device)
                        if interface == device['Interface']:
                            model = device['Vendor'] + ' ' + device['Prodact']
                            speed = device['Speed']
                        else:
                            model = "Unknown"
                            speed = "Unknown"
                    self.network['net_' + str(netpos)] = {'name': interface,
                                                          'model': model,
                                                          'speed': speed,
                                                          'addr': net[0]['addr'],
                                                          'netmask': net[0]['netmask']}
                    #print(self.network)
                except KeyError:
                    continue
        return self.network

    def get_hdd(self):
        self.hdd = {}
        list = []
        self.partitions = psutil.disk_partitions()

        for i, partition in enumerate(self.partitions):
            if re.match(r'/dev/sd', partition.device):
                hddpos = i + 1
                usage = psutil.disk_usage(partition.mountpoint)
                dict = {}
                dict['hdd_' + str(hddpos)] = {"Name": partition.device,
                                                  "Size": usage.total,
                                                  "LOGICAL": partition.mountpoint,
                                                  "LOAD": usage.percent}
                #print(dict)
                list.append(dict)
        self.hdd['hdd'] = list
        #print(self.hdd)
        return self.hdd

    def update(self):
        # FANS
        self.fans = self.get_sensors_fans()

        # TEMP
        self.temps = self.get_sensors_temperatures()

        # RAM
        self.swap = psutil.swap_memory()
        self.memory = psutil.virtual_memory()
        self.TotalPh = self.memory.total
        self.TotalPF = self.swap.total

        # NET
        self.network = self.get_network()

        # HDD
        self.hdd = self.get_hdd()

        # RESULT CONFIG
        self.config_data = {
            'id': {'device_id': self.computerId, 'user_id': self.userId},
            'state': "config",
            'device_config': {'device_name': self.nodename,
                              'system': self.os,
                              'icon': self.icon,
                              #'cpu': self.cpu_model,
                              'cpu': {"cpu_1": self.cpu_model},
                              'ram': {
                                  'TotalPh': self.TotalPh,
                                  'TotalPF': self.TotalPF,
                                  'bits': self.bits
                              },
                              'net': self.network,
                              'hdd': self.hdd,
                              'temp': self.temps,
                              'fan': self.fans
                              }
        }
        self.logger.info("config_data was initialized")
        #print(json.dumps(self.config_data, sort_keys=True, indent=4))
        return self.config_data
