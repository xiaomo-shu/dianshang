import errno
import netaddr
import logging
import re
from common.config import SERVER_CONF as CONF
from common import constants
from common import cmdutils
from yzy_compute import exception
from yzy_compute import utils
from yzy_compute.network import privileged
from pyroute2.netlink import rtnl
from pyroute2.netlink.rtnl import ifaddrmsg
from pyroute2.netlink.rtnl import ifinfmsg
from pyroute2 import NetlinkError


IP_ADDRESS_SCOPE = {rtnl.rtscopes['RT_SCOPE_UNIVERSE']: 'global',
                    rtnl.rtscopes['RT_SCOPE_SITE']: 'site',
                    rtnl.rtscopes['RT_SCOPE_LINK']: 'link',
                    rtnl.rtscopes['RT_SCOPE_HOST']: 'host'}

IP_ADDRESS_SCOPE_NAME = {v: k for k, v in IP_ADDRESS_SCOPE.items()}
IP_ADDRESS_EVENTS = {'RTM_NEWADDR': 'added',
                     'RTM_DELADDR': 'removed'}
IP_RULE_TABLES = {'default': 253,
                  'main': 254,
                  'local': 255}

IP_RULE_TABLES_NAMES = {v: k for k, v in IP_RULE_TABLES.items()}
IP_ROUTE_METRIC_DEFAULT = {constants.IP_VERSION_4: 0,
                           constants.IP_VERSION_6: 1024}


def add_namespace_to_cmd(cmd, namespace=None):
    """Add an optional namespace to the command."""

    return ['ip', 'netns', 'exec', namespace] + cmd if namespace else cmd


def add_ip_address(cidr, device, namespace=None, scope='global',
                   add_broadcast=True):
    """Add an IP address.

    :param cidr: IP address to add, in CIDR notation
    :param device: Device name to use in adding address
    :param namespace: The name of the namespace in which to add the address
    :param scope: scope of address being added
    :param add_broadcast: should broadcast address be added
    """
    net = netaddr.IPNetwork(cidr)
    broadcast = None
    if add_broadcast and net.version == 4:
        # NOTE(slaweq): in case if cidr is /32 net.broadcast is None so
        # same IP address as cidr should be set as broadcast
        broadcast = str(net.broadcast or net.ip)
    privileged.add_ip_address(
        net.version, str(net.ip), net.prefixlen,
        device, namespace, scope, broadcast)


def delete_ip_address(cidr, device, namespace=None):
    """Delete an IP address.

    :param cidr: IP address to delete, in CIDR notation
    :param device: Device name to use in deleting address
    :param namespace: The name of the namespace in which to delete the address
    """
    net = netaddr.IPNetwork(cidr)
    privileged.delete_ip_address(
        net.version, str(net.ip), net.prefixlen, device, namespace)


def flush_ip_addresses(ip_version, device, namespace=None):
    """Flush all IP addresses.

    :param ip_version: IP version of addresses to flush
    :param device: Device name to use in flushing addresses
    :param namespace: The name of the namespace in which to flush the addresses
    """
    privileged.flush_ip_addresses(ip_version, device, namespace)


def create_network_namespace(namespace, **kwargs):
    """Create a network namespace.

    :param namespace: The name of the namespace to create
    :param kwargs: Callers add any filters they use as kwargs
    """
    privileged.create_netns(namespace, **kwargs)


def delete_network_namespace(namespace, **kwargs):
    """Delete a network namespace.

    :param namespace: The name of the namespace to delete
    :param kwargs: Callers add any filters they use as kwargs
    """
    privileged.remove_netns(namespace, **kwargs)


def list_network_namespaces(**kwargs):
    """List all network namespace entries.

    :param kwargs: Callers add any filters they use as kwargs
    """
    return privileged.list_netns(**kwargs)


def network_namespace_exists(namespace, try_is_ready=False, **kwargs):
    """Check if a network namespace exists.

    :param namespace: The name of the namespace to check
    :param try_is_ready: Try to open the namespace to know if the namespace
                         is ready to be operated.
    :param kwargs: Callers add any filters they use as kwargs
    """
    if not try_is_ready:
        output = list_network_namespaces(**kwargs)
        return namespace in output

    try:
        privileged.open_namespace(namespace)
        return True
    except (RuntimeError, OSError):
        pass
    return False


