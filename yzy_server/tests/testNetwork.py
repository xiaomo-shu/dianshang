# -*- coding:utf-8 -*-


import netaddr

# ip = netaddr.IPNetwork("10.10.25.0")
ip = netaddr.IPAddress("10.10.25.3")
print(ip.netmask_bits())

netmask = netaddr.IPAddress("255.255.248.0")
print(netmask.bits())


network = netaddr.IPNetwork("10.10.24.0/21")
print(network.netmask)
print(network.size)

ipNetList = netaddr.iprange_to_cidrs("192.168.1.1", "192.168.1.100")

# if __name__ == "__main__":
#     print(ip.version)

print(ip.bits())


def ip_to_cidr(ip, prefix=None):
    """Convert an ip with no prefix to cidr notation

    :param ip: An ipv4 or ipv6 address.  Convertable to netaddr.IPNetwork.
    :param prefix: Optional prefix.  If None, the default 32 will be used for
        ipv4 and 128 for ipv6.
    """
    net = netaddr.IPNetwork(ip)
    if prefix is not None:
        # Can't pass ip and prefix separately.  Must concatenate strings.
        net = netaddr.IPNetwork(str(net.ip) + '/' + str(prefix))
    return str(net)


print(ip_to_cidr("10.10.240.0", 22))

ipNetList = netaddr.iprange_to_cidrs("10.10.25.3", "10.10.25.30")
print(ipNetList)



s1 = "00001010.00001010.00011000.00000000"
s1 = s1.replace(".", "")
print(int(s1, 2))
