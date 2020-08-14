"""
this file is the entry of network operation
"""
import logging
from yzy_compute.network import bridge_lib
from yzy_compute.network import ip_lib
from yzy_compute.network import privileged
from common import constants
from yzy_compute import exception
from yzy_compute import utils


class LinuxBridgeManager(object):

    def __init__(self, namespace=None):
        super(LinuxBridgeManager, self).__init__()
        self.namespace = namespace

    def create_flat_network(self, network_id, physical_interface):
        """
        Create a non-vlan bridge unless it already exists.
        :param network_id: the network uuid
        :param physical_interface: the physical_interface bind to, such as 'eth0'
        :param vlan_id: the vlan id
        """
        bridge_name = self.get_bridge_name(network_id)
        if self.ensure_bridge(bridge_name, physical_interface):
            return physical_interface

    def create_vlan_network(self, network_id, physical_interface, vlan_id):
        """
        :param network_id: the network uuid
        :param physical_interface: the physical_interface bind to, such as 'eth0'
        :param vlan_id: the vlan id
        :return:
        """
        # first create the vlan interface
        interface = self._ensure_vlan(physical_interface, int(vlan_id))
        bridge_name = self.get_bridge_name(network_id)
        # then create the bridge and bind interface to bridge
        if self.ensure_bridge(bridge_name, interface):
            return interface

    def ensure_vlan_bridge(self, vlan_id, bridge_name, bridge_interface):
        interface = self._ensure_vlan(bridge_interface, int(vlan_id))
        self.ensure_bridge(bridge_name, interface)

    def network_delete(self, network_id, vlan_id=None):
        """
        :param network_id: the network uuid
        :param vlan_id: the vlan id
        :return:
        """
        logging.info("network_delete begin, network_id:%s, vlan_id:%s", network_id, vlan_id)
        bridge_name = self.get_bridge_name(network_id)
        logging.info("Delete %s", bridge_name)
        self.delete_bridge(bridge_name, vlan_id)

    @staticmethod
    def get_bridge_name(network_id):
        if not network_id:
            logging.warning("Invalid Network ID, will lead to incorrect "
                        "bridge name")
        bridge_name = constants.BRIDGE_NAME_PREFIX + \
            network_id[:constants.RESOURCE_ID_LENGTH]
        return bridge_name

    @staticmethod
    def get_subinterface_name(physical_interface, vlan_id):
        if not vlan_id:
            logging.warning("Invalid VLAN ID, will lead to incorrect "
                        "subinterface name")
        vlan_postfix = '.%s' % vlan_id
        interface_name = "%s%s" % (physical_interface, vlan_postfix)
        if len(interface_name) > constants.DEVICE_NAME_MAX_LEN:
            raise exception.InterfaceNameTooLong(interface=interface_name)
        return "%s%s" % (physical_interface, vlan_postfix)

    def _add_vlan(self, name, physical_interface, vlan_id):
        privileged.create_interface(name,
                                    self.namespace,
                                    "vlan",
                                    physical_interface=physical_interface,
                                    vlan_id=vlan_id)
        return ip_lib.IPDevice(name, namespace=self.namespace)

    def _ensure_vlan(self, physical_interface, vlan_id):
        """Create a vlan subinterface unless it already exists."""
        interface = self.get_subinterface_name(physical_interface, vlan_id)
        if not ip_lib.device_exists(interface):
            logging.info("Creating subinterface %(interface)s for "
                      "VLAN %(vlan_id)s on interface "
                      "%(physical_interface)s",
                      {'interface': interface, 'vlan_id': vlan_id,
                       'physical_interface': physical_interface})
            int_vlan = self._add_vlan(interface, physical_interface, vlan_id)
            int_vlan.disable_ipv6()
            int_vlan.link.set_up()
            logging.debug("Done creating subinterface %s", interface)
        return interface

    def ensure_bridge(self, bridge_name, interface=None,
                      update_interface=True):
        """Create a bridge unless it already exists."""
        # ensure_device_is_ready instead of device_exists is used here
        # because there are cases where the bridge exists but it's not UP
        logging.info("ensure bridge, bridge_name:%s, interface:%s", bridge_name, interface)
        if not ip_lib.ensure_device_is_ready(bridge_name):
            logging.info("Starting bridge %(bridge_name)s for subinterface "
                      "%(interface)s",
                      {'bridge_name': bridge_name, 'interface': interface})
            # add a bridge use pyroute2
            bridge_device = bridge_lib.BridgeDevice.addbr(bridge_name)
            if bridge_device.setfd(0)[0]:
                return
            if bridge_device.disable_stp()[0]:
                return
            if bridge_device.link.set_up():
                return
            logging.info("Done starting bridge %(bridge_name)s for "
                      "subinterface %(interface)s",
                      {'bridge_name': bridge_name, 'interface': interface})
        else:
            logging.info("bridge already exist")
            bridge_device = bridge_lib.BridgeDevice(bridge_name)

        if not interface:
            return bridge_name

        # Update IP info if necessary
        if update_interface:
            self.update_interface_ip_details(bridge_name, interface)

        # Check if the interface is part of the bridge
        if not bridge_device.owns_interface(interface):
            try:
                # Check if the interface is not enslaved in another bridge
                bridge = bridge_lib.BridgeDevice.get_interface_bridge(
                    interface)
                if bridge:
                    bridge.delif(interface)

                bridge_device.addif(interface)
            except Exception as e:
                logging.error("Unable to add %(interface)s to %(bridge_name)s"
                          "! Exception: %(e)s",
                          {'interface': interface, 'bridge_name': bridge_name,
                           'e': e})
                return
        return bridge_name

    @staticmethod
    def remove_interface(bridge_name, interface_name):
        bridge_device = bridge_lib.BridgeDevice(bridge_name)
        if bridge_device.exists():
            if not bridge_device.owns_interface(interface_name):
                return True
            logging.info("Removing device %(interface_name)s from bridge "
                      "%(bridge_name)s",
                      {'interface_name': interface_name,
                       'bridge_name': bridge_name})
            try:
                bridge_device.delif(interface_name)
                logging.info("Done removing device %(interface_name)s from "
                          "bridge %(bridge_name)s",
                          {'interface_name': interface_name,
                           'bridge_name': bridge_name})
                return True
            except Exception as e:
                    logging.error("Cannot remove %(interface_name)s from "
                              "%(bridge_name)s. error:%(error)s.",
                              {'interface_name': interface_name,
                               'bridge_name': bridge_name, 'error': e})
                    return False
        else:
            logging.info("Cannot remove device %(interface_name)s bridge "
                      "%(bridge_name)s does not exist",
                      {'interface_name': interface_name,
                       'bridge_name': bridge_name})
            return False

    def get_interface_details(self, interface, ip_version):
        device = ip_lib.IPDevice(interface)
        ips = device.addr.list(scope='global',
                               ip_version=ip_version)

        # Update default gateway if necessary
        gateway = device.route.get_gateway(scope='global',
                                           ip_version=ip_version)
        return ips, gateway

    def _update_interface_ip_details(self, destination, source, ips, gateway):
        dst_device = ip_lib.IPDevice(destination)
        src_device = ip_lib.IPDevice(source)

        # Append IP's to bridge if necessary
        if ips:
            for ip in ips:
                # If bridge ip address already exists, then don't add
                # otherwise will report error
                to = utils.cidr_to_ip(ip['cidr'])
                if not dst_device.addr.list(to=to):
                    logging.info("add ip address %s to %s", ip['cidr'], destination)
                    dst_device.addr.add(cidr=ip['cidr'])

        if gateway:
            # Ensure that the gateway can be updated by changing the metric
            metric = 100
            ip_version = ip_lib.get_ip_version(gateway['cidr'])
            if gateway['metric'] != ip_lib.IP_ROUTE_METRIC_DEFAULT[ip_version]:
                metric = gateway['metric'] - 1
            dst_device.route.add_gateway(gateway=gateway['via'],
                                         metric=metric)
            logging.info("dev %s add gateway %s", destination, gateway)
            src_device.route.delete_gateway(gateway=gateway['via'])
            logging.info("dev %s delete gateway %s", source, gateway)

        # Remove IP's from interface
        if ips:
            for ip in ips:
                src_device.addr.delete(cidr=ip['cidr'])
                logging.info("dev %s delete ip address %s", source, ip['cidr'])

    def update_interface_ip_details(self, destination, source):
        # Returns True if there were IPs or a gateway moved
        updated = False
        for ip_version in (constants.IP_VERSION_4, constants.IP_VERSION_6):
            ips, gateway = self.get_interface_details(source, ip_version)
            if ips or gateway:
                logging.info("update interface ip to:%s, ips:%s, gateway:%s", destination, ips, gateway)
                try:
                    self._update_interface_ip_details(destination, source, ips, gateway)
                except Exception as e:
                    logging.error("_update_interface_ip_details failed:%s", e, exc_info=True)
                updated = True

        return updated

    def delete_interface(self, interface):
        device = ip_lib.IPDevice(interface)
        if device.exists():
            logging.info("Deleting interface %s", interface)
            device.link.set_down()
            device.link.delete()
            logging.info("Done deleting interface %s", interface)

    def delete_bridge(self, bridge_name, vlan_id=None):
        bridge_device = bridge_lib.BridgeDevice(bridge_name)
        if bridge_device.exists():
            interfaces_on_bridge = bridge_device.get_interfaces()
            for interface in interfaces_on_bridge:
                self.remove_interface(bridge_name, interface)

                # Match the vlan/flat interface in the bridge.
                # If the bridge has an IP, it mean that this IP was moved
                # from the current interface, which also mean that this
                # interface was not created by the agent.
                updated = self.update_interface_ip_details(interface,
                                                           bridge_name)
                if not updated and interface.endswith('.%s' % vlan_id):
                    self.delete_interface(interface)

            try:
                logging.info("Deleting bridge %s", bridge_name)
                if bridge_device.link.set_down():
                    return
                if bridge_device.delbr():
                    return
                logging.info("Done deleting bridge %s", bridge_name)
            except Exception as e:
                    logging.error("delete bridge error:%s", e)
                    raise
        else:
            logging.info("Cannot delete bridge %s; it does not exist", bridge_name)

    def check_bridge_exist(self, network_id):
        bridge_name = self.get_bridge_name(network_id)
        bridge_device = bridge_lib.BridgeDevice(bridge_name)
        if bridge_device.exists():
            return True
        return False

    def add_addition_ip(self, network_id, ip_infos, gate_info):
        bridge_name = self.get_bridge_name(network_id)
        dst_device = ip_lib.IPDevice(bridge_name)
        ips, gateway = self.get_interface_details(bridge_name, constants.IP_VERSION_4)
        # 不存在的IP删除掉
        for ip in ips:
            flag = False
            for info in ip_infos:
                if utils.cidr_to_ip(ip['cidr']) == info['ip']:
                    flag = True
                    break
            if not flag:
                logging.info("delete ip address %s on %s", ip['cidr'], bridge_name)
                dst_device.addr.delete(cidr=ip['cidr'])

        for info in ip_infos:
            _, bit = utils.is_netmask(info['netmask'])
            ip_cidr = '%s/%s' % (info['ip'], bit)
            # 已经存在的IP不去修改
            flag = False
            for ip in ips:
                if ip_cidr == ip['cidr']:
                    flag = True
                    break
            if flag:
                continue
            try:
                if not dst_device.addr.list(to=info['ip']):
                    logging.info("add ip address %s to %s", info['ip'], bridge_name)
                    dst_device.addr.add(cidr=ip_cidr)
            except Exception as e:
                logging.exception("add ip info failed:%s", e)
        try:
            if gate_info.get('gateway'):
                dst_device.route.add_gateway(gateway=gate_info['gateway'])
                logging.info("dev %s add gateway %s", bridge_name, gate_info['gateway'])
        except Exception as e:
            logging.exception("add gateway info failed:%s", e)
