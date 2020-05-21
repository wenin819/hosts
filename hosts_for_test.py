#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__author__ = 'wenin819'
"""
from hosts import Hosts

def_hosts = {
    "test": "1.2.3.6"
}

if __name__ == '__main__':
    import os
    import argparse

    if os.name == 'nt':
        hosts_path = os.path.join(os.environ['SYSTEMROOT'], 'system32/drivers/etc/hosts')
    elif os.name == 'posix':
        hosts_path = '/etc/hosts'
    else:
        raise Exception('Unsupported OS: %s' % os.name)

    hosts = Hosts(hosts_path)
    for (host, val) in def_hosts.items():
        hosts.set_one(host,  val)
    hosts.write(hosts_path)