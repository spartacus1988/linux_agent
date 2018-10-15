# -*- coding: utf-8 -*-
''' Hello from monyze/data.py '''

__author__ = 'Konstantin Lyakhov'
__contact__ = 'kl@rifco.ru'
__copyright__ = 'Copyright (C) Monyze. All rights reserved.'
__credits__ = ['Konstantin Lyakhov (Skype: komstin)', 'Dmitry Soloviev (Skype: gex_skype)']
__license__ = ''

from uptime import uptime
import logging
import psutil
import time
import sys
import json
import re
from os.path import basename

DEBUG = False
if len(sys.argv) > 1:
    if sys.argv[1] == '-dsdlkfskjdgfsdkjgsgdiu':
        DEBUG = True


class Data:
    ''' Monitoring data - get, update '''

    def __init__(self, config):
        logger = logging.getLogger("monyze.data")
        logger.info("Initializing data")
        self.computerId = config.computerId
        self.userId = config.userId



    def get_sensors_temperatures(self):
        temp_dict = {}
        if not hasattr(psutil, "sensors_temperatures"):
            print("platform not supported sensors_temperatures")
        temps = psutil.sensors_temperatures()
        if not temps:
            print("no temps detected")
            return None
        for name, entries in temps.items():
            print(name)
            for entry in entries:
                temp_dict[entry.label or name] = entry.current
                #print("     %-20s %s C" % (entry.label or name, entry.current))
        #print(temp_dict)
        return temp_dict

    def get_cpu_total_temp_widg(self):
        # total_cpu = psutil.cpu_percent()
        total_cpu = None
        self.cpu_total_temp_widg = total_cpu
        return self.cpu_total_temp_widg

    def get_cpu_total_load_widg(self, total_cpu):
        # print(total_cpu)
        self.cpu_total_load_widg = total_cpu
        return self.cpu_total_load_widg

    def get_cpu_load(self, total_cpu):
        cpu_count = 1
        load_arr = {}
        temp_arr = {}
        # cpu_load_widg_arr = []
        # cpu_temp_widg_arr = []
        cpu_load_data = {}
        self.cpu_load = {}

        # print('first call total_cpu ' + str(total_cpu))
        load_arr['total'] = total_cpu
        percents = psutil.cpu_percent(interval=0, percpu=True)

        for i, percent in enumerate(percents):
            load_arr['core_' + str(i + 1)] = round(percent)

        cpu_load_data['load'] = load_arr
        cpu_load_data['temp'] = temp_arr
        cpu_pos = 'cpu_' + str(cpu_count) + ''
        self.cpu_load[cpu_pos] = cpu_load_data

        return self.cpu_load

    def get_ram_load(self):
        memory = psutil.virtual_memory()
        self.ram_load = round(memory.percent)
        return self.ram_load

    def get_ram(self):
        memory = psutil.virtual_memory()
        self.ram = {"load": round(memory.percent), "AvailPh": memory.available}
        return self.ram

    def get_hdd_info(self):
        self.hdd = {}
        self.hdd_widgets = {}
        prev_hdd = {}
        partitions = psutil.disk_partitions()
        ldisks = []
        ldisks_widgets = []
        hddpos = 0
        INTERVAL = 1  # 1 second

        iostats = psutil.disk_io_counters(perdisk=True)
        for i, partition in enumerate(partitions):
            if re.match(r'/dev/sd', partition.device):
                hddpos = hddpos + 1
                hdd_count = 'hdd_' + str(hddpos)
                ld = partition[0]
                prev_hdd[partition.device] = {
                    "read_rate": 0,
                    "write_rate": 0,
                    "load": 0,
                    "free": 0,
                    "used": 0,
                    "read_count": 0,
                    "write_count": 0,
                    "read_time": 0,
                    "write_time": 0,
                    "busy_time": 0,
                    "read_bytes": iostats[basename(ld)].read_bytes,
                    'write_bytes': iostats[basename(ld)].write_bytes
                }


        #print(prev_hdd)
        # print(json.dumps(prev_hdd, sort_keys=True, indent=4))

        if DEBUG:
            sys.stdout.flush()
        # for i in range(INTERVAL):
        #     print(i)
        #     print(INTERVAL)
        #     iostats = psutil.disk_io_counters(perdisk=True)
        #     #print(iostats[)
        #     time.sleep(1)

        time.sleep(INTERVAL)
        # print(INTERVAL)
        # print(prev_hdd)
        #hdd_pos = 1
        hddpos = 0

        iostats = psutil.disk_io_counters(perdisk=True)
        for i, partition in enumerate(partitions):
            if re.match(r'/dev/sd', partition.device):
                io = {}
                hddpos = hddpos + 1
                hdd_count = 'hdd_' + str(hddpos)
                ld = partition[0]
                usage = psutil.disk_usage(partition.mountpoint)
                perc = usage.percent


                # print(partition)
                # print(type(partition))
                # print(partition.device)
                free = round((int(usage.free) / 1024 / 1024 / 1024), 2)
                used = round((int(usage.used) / 1024 / 1024 / 1024), 2)
                l = {'ldisk': ld, 'load': round(perc), 'free': free, 'used': used}
                lw = {'ldisk': ld, 'load': round(perc)}
                ldisks.append(l)
                ldisks_widgets.append(lw)

                try:
                    # Calculate the Rate
                    prev_hdd[partition.device]["read_rate"] = (iostats[basename(ld)].read_bytes -
                                                               prev_hdd[partition.device][
                                                                   "read_bytes"]) / INTERVAL
                    # print(prev_hdd[partition.device]["read_rate"])
                    prev_hdd[partition.device]["write_rate"] = (iostats[basename(ld)].write_bytes -
                                                               prev_hdd[partition.device]["write_bytes"]) / INTERVAL
                    # print(prev_hdd[partition.device]["write_rate"])

                    #print(prev_hdd[partition.device]["read_rate"])
                    #print(prev_hdd[partition.device]["write_rate"])


                    rd = (prev_hdd[partition.device]["read_rate"])
                    wr = (prev_hdd[partition.device]["write_rate"])
                    # self.hdd[hdd_count] = {'rd': round(rd) / 1024 / 1024, 'wr': round(wr) / 1024 / 1024}
                    io = {'rd': round(rd), 'wr': round(wr)}
                    # print(prev_hdd[partition.device]["read_rate"])
                    # print(prev_hdd[partition.device]["write_rate"])
                    # print(self.hdd)
                    x = {'ldisks': ldisks, 'io': io}
                    self.hdd[hdd_count] = x
                    xw = {'ldisks': ldisks_widgets}
                    self.hdd_widgets[hdd_count] = xw
                except KeyError:
                    pass
        #print(self.hdd)
        #print(self.hdd_widgets)

        return self.hdd, self.hdd_widgets

    def get_network_interfaces(self):
        self.ifaces = []
        f = open("/proc/net/dev")
        data = f.read()
        f.close()
        data = data.split("\n")[2:]
        for i in data:
            if len(i.strip()) > 0:
                x = i.split()
                k = {
                    "interface": x[0][:len(x[0]) - 1],
                    "tx": {
                        "bytes": int(x[1]),
                        "packets": int(x[2]),
                        "errs": int(x[3]),
                        "drop": int(x[4]),
                        "fifo": int(x[5]),
                        "frame": int(x[6]),
                        "compressed": int(x[7]),
                        "multicast": int(x[8])
                    },
                    "rx": {
                        "bytes": int(x[9]),
                        "packets": int(x[10]),
                        "errs": int(x[11]),
                        "drop": int(x[12]),
                        "fifo": int(x[13]),
                        "frame": int(x[14]),
                        "compressed": int(x[15]),
                        "multicast": int(x[16])
                    }
                }
                self.ifaces.append(k)
        return self.ifaces

    def get_uptime(self):
        seconds = round(uptime())
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        # print(days, 'd', hours, 'h', minutes, 'm', seconds, 's')
        self.uptime = str(days) + 'd ' + str(hours) + 'h ' + str(minutes) + 'm ' + str(seconds) + 's'
        return self.uptime

    def get_network_info(self):
        self.net = {}
        prev_net = {}
        INTERVAL = 2  # 2 second

        idata = self.get_network_interfaces()
        # print(idata)
        # print(json.dumps(idata, sort_keys=True, indent=4))
        for eth in idata:
            if not re.match(r'lo', eth["interface"]):
                prev_net[eth["interface"]] = {
                    "rxrate": 0,
                    "txrate": 0,
                    "avgrx": 0,
                    "avgtx": 0,
                    "toptx": 0,
                    "toprx": 0,
                    "sendbytes": eth["tx"]["bytes"],
                    "recvbytes": eth["rx"]["bytes"]
                }
        # print(prev_net)
        # print(json.dumps(prev_net, sort_keys=True, indent=4))

        if DEBUG:
            sys.stdout.flush()
        # for i in range(INTERVAL):
        #     print(i)
        #     print(INTERVAL)
        #     idata = self.get_network_interfaces()
        #     #print(idata)
        #     time.sleep(1)

        time.sleep(INTERVAL)
        # print(INTERVAL)
        # print(prev_net)

        idata = self.get_network_interfaces()
        # print(idata)
        net_pos = 1
        for eth in idata:
            if not re.match(r'lo', eth["interface"]):
                try:
                    # Calculate the Rate
                    prev_net[eth["interface"]]["rxrate"] = (eth["rx"]["bytes"] - prev_net[eth["interface"]][
                        "recvbytes"]) / INTERVAL
                    # print(prev_net[eth["interface"]]["rxrate"])
                    prev_net[eth["interface"]]["txrate"] = (eth["tx"]["bytes"] - prev_net[eth["interface"]][
                        "sendbytes"]) / INTERVAL
                    # print(prev_net[eth["interface"]]["txrate"])

                    if (prev_net[eth["interface"]]["rxrate"] >= 0 or prev_net[eth["interface"]]["txrate"] >= 0):
                        tx = (prev_net[eth["interface"]]["txrate"])
                        rx = (prev_net[eth["interface"]]["rxrate"])
                        # self.net['net_' + str(net_pos)] = {'tx': round(tx) / 1024 / 1024, 'rx': round(rx) / 1024 / 1024}
                        self.net['net_' + str(net_pos)] = {'tx': round(tx), 'rx': round(rx)}
                        net_pos = net_pos + 1
                        # print(prev_net[eth["interface"]]["rxrate"])
                        # print(prev_net[eth["interface"]]["txrate"])
                        # print(self.net)
                except KeyError:
                    pass
        #print(self.net)
        return self.net

    def update(self):
        # TEMP
        self.temps = self.get_sensors_temperatures()

        # CPU
        total_cpu = round(psutil.cpu_percent())  # only 1 call per 0.1 sec
        self.cpu_load = self.get_cpu_load(total_cpu)
        self.cpu_total_load_widg = self.get_cpu_total_load_widg(total_cpu)
        self.cpu_total_temp_widg = self.get_cpu_total_temp_widg()

        # RAM
        self.ram = self.get_ram()
        self.ram_load = self.get_ram_load()

        # HDD
        self.hdd, self.hdd_widgets = self.get_hdd_info()

        # NET
        self.net = self.get_network_info()

        # UPTIME
        self.uptime = self.get_uptime()

        # RESULT DATA
        self.load_data = {
            'id': {'device_id': self.computerId, 'user_id': self.userId},
            "state": "load",
            "load": {
                "cpu": self.cpu_load,
                "ram": self.ram,
                "hdd": self.hdd,
                "net": self.net,
                "temps": self.temps
            },
            "widgets": {
                "cpu_load": self.cpu_total_load_widg,
                "cpu_temp": self.cpu_total_temp_widg,
                "ram_load": self.ram_load,
                "hdd_load": self.hdd_widgets,
                "uptime": self.uptime
            }
        }
        # print(json.dumps(self.load_data, sort_keys=True, indent=4))
        return self.load_data