class IPDevice(object):
    def __init__(self, name, namespace=None, kind='link'):
        super(IPDevice, self).__init__()
        self._name = name
        self.namespace = namespace
        self.kind = kind
        self.link = IpLinkCommand(self)
        self.addr = IpAddrCommand(self)
        self.route = IpRouteCommand(self)

    def __eq__(self, other):
        return (other is not None and self.name == other.name and
                self.namespace == other.namespace)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<IPDevice(name=%s, namespace=%s)>" % (self._name,
                                                      self.namespace)

    def exists(self):
        """Return True if the device exists in the namespace."""
        return privileged.interface_exists(self.name, self.namespace)

    def disable_ipv6(self):
        if not utils.is_enabled_and_bind_by_default():
            return
        sysctl_name = re.sub(r'\.', '/', self.name)
        cmd = ['net.ipv6.conf.%s.disable_ipv6=1' % sysctl_name]
        return sysctl(cmd, namespace=self.namespace)

    @property
    def name(self):
        if self._name:
            return self._name[:constants.DEVICE_NAME_MAX_LEN]
        return self._name

    @name.setter
    def name(self, name):
        self._name = name


class IpCommandBase(object):
    COMMAND = ''

    def __init__(self, parent):
        self._parent = parent

    # def _run(self, options, args):
    #     return self._parent._run(options, self.COMMAND, args)
    #
    # def _as_root(self, options, args, use_root_namespace=False):
    #     return self._parent._as_root(options,
    #                                  self.COMMAND,
    #                                  args,
    #                                  use_root_namespace=use_root_namespace)


class IpDeviceCommandBase(IpCommandBase):

    @property
    def name(self):
        return self._parent.name

    @property
    def kind(self):
        return self._parent.kind


class IpLinkCommand(IpDeviceCommandBase):
    COMMAND = 'link'

    def set_address(self, mac_address):
        privileged.set_link_attribute(
            self.name, self._parent.namespace, address=mac_address)

    def set_allmulticast_on(self):
        privileged.set_link_flags(
            self.name, self._parent.namespace, ifinfmsg.IFF_ALLMULTI)

    def set_mtu(self, mtu_size):
        try:
            privileged.set_link_attribute(
                self.name, self._parent.namespace, mtu=mtu_size)
        except NetlinkError as e:
            if e.code == errno.EINVAL:
                raise exception.InvalidArgument(parameter="MTU", value=mtu_size)
            raise

    def set_up(self):
        privileged.set_link_attribute(
            self.name, self._parent.namespace, state='up')

    def set_down(self):
        privileged.set_link_attribute(
            self.name, self._parent.namespace, state='down')

    def set_netns(self, namespace):
        privileged.set_link_attribute(
            self.name, self._parent.namespace, net_ns_fd=namespace)
        self._parent.namespace = namespace

    def set_name(self, name):
        privileged.set_link_attribute(
            self.name, self._parent.namespace, ifname=name)
        self._parent.name = name

    def set_alias(self, alias_name):
        privileged.set_link_attribute(
            self.name, self._parent.namespace, ifalias=alias_name)

    def create(self):
        privileged.create_interface(self.name, self._parent.namespace,
                                    self.kind)

    def delete(self):
        privileged.delete_interface(self.name, self._parent.namespace)

    @property
    def address(self):
        return self.attributes.get('link/ether')

    @property
    def state(self):
        return self.attributes.get('state')

    @property
    def allmulticast(self):
        return self.attributes.get('allmulticast')

    @property
    def mtu(self):
        return self.attributes.get('mtu')

    @property
    def qdisc(self):
        return self.attributes.get('qdisc')

    @property
    def qlen(self):
        return self.attributes.get('qlen')

    @property
    def alias(self):
        return self.attributes.get('alias')

    @property
    def link_kind(self):
        return self.attributes.get('link_kind')

    @property
    def attributes(self):
        return privileged.get_link_attributes(self.name,
                                              self._parent.namespace)


