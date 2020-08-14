import errno
import logging
import socket
import pyroute2
from pyroute2 import netlink
from pyroute2.netlink import rtnl
from pyroute2 import NetlinkError
from pyroute2.netlink.rtnl import ifinfmsg
from pyroute2 import netns
from yzy_compute import exception


_IP_VERSION_FAMILY_MAP = {4: socket.AF_INET, 6: socket.AF_INET6}


def get_iproute(namespace):
    # From iproute.py:
    # `IPRoute` -- RTNL API to the current network namespace
    # `NetNS` -- RTNL API to another network namespace
    if namespace:
        # do not try and create the namespace
        return pyroute2.NetNS(namespace, flags=0)
    else:
        return pyroute2.IPRoute()


def get_link_id(device, namespace):
    try:
        with get_iproute(namespace) as ip:
            return ip.link_lookup(ifname=device)[0]
    except IndexError:
        raise exception.NetworkInterfaceNotFound(device=device, namespace=namespace)


def interface_exists(ifname, namespace):
    try:
        idx = get_link_id(ifname, namespace)
        return bool(idx)
    except exception.NetworkInterfaceNotFound:
        return False
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False
        raise


def _translate_ip_device_exception(e, device=None, namespace=None):
    if e.code == errno.ENODEV:
        raise exception.NetworkInterfaceNotFound(device=device, namespace=namespace)
    if e.code == errno.EOPNOTSUPP:
        raise exception.InterfaceOperationNotSupported(device=device,
                                             namespace=namespace)


def _run_iproute_link(command, device, namespace=None, **kwargs):
    try:
        with get_iproute(namespace) as ip:
            idx = get_link_id(device, namespace)
            return ip.link(command, index=idx, **kwargs)
    except NetlinkError as e:
        _translate_ip_device_exception(e, device, namespace)
        raise
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise exception.NetworkNamespaceNotFound(netns_name=namespace)
        raise


def set_link_attribute(device, namespace, **attributes):
    return _run_iproute_link("set", device, namespace, **attributes)


def set_link_flags(device, namespace, flags):
    link = _run_iproute_link("get", device, namespace)[0]
    new_flags = flags | link['flags']
    return _run_iproute_link("set", device, namespace, flags=new_flags)


def create_interface(ifname, namespace, kind, **kwargs):
    # ifname = ifname[:constants.DEVICE_NAME_MAX_LEN]
    try:
        with get_iproute(namespace) as ip:
            physical_interface = kwargs.pop("physical_interface", None)
            if physical_interface:
                link_key = "vxlan_link" if kind == "vxlan" else "link"
                kwargs[link_key] = get_link_id(physical_interface, namespace)
            return ip.link("add", ifname=ifname, kind=kind, **kwargs)
    except NetlinkError as e:
        if e.code == errno.EEXIST:
            logging.warning("Interface %(device)s already exists.", ifname)
        else:
            raise
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise exception.NetworkNamespaceNotFound(netns_name=namespace)
        raise


def delete_interface(ifname, namespace, **kwargs):
    _run_iproute_link("del", ifname, namespace, **kwargs)


def get_link_attributes(device, namespace):
    link = _run_iproute_link("get", device, namespace)[0]
    return {
        'mtu': link.get_attr('IFLA_MTU'),
        'qlen': link.get_attr('IFLA_TXQLEN'),
        'state': link.get_attr('IFLA_OPERSTATE'),
        'qdisc': link.get_attr('IFLA_QDISC'),
        'brd': link.get_attr('IFLA_BROADCAST'),
        'link/ether': link.get_attr('IFLA_ADDRESS'),
        'alias': link.get_attr('IFLA_IFALIAS'),
        'allmulticast': bool(link['flags'] & ifinfmsg.IFF_ALLMULTI),
        'link_kind': link.get_nested('IFLA_LINKINFO', 'IFLA_INFO_KIND')
    }


def _run_iproute_addr(command, device, namespace, **kwargs):
    try:
        with get_iproute(namespace) as ip:
            idx = get_link_id(device, namespace)
            return ip.addr(command, index=idx, **kwargs)
    except NetlinkError as e:
        _translate_ip_device_exception(e, device, namespace)
        raise
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise exception.NetworkNamespaceNotFound(netns_name=namespace)
        raise


def _get_scope_name(scope):
    """Return the name of the scope (given as a number), or the scope number
    if the name is unknown.

    For backward compatibility (with "ip" tool) "global" scope is converted to
    "universe" before converting to number
    """
    scope = 'universe' if scope == 'global' else scope
    return rtnl.rt_scope.get(scope, scope)


def add_ip_address(ip_version, ip, prefixlen, device, namespace, scope,
                   broadcast=None):
    family = _IP_VERSION_FAMILY_MAP[ip_version]
    try:
        _run_iproute_addr('add',
                          device,
                          namespace,
                          address=ip,
                          mask=prefixlen,
                          family=family,
                          broadcast=broadcast,
                          scope=_get_scope_name(scope))
    except NetlinkError as e:
        if e.code == errno.EEXIST:
            logging.warning('IP address %(ip)s already configured on %(device)s.', ip, device)
        else:
            raise


