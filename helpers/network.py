# -*- coding: utf-8 -*-
import array
import fcntl
import platform
import socket
import struct
import sys
from http import client as httplib
from urllib.request import urlopen

from helpers.cli import CLI


class Network:

    STATUS_OK_200 = 200

    @staticmethod
    def get_local_interfaces(all_=False):
        """
        Returns a dictionary of name:ip key value pairs.
        Linux Only!
        Source: https://gist.github.com/bubthegreat/24c0c43ad159d8dfed1a5d3f6ca99f9b

        Args:
            all_ (bool): If False, filter virtual interfaces such VMWare,
                        Docker etc...
        Returns:
            dict
        """
        ip_dict = {}
        excluded_interfaces = ('lo', 'docker', 'br-', 'veth', 'vmnet')

        if platform.system() == 'Linux':
            # Max possible bytes for interface result.
            # Will truncate if more than 4096 characters to describe interfaces.
            MAX_BYTES = 4096

            # We're going to make a blank byte array to operate on.
            # This is our fill char.
            FILL_CHAR = b'\0'

            # Command defined in ioctl.h for the system operation for get iface
            # list.
            # Defined at https://code.woboq.org/qt5/include/bits/ioctls.h.html
            # under /* Socket configuration controls. */ section.
            SIOCGIFCONF = 0x8912

            # Make a dgram socket to use as our file descriptor that we'll
            # operate on.
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Make a byte array with our fill character.
            names = array.array('B', MAX_BYTES * FILL_CHAR)

            # Get the address of our names byte array for use in our struct.
            names_address, names_length = names.buffer_info()

            # Create a mutable byte buffer to store the data in
            mutable_byte_buffer = struct.pack('iL', MAX_BYTES, names_address)

            # mutate our mutable_byte_buffer with the results of get_iface_list.
            # NOTE: mutated_byte_buffer is just a reference to
            # mutable_byte_buffer - for the sake of clarity we've defined
            # them as separate variables, however they are the same address
            # space - that's how fcntl.ioctl() works since the mutate_flag=True
            # by default.
            mutated_byte_buffer = fcntl.ioctl(sock.fileno(),
                                              SIOCGIFCONF,
                                              mutable_byte_buffer)

            # Get our max_bytes of our mutated byte buffer
            # that points to the names variable address space.
            max_bytes_out, names_address_out = struct.unpack(
                'iL',
                mutated_byte_buffer)

            # Convert names to a bytes array - keep in mind we've mutated the
            # names array, so now our bytes out should represent the bytes
            # results of the get iface list ioctl command.
            namestr = names.tobytes()

            namestr[:max_bytes_out]

            bytes_out = namestr[:max_bytes_out]

            # Each entry is 40 bytes long. The first 16 bytes are the
            # name string. The 20-24th bytes are IP address octet strings in
            # byte form - one for each byte.
            # Don't know what 17-19 are, or bytes 25:40.

            for i in range(0, max_bytes_out, 40):
                name = namestr[i: i + 16].split(FILL_CHAR, 1)[0]
                name = name.decode()
                ip_bytes = namestr[i + 20:i + 24]
                full_addr = []
                for netaddr in ip_bytes:
                    if isinstance(netaddr, int):
                        full_addr.append(str(netaddr))
                    elif isinstance(netaddr, str):
                        full_addr.append(str(ord(netaddr)))
                if not name.startswith(excluded_interfaces) or all_:
                    ip_dict[name] = '.'.join(full_addr)
        else:
            try:
                import netifaces
            except ImportError:
                CLI.colored_print('You must install netinfaces first! Please '
                                  'type `pip install netifaces --user`',
                                  CLI.COLOR_ERROR)
                sys.exit(1)

            for interface in netifaces.interfaces():
                if not interface.startswith(excluded_interfaces) or all_:
                    ifaddresses = netifaces.ifaddresses(interface)
                    if (
                        ifaddresses.get(netifaces.AF_INET)
                        and ifaddresses.get(netifaces.AF_INET)[0].get('addr')
                    ):
                        addresses = ifaddresses.get(netifaces.AF_INET)
                        ip_dict[interface] = addresses[0].get('addr')
                        for i in range(1, len(addresses)):
                            virtual_interface = '{interface}:{idx}'.format(
                                interface=interface,
                                idx=i
                            )
                            ip_dict[virtual_interface] = addresses[i]['addr']

        return ip_dict

    @staticmethod
    def get_primary_ip():
        """
        https://stackoverflow.com/a/28950776/1141214
        :return:
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            # …but it can't be a broadcast address, or you'll get
            # `Permission denied`. See recent comments on the same SO answer:
            # https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib/28950776#comment128390746_28950776
            s.connect(('10.255.255.254', 1))
            ip_address = s.getsockname()[0]
        except:
            ip_address = None
        finally:
            s.close()
        return ip_address

    @classmethod
    def get_primary_interface(cls):
        """
        :return: string
        """
        primary_ip = cls.get_primary_ip()
        local_interfaces = cls.get_local_interfaces()

        for interface, ip_address in local_interfaces.items():
            if ip_address == primary_ip:
                return interface

        return 'eth0'

    @staticmethod
    def status_check(hostname, endpoint, port=80, secure=False):
        try:
            if secure:
                conn = httplib.HTTPSConnection(
                    f'{hostname}:{port}',
                    timeout=10)
            else:
                conn = httplib.HTTPConnection(
                    f'{hostname}:{port}',
                    timeout=10)
            conn.request('GET', endpoint)
            response = conn.getresponse()
            return response.status
        except:
            pass

        return

    @staticmethod
    def is_port_open(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', int(port)))
        return result == 0

    @staticmethod
    def curl(url):
        try:
            response = urlopen(url)
            data = response.read()
            if isinstance(data, str):
                # Python 2
                return data
            else:
                # Python 3
                return data.decode(response.headers.get_content_charset())
        except Exception as e:
            pass
        return
