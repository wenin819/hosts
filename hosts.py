'''
Copyright (c) 2012 Michael Dominice

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
'''

from __future__ import print_function
import os
import datetime
import re
import socket
import struct
from functools import cmp_to_key


def normalize_ipv4(ip):
    try:
        _str = socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        raise ValueError
    return struct.unpack('!I', _str)[0]


def normalize_ipv6(ip):
    try:
        _str = socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:
        raise ValueError
    a, b = struct.unpack('!2Q', _str)
    return (a << 64) | b


def normalize_ip(ip):
    try:
        for fn in [normalize_ipv4, normalize_ipv6]:
            try:
                return fn(ip)
            except ValueError:
                continue
    except AttributeError:
        # Fall back, will fail on IPv6
        pass
    return map(int, ip.split('.'))


def compare_ip(ip1, ip2):
    """Comparator function for comparing two IPv4 address strings"""
    return normalize_ip(ip1) < normalize_ip(ip2)


def get_created_comment():
    return '\n'.join([
        '# Autogenerated by hosts.py',
        '# https://github.com/wenin819/hosts',
        '# Updated: %s' % datetime.datetime.now()
        ])


class Hosts(object):

    def __init__(self, path):
        self.hosts = {}
        self.read(path)

    def get_one(self, host_name, raise_on_not_found=False):
        if host_name in self.hosts:
            return self.hosts[host_name]
        try:
            socket.gethostbyname(host_name)
        except socket.gaierror:
            if raise_on_not_found:
                raise Exception('Unknown host: %s' % (host_name,))
        return '[Unknown]'

    def print_one(self, host_name):
        print(host_name, self.get_one(host_name))

    def print_all(self, host_names=None):
        if host_names is None or len(host_names) == 0:
            for host_name in self.hosts.keys():
                self.print_one(host_name)
        else:
            for host_name in host_names:
                self.print_one(host_name)

    def file_contents(self):
        reversed_hosts = {}
        for host_name, ip_address in self.hosts.items():
            if ip_address not in reversed_hosts:
                reversed_hosts[ip_address] = []
            reversed_hosts[ip_address].append(host_name)
        parts = []
        for ip_address in sorted(reversed_hosts.keys(), key=cmp_to_key(compare_ip)):
            parts.append('\n# -- %s -- #' % (ip_address,))
            for host_name in sorted(reversed_hosts[ip_address]):
                if not host_name:
                    continue
                parts.append('%s\t%s' % (ip_address, host_name))
            parts.append('# -- %s -- #' % (ip_address,))
        return '\n'.join([get_created_comment(), '\n'.join(parts), ''])

    def read(self, path):
        """Read the hosts file at the given location and parse the contents"""
        with open(path, 'r') as hosts_file:
            for line in hosts_file.read().split('\n'):
                if len(re.sub('\s*', '', line)) and not line.startswith('#'):
                    parts = re.split('\s+', line)
                    ip_address = parts[0]
                    for host_name in parts[1:]:
                        self.hosts[host_name] = ip_address

    def remove_one(self, host_name, raise_on_not_found=True):
        """Remove a mapping for the given host_name"""
        try:
            del self.hosts[host_name]
        except KeyError:
            if raise_on_not_found:
                raise

    def remove_all(self, host_names, raise_on_not_found=True):
        """Remove a mapping for the given host_name"""
        for host_name in host_names:
            self.remove_one(host_name, raise_on_not_found)

    def write(self, path):
        """Write the contents of this hosts definition to the provided path"""
        try:
            contents = self.file_contents()
        except Exception as e:
            raise e

        tmp_hosts_file_path = "{0}.tmp".format(path)  # Write atomically
        with open(tmp_hosts_file_path, 'w') as tmp_hosts_file:
            tmp_hosts_file.write(contents)

        orig_path = path + '.orig'
        if not os.path.exists(orig_path):
            os.rename(path, orig_path)
        os.rename(tmp_hosts_file_path, path)

    def set_one(self, host_name, ip_address):
        """Set the given hostname to map to the given IP address"""
        self.hosts[host_name] = ip_address

    def set_all(self, host_names, ip_address):
        """Set the given list of hostnames to map to the given IP address"""
        for host_name in host_names:
            self.set_one(host_name, ip_address)

    def alias_all(self, host_names, target, raise_on_not_found=True):
        """Set the given hostname to map to the IP address that target maps to"""
        self.set_all(host_names, self.get_one(target, raise_on_not_found))

if __name__ == '__main__':
    import os
    import argparse

    parser = argparse.ArgumentParser(description='Manipulate your hosts file')

    parser.add_argument('name', nargs='*')
    parser.add_argument('--silent', action='store_true', default=False)
    parser.add_argument('--set', dest='ip_address')
    parser.add_argument('--alias')
    parser.add_argument('--get', action='store_true', default=False)
    parser.add_argument('--remove', action='store_true', default=False)
    parser.add_argument('--dry', action='store_true', default=False)

    args = parser.parse_args()

    if os.name == 'nt':
        hosts_path = os.path.join(os.environ['SYSTEMROOT'], 'system32/drivers/etc/hosts')
    elif os.name == 'posix':
        hosts_path = '/etc/hosts'
    else:
        raise Exception('Unsupported OS: %s' % os.name)

    hosts = Hosts(hosts_path)

    try:
        if args.get:
            hosts.print_all(args.name)
        elif args.alias is not None:
            hosts.alias_all(args.name, args.alias, not args.silent)
            if args.dry:
                print(hosts.file_contents())
            else:
                hosts.write(hosts_path)
        elif args.ip_address is not None:
            hosts.set_all(args.name, args.ip_address)
            if args.dry:
                print(hosts.file_contents())
            else:
                hosts.write(hosts_path)
        elif args.remove:
            hosts.remove_all(args.name, not args.silent)
            if args.dry:
                print(hosts.file_contents())
            else:
                hosts.write(hosts_path)
    except Exception as e:
        print('Error: %s' % (e,))
        exit(1)