class IpAddrCommand(IpDeviceCommandBase):
    COMMAND = 'addr'

    def add(self, cidr, scope='global', add_broadcast=True):
        add_ip_address(cidr, self.name, self._parent.namespace, scope,
                       add_broadcast)

    def delete(self, cidr):
        delete_ip_address(cidr, self.name, self._parent.namespace)

    def flush(self, ip_version):
        flush_ip_addresses(ip_version, self.name, self._parent.namespace)

    def list(self, scope=None, to=None, filters=None, ip_version=None):
        """Get device details of a device named <self.name>."""
        def filter_device(device, filters):
            # Accepted filters: dynamic, permanent, tentative, dadfailed.
            for filter in filters:
                if filter == 'permanent' and device['dynamic']:
                    return False
                elif not device[filter]:
                    return False
            return True

        kwargs = {}
        if to:
            cidr = utils.ip_to_cidr(to)
            kwargs = {'address': utils.cidr_to_ip(cidr)}
            if not utils.is_cidr_host(cidr):
                kwargs['mask'] = utils.cidr_mask_length(cidr)
        if scope:
            kwargs['scope'] = IP_ADDRESS_SCOPE_NAME[scope]
        if ip_version:
            kwargs['family'] = utils.get_socket_address_family(
                ip_version)

        devices = get_devices_with_ip(self._parent.namespace, name=self.name,
                                      **kwargs)
        if not filters:
            return devices

        filtered_devices = []
        for device in (device for device in devices
                       if filter_device(device, filters)):
            filtered_devices.append(device)

        return filtered_devices

    # def wait_until_address_ready(self, address, wait_time=30):
    #     """Wait until an address is no longer marked 'tentative'
    #
    #     raises AddressNotReady if times out or address not present on interface
    #     """
    #     def is_address_ready():
    #         try:
    #             addr_info = self.list(to=address)[0]
    #         except IndexError:
    #             raise exception.AddressNotReady(
    #                 address=address,
    #                 reason='Address not present on interface')
    #         if not addr_info['tentative']:
    #             return True
    #         if addr_info['dadfailed']:
    #             raise exception.AddressNotReady(
    #                 address=address, reason='Duplicate address detected')
    #         return False
    #     errmsg = "Exceeded %s second limit waiting for address to leave the tentative state." % wait_time
    #     utils.wait_until_true(
    #         is_address_ready, timeout=wait_time, sleep=0.20,
    #         exception=exception.AddressNotReady(address=address, reason=errmsg))


class IpRouteCommand(IpDeviceCommandBase):
    COMMAND = 'route'

    def __init__(self, parent, table=None):
        super(IpRouteCommand, self).__init__(parent)
        self._table = table

    def add_gateway(self, gateway, metric=None, table=None, scope='global'):
        self.add_route(None, via=gateway, table=table, metric=metric,
                       scope=scope)

    def delete_gateway(self, gateway, table=None, scope=None):
        self.delete_route(None, device=self.name, via=gateway, table=table,
                          scope=scope)

    def list_routes(self, ip_version, scope=None, via=None, table=None,
                    **kwargs):
        table = table or self._table
        return list_ip_routes(self._parent.namespace, ip_version, scope=scope,
                              via=via, table=table, device=self.name, **kwargs)

    def list_onlink_routes(self, ip_version):
        routes = self.list_routes(ip_version, scope='link')
        return [r for r in routes if not r['source_prefix']]

    def add_onlink_route(self, cidr):
        self.add_route(cidr, scope='link')

    def delete_onlink_route(self, cidr):
        self.delete_route(cidr, device=self.name, scope='link')

    def get_gateway(self, scope=None, table=None,
                    ip_version=constants.IP_VERSION_4):
        routes = self.list_routes(ip_version, scope=scope, table=table)
        for route in routes:
            if route['via'] and route['cidr'] in constants.IP_ANY.values():
                return route

    def flush(self, ip_version, table=None, **kwargs):
        for route in self.list_routes(ip_version, table=table):
            self.delete_route(route['cidr'], device=route['device'],
                              via=route['via'], table=table, **kwargs)

    def add_route(self, cidr, via=None, table=None, metric=None, scope=None,
                  **kwargs):
        table = table or self._table
        add_ip_route(self._parent.namespace, cidr, device=self.name, via=via,
                     table=table, metric=metric, scope=scope, **kwargs)

    def delete_route(self, cidr, device=None, via=None, table=None, scope=None,
                     **kwargs):
        table = table or self._table
        delete_ip_route(self._parent.namespace, cidr, device=device, via=via,
                        table=table, scope=scope, **kwargs)


class IPWrapper(object):
    def __init__(self, namespace=None):
        super(IPWrapper, self).__init__()
        self.namespace = namespace
        self.netns = IpNetnsCommand(self)

    def device(self, name):
        return IPDevice(name, namespace=self.namespace)


class IpNetnsCommand(IpCommandBase):
    COMMAND = 'netns'

    def add(self, name):
        create_network_namespace(name)
        wrapper = IPWrapper(namespace=name)
        wrapper.netns.execute(['sysctl', '-w',
                               'net.ipv4.conf.all.promote_secondaries=1'])
        return wrapper

    def delete(self, name):
        delete_network_namespace(name)

    def execute(self, cmds, addl_env=None, check_exit_code=True,
                log_errors=True, run_as_root=False):
        ns_params = []
        if self._parent.namespace:
            run_as_root = True
            ns_params = ['ip', 'netns', 'exec', self._parent.namespace]

        env_params = []
        if addl_env:
            env_params = (['env'] +
                          ['%s=%s' % pair for pair in addl_env.items()])
        cmd = ns_params + env_params + list(cmds)
        return cmdutils.execute(*cmd, check_exit_code=check_exit_code, log_errors=log_errors,
                                    run_as_root=run_as_root)

    def exists(self, name):
        return network_namespace_exists(name)