def delete_ip_address(ip_version, ip, prefixlen, device, namespace):
    family = _IP_VERSION_FAMILY_MAP[ip_version]
    try:
        _run_iproute_addr("delete",
                          device,
                          namespace,
                          address=ip,
                          mask=prefixlen,
                          family=family)
    except NetlinkError as e:
        # when trying to delete a non-existent IP address, pyroute2 raises
        # NetlinkError with code EADDRNOTAVAIL (99, 'Cannot assign requested
        # address')
        # this shouldn't raise an error
        if e.code == errno.EADDRNOTAVAIL:
            return
        raise


def flush_ip_addresses(ip_version, device, namespace):
    family = _IP_VERSION_FAMILY_MAP[ip_version]
    try:
        with get_iproute(namespace) as ip:
            idx = get_link_id(device, namespace)
            ip.flush_addr(index=idx, family=family)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise exception.NetworkNamespaceNotFound(netns_name=namespace)
        raise


def make_serializable(value):
    """Make a pyroute2 object serializable

    This function converts 'netlink.nla_slot' object (key, value) in a list
    of two elements.
    """
    if isinstance(value, list):
        return [make_serializable(item) for item in value]
    elif isinstance(value, dict):
        return {key: make_serializable(data) for key, data in value.items()}
    elif isinstance(value, netlink.nla_slot):
        return [value[0], make_serializable(value[1])]
    elif isinstance(value, tuple):
        return tuple(make_serializable(item) for item in value)
    return value


def get_link_devices(namespace, **kwargs):
    """List interfaces in a namespace

    :return: (list) interfaces in a namespace
    """
    try:
        with get_iproute(namespace) as ip:
            return make_serializable(ip.get_links(**kwargs))
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise exception.NetworkNamespaceNotFound(netns_name=namespace)
        raise

def get_ip_addresses(namespace, **kwargs):
    """List of IP addresses in a namespace

    :return: (tuple) IP addresses in a namespace
    """
    try:
        with get_iproute(namespace) as ip:
            return make_serializable(ip.get_addr(**kwargs))
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise exception.NetworkNamespaceNotFound(netns_name=namespace)
        raise


def create_netns(name, **kwargs):
    """Create a network namespace.

    :param name: The name of the namespace to create
    """
    try:
        netns.create(name, **kwargs)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def remove_netns(name, **kwargs):
    """Remove a network namespace.

    :param name: The name of the namespace to remove
    """
    try:
        netns.remove(name, **kwargs)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def list_netns(**kwargs):
    """List network namespaces.

    Caller requires raised priveleges to list namespaces
    """
    return netns.listnetns(**kwargs)


def open_namespace(namespace):
    """Open namespace to test if the namespace is ready to be manipulated"""
    with pyroute2.NetNS(namespace, flags=0):
        pass


def _make_pyroute2_route_args(namespace, ip_version, cidr, device, via, table,
                              metric, scope, protocol):
    """Returns a dictionary of arguments to be used in pyroute route commands

    :param namespace: (string) name of the namespace
    :param ip_version: (int) [4, 6]
    :param cidr: (string) source IP or CIDR address (IPv4, IPv6)
    :param device: (string) input interface name
    :param via: (string) gateway IP address
    :param table: (string, int) table number or name
    :param metric: (int) route metric
    :param scope: (int) route scope
    :param protocol: (string) protocol name (pyroute2.netlink.rtnl.rt_proto)
    :return: a dictionary with the kwargs needed in pyroute rule commands
    """
    args = {'family': _IP_VERSION_FAMILY_MAP[ip_version]}
    if not scope:
        scope = 'global' if via else 'link'
    scope = _get_scope_name(scope)
    if scope:
        args['scope'] = scope
    if cidr:
        args['dst'] = cidr
    if device:
        args['oif'] = get_link_id(device, namespace)
    if via:
        args['gateway'] = via
    if table:
        args['table'] = int(table)
    if metric:
        args['priority'] = int(metric)
    if protocol:
        args['proto'] = protocol
    return args


def add_ip_route(namespace, cidr, ip_version, device=None, via=None,
                 table=None, metric=None, scope=None, **kwargs):
    """Add an IP route"""
    kwargs.update(_make_pyroute2_route_args(
        namespace, ip_version, cidr, device, via, table, metric, scope,
        'static'))
    try:
        with get_iproute(namespace) as ip:
            ip.route('replace', **kwargs)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise exception.NetworkNamespaceNotFound(netns_name=namespace)
        raise


def delete_ip_route(namespace, cidr, ip_version, device=None, via=None,
                    table=None, scope=None, **kwargs):
    """Delete an IP route"""
    kwargs.update(_make_pyroute2_route_args(
        namespace, ip_version, cidr, device, via, table, None, scope, None))
    try:
        with get_iproute(namespace) as ip:
            ip.route('del', **kwargs)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise exception.NetworkNamespaceNotFound(netns_name=namespace)
        raise


def list_ip_routes(namespace, ip_version, device=None, table=None, **kwargs):
    """List IP routes"""
    kwargs.update(_make_pyroute2_route_args(
        namespace, ip_version, None, device, None, table, None, None, None))
    try:
        with get_iproute(namespace) as ip:
            return make_serializable(ip.route('show', **kwargs))
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise exception.NetworkNamespaceNotFound(netns_name=namespace)
        raise
