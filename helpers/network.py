# -*- coding: utf-8 -*-
import array
import fcntl
import socket
import struct
import platform


class Network:

    @staticmethod
    def get_local_interfaces():
        """
            Returns a dictionary of name:ip key value pairs.
            Linux Only!
            Source: https://gist.github.com/bubthegreat/24c0c43ad159d8dfed1a5d3f6ca99f9b
        """
        if platform.system() == "Linux":
            # Max possible bytes for interface result.  Will truncate if more than 4096 characters to describe interfaces.
            MAX_BYTES = 4096

            # We're going to make a blank byte array to operate on.  This is our fill char.
            FILL_CHAR = b'\0'

            # Command defined in ioctl.h for the system operation for get iface list
            # Defined at https://code.woboq.org/qt5/include/bits/ioctls.h.html under
            # /* Socket configuration controls. */ section.
            SIOCGIFCONF = 0x8912

            # Make a dgram socket to use as our file descriptor that we'll operate on.
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Make a byte array with our fill character.
            names = array.array('B', MAX_BYTES * FILL_CHAR)

            # Get the address of our names byte array for use in our struct.
            names_address, names_length = names.buffer_info()

            # Create a mutable byte buffer to store the data in
            mutable_byte_buffer = struct.pack('iL', MAX_BYTES, names_address)

            # mutate our mutable_byte_buffer with the results of get_iface_list.
            # NOTE: mutated_byte_buffer is just a reference to mutable_byte_buffer - for the sake of clarity we've defined them as
            # separate variables, however they are the same address space - that's how fcntl.ioctl() works since the mutate_flag=True
            # by default.
            mutated_byte_buffer = fcntl.ioctl(sock.fileno(), SIOCGIFCONF, mutable_byte_buffer)

            # Get our max_bytes of our mutated byte buffer that points to the names variable address space.
            max_bytes_out, names_address_out = struct.unpack('iL', mutated_byte_buffer)

            # Convert names to a bytes array - keep in mind we've mutated the names array, so now our bytes out should represent
            # the bytes results of the get iface list ioctl command.
            namestr = names.tostring()

            namestr[:max_bytes_out]

            bytes_out = namestr[:max_bytes_out]

            # Each entry is 40 bytes long.  The first 16 bytes are the name string.
            # the 20-24th bytes are IP address octet strings in byte form - one for each byte.
            # Don't know what 17-19 are, or bytes 25:40.
            ip_dict = {}
            for i in range(0, max_bytes_out, 40):
                name = namestr[i: i + 16].split(FILL_CHAR, 1)[0]
                name = name.decode('utf-8')
                ip_bytes = namestr[i + 20:i + 24]
                full_addr = []
                for netaddr in ip_bytes:
                    if isinstance(netaddr, int):
                        full_addr.append(str(netaddr))
                    elif isinstance(netaddr, str):
                        full_addr.append(str(ord(netaddr)))
                if not (name == "lo" or name.startswith(("docker", "br-", "veth"))):
                    ip_dict[name] = '.'.join(full_addr)

            return ip_dict
        else:
            # TODO use netifaces with venv on MacOS
            raise Exception("Only available for linux!")

    @staticmethod
    def get_primary_ip():
        """
        https://stackoverflow.com/a/28950776/1141214
        :return:
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(("10.255.255.255", 1))
            ip_address = s.getsockname()[0]
        except:
            ip_address = "127.0.0.1"
        finally:
            s.close()
        return ip_address