def get_attr(pyroute2_obj, attr_name):
    """Get an attribute from a PyRoute2 object"""
    rule_attrs = pyroute2_obj.get('attrs', [])
    for attr in (attr for attr in rule_attrs if attr[0] == attr_name):
        return attr[1]


def _parse_ip_address(pyroute2_address, device_name):
    ip = get_attr(pyroute2_address, 'IFA_ADDRESS')
    ip_length = pyroute2_address['prefixlen']
    event = IP_ADDRESS_EVENTS.get(pyroute2_address.get('event'))
    cidr = utils.ip_to_cidr(ip, prefix=ip_length)
    flags = get_attr(pyroute2_address, 'IFA_FLAGS')
    dynamic = not bool(flags & ifaddrmsg.IFA_F_PERMANENT)
    tentative = bool(flags & ifaddrmsg.IFA_F_TENTATIVE)
    dadfailed = bool(flags & ifaddrmsg.IFA_F_DADFAILED)
    scope = IP_ADDRESS_SCOPE[pyroute2_address['scope']]
    return {'name': device_name,
            'cidr': cidr,
            'scope': scope,
            'broadcast': get_attr(pyroute2_address, 'IFA_BROADCAST'),
            'dynamic': dynamic,
            'tentative': tentative,
            'dadfailed': dadfailed,
            'event': event}


def _parse_link_device(namespace, device, **kwargs):
    """Parse pytoute2 link device information

    For each link device, the IP address information is retrieved and returned
    in a dictionary.
    IP address scope: http://linux-ip.net/html/tools-ip-address.html
    """
    retval = []
    name = get_attr(device, 'IFLA_IFNAME')
    ip_addresses = privileged.get_ip_addresses(namespace,
                                               index=device['index'],
                                               **kwargs)
    for ip_address in ip_addresses:
        retval.append(_parse_ip_address(ip_address, name))
    return retval


def get_devices_with_ip(namespace, name=None, **kwargs):
    link_args = {}
    if name:
        link_args['ifname'] = name
    devices = privileged.get_link_devices(namespace, **link_args)
    retval = []
    for parsed_ips in (_parse_link_device(namespace, device, **kwargs)
                       for device in devices):
        retval += parsed_ips
    return retval


def ensure_device_is_ready(device_name, namespace=None):
    dev = IPDevice(device_name, namespace=namespace)
    try:
        # Ensure the device has a MAC address and is up, even if it is already
        # up. If the device doesn't exist, a RuntimeError will be raised.
        if not dev.link.address:
            logging.error("Device %s cannot be used as it has no MAC "
                      "address", device_name)
            return False
        dev.link.set_up()
    except:
        return False
    return True


def device_exists(device_name, namespace=None):
    """Return True if the device exists in the namespace."""
    return IPDevice(device_name, namespace=namespace).exists()



def get_devices_info(namespace, **kwargs):
    devices = privileged.get_link_devices(namespace, **kwargs)
    retval = {}
    for device in devices:
        ret = {'index': device['index'],
               'name': get_attr(device, 'IFLA_IFNAME'),
               'operstate': get_attr(device, 'IFLA_OPERSTATE'),
               'linkmode': get_attr(device, 'IFLA_LINKMODE'),
               'mtu': get_attr(device, 'IFLA_MTU'),
               'promiscuity': get_attr(device, 'IFLA_PROMISCUITY'),
               'mac': get_attr(device, 'IFLA_ADDRESS'),
               'broadcast': get_attr(device, 'IFLA_BROADCAST')}
        ifla_link = get_attr(device, 'IFLA_LINK')
        if ifla_link:
            ret['parent_index'] = ifla_link
        ifla_linkinfo = get_attr(device, 'IFLA_LINKINFO')
        if ifla_linkinfo:
            ret['kind'] = get_attr(ifla_linkinfo, 'IFLA_INFO_KIND')
            ifla_data = get_attr(ifla_linkinfo, 'IFLA_INFO_DATA')
            if ret['kind'] == 'vxlan':
                ret['vxlan_id'] = get_attr(ifla_data, 'IFLA_VXLAN_ID')
                ret['vxlan_group'] = get_attr(ifla_data, 'IFLA_VXLAN_GROUP')
                ret['vxlan_link_index'] = get_attr(ifla_data,
                                                   'IFLA_VXLAN_LINK')
            elif ret['kind'] == 'vlan':
                ret['vlan_id'] = get_attr(ifla_data, 'IFLA_VLAN_ID')
        retval[device['index']] = ret

    for device in retval.values():
        if device.get('parent_index'):
            parent_device = retval.get(device['parent_index'])
            if parent_device:
                device['parent_name'] = parent_device['name']
        elif device.get('vxlan_link_index'):
            device['vxlan_link_name'] = (
                retval[device['vxlan_link_index']]['name'])

    return list(retval.values())


def vlan_in_use(segmentation_id, namespace=None):
    """Return True if VLAN ID is in use by an interface, else False."""
    interfaces = get_devices_info(namespace)
    vlans = {interface.get('vlan_id') for interface in interfaces
             if interface.get('vlan_id')}
    return segmentation_id in vlans


def sysctl(cmd, namespace=None, log_errors=True):
    """Run sysctl command 'cmd'

    @param cmd: a list containing the sysctl command to run
    @param namespace: network namespace to run command in
    @param log_fail_as_error: failure logged as LOG.error

    execute() doesn't return the exit status of the command it runs,
    it returns stdout and stderr. Setting check_exit_code=True will cause
    it to raise a RuntimeError if the exit status of the command is
    non-zero, which in sysctl's case is an error. So we're normalizing
    that into zero (success) and one (failure) here to mimic what
    "echo $?" in a shell would be.

    This is all because sysctl is too verbose and prints the value you
    just set on success, unlike most other utilities that print nothing.

    execute() will have dumped a message to the logs with the actual
    output on failure, so it's not lost, and we don't need to print it
    here.
    """
    cmd = ['sysctl', '-w'] + cmd
    ip_wrapper = IPWrapper(namespace=namespace)
    try:
        ip_wrapper.netns.execute(cmd, run_as_root=True,
                                 log_errors=log_errors)
    except RuntimeError as rte:
        logging.warning(
            "Setting %(cmd)s in namespace %(ns)s failed: %(err)s.",
            {'cmd': cmd,
             'ns': namespace,
             'err': rte})
        return 1

    return 0


def get_ip_version(ip_or_cidr):
    return netaddr.IPNetwork(ip_or_cidr).version


def add_ip_route(namespace, cidr, device=None, via=None, table=None,
                 metric=None, scope=None, **kwargs):
    """Add an IP route"""
    if table:
        table = IP_RULE_TABLES.get(table, table)
    ip_version = get_ip_version(cidr or via)
    privileged.add_ip_route(namespace, cidr, ip_version,
                            device=device, via=via, table=table,
                            metric=metric, scope=scope, **kwargs)


def delete_ip_route(namespace, cidr, device=None, via=None, table=None,
                    scope=None, **kwargs):
    """Delete an IP route"""
    if table:
        table = IP_RULE_TABLES.get(table, table)
    ip_version = get_ip_version(cidr or via)
    privileged.delete_ip_route(namespace, cidr, ip_version,
                               device=device, via=via, table=table,
                               scope=scope, **kwargs)


def list_ip_routes(namespace, ip_version, scope=None, via=None, table=None,
                   device=None, **kwargs):
    """List IP routes"""
    def get_device(index, devices):
        for device in (d for d in devices if d['index'] == index):
            return get_attr(device, 'IFLA_IFNAME')

    table = table if table else 'main'
    table = IP_RULE_TABLES.get(table, table)
    routes = privileged.list_ip_routes(namespace, ip_version, device=device,
                                       table=table, **kwargs)
    devices = privileged.get_link_devices(namespace)
    ret = []
    for route in routes:
        cidr = get_attr(route, 'RTA_DST')
        if cidr:
            cidr = '%s/%s' % (cidr, route['dst_len'])
        else:
            cidr = constants.IP_ANY[ip_version]
        table = int(get_attr(route, 'RTA_TABLE'))
        metric = (get_attr(route, 'RTA_PRIORITY') or IP_ROUTE_METRIC_DEFAULT[ip_version])
        value = {
            'table': IP_RULE_TABLES_NAMES.get(table, table),
            'source_prefix': get_attr(route, 'RTA_PREFSRC'),
            'cidr': cidr,
            'scope': IP_ADDRESS_SCOPE[int(route['scope'])],
            'device': get_device(int(get_attr(route, 'RTA_OIF')), devices),
            'via': get_attr(route, 'RTA_GATEWAY'),
            'metric': metric,
        }

        ret.append(value)

    if scope:
        ret = [route for route in ret if route['scope'] == scope]
    if via:
        ret = [route for route in ret if route['via'] == via]

    return ret
