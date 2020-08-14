"""
Configuration for libvirt objects.

This is refer to the nova code
"""

import logging
import six
from lxml import etree
from common.constants import Mi


class LibvirtConfigObject(object):

    def __init__(self, **kwargs):
        super(LibvirtConfigObject, self).__init__()

        self.root_name = kwargs.get("root_name")
        self.ns_prefix = kwargs.get('ns_prefix')
        self.ns_uri = kwargs.get('ns_uri')

    def _new_node(self, node_name, **kwargs):
        if self.ns_uri is None:
            return etree.Element(node_name, **kwargs)
        else:
            return etree.Element(node_name, nsmap={self.ns_prefix: self.ns_uri},
                                 **kwargs)

    def _text_node(self, node_name, value, **kwargs):
        child = etree.Element(node_name, **kwargs)
        child.text = six.text_type(value)
        return child

    def format_dom(self):
        return self._new_node(self.root_name)

    def parse_str(self, xmlstr):
        self.parse_dom(etree.fromstring(xmlstr))

    def parse_dom(self, xmldoc):
        if self.root_name != xmldoc.tag:
            msg = ("Root element name should be '%(name)s' not '%(tag)s'" %
                   {'name': self.root_name, 'tag': xmldoc.tag})
            raise Exception(msg)
            # raise exception.InvalidInput(msg)

    def to_xml(self, pretty_print=True):
        root = self.format_dom()
        xml_str = etree.tostring(root, encoding='unicode',
                                 pretty_print=pretty_print)
        return xml_str


class LibvirtConfigCPU(LibvirtConfigObject):

    def __init__(self, **kwargs):
        super(LibvirtConfigCPU, self).__init__(root_name='cpu',
                                               **kwargs)

        self.arch = None
        self.vendor = None
        self.model = None

        self.sockets = None
        self.cores = None
        self.threads = None

        self.features = set()

    def parse_dom(self, xmldoc):
        super(LibvirtConfigCPU, self).parse_dom(xmldoc)

        for c in xmldoc:
            if c.tag == "arch":
                self.arch = c.text
            elif c.tag == "model":
                self.model = c.text
            elif c.tag == "vendor":
                self.vendor = c.text
            elif c.tag == "topology":
                self.sockets = int(c.get("sockets"))
                self.cores = int(c.get("cores"))
                self.threads = int(c.get("threads"))
            # elif c.tag == "feature":
            #     f = LibvirtConfigCPUFeature()
            #     f.parse_dom(c)
            #     self.add_feature(f)

    def format_dom(self):
        cpu = super(LibvirtConfigCPU, self).format_dom()

        if self.arch is not None:
            cpu.append(self._text_node("arch", self.arch))
        if self.model is not None:
            cpu.append(self._text_node("model", self.model))
        if self.vendor is not None:
            cpu.append(self._text_node("vendor", self.vendor))

        if (self.sockets is not None and
            self.cores is not None and
                self.threads is not None):
            top = etree.Element("topology")
            top.set("sockets", str(self.sockets))
            top.set("cores", str(self.cores))
            top.set("threads", str(self.threads))
            cpu.append(top)

        # sorting the features to allow more predictable tests
        for f in sorted(self.features, key=lambda x: x.name):
            cpu.append(f.format_dom())

        return cpu

    def add_feature(self, feat):
        self.features.add(feat)


class LibvirtConfigGuestCPU(LibvirtConfigCPU):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestCPU, self).__init__(**kwargs)

        self.mode = None
        self.match = "exact"

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestCPU, self).parse_dom(xmldoc)
        self.mode = xmldoc.get('mode')
        self.match = xmldoc.get('match')

    def format_dom(self):
        cpu = super(LibvirtConfigGuestCPU, self).format_dom()

        if self.mode:
            cpu.set("mode", self.mode)
        if self.match:
            cpu.set("match", self.match)

        return cpu


class LibvirtConfigGuestTimer(LibvirtConfigObject):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestTimer, self).__init__(root_name="timer",
                                                      **kwargs)

        self.name = "platform"
        self.track = None
        self.tickpolicy = None
        self.present = None

    def format_dom(self):
        tm = super(LibvirtConfigGuestTimer, self).format_dom()

        tm.set("name", self.name)
        if self.track is not None:
            tm.set("track", self.track)
        if self.tickpolicy is not None:
            tm.set("tickpolicy", self.tickpolicy)
        if self.present is not None:
            if self.present:
                tm.set("present", "yes")
            else:
                tm.set("present", "no")

        return tm


class LibvirtConfigGuestClock(LibvirtConfigObject):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestClock, self).__init__(root_name="clock",
                                                      **kwargs)

        self.offset = "utc"
        self.adjustment = None
        self.timezone = None
        self.timers = []

    def format_dom(self):
        clk = super(LibvirtConfigGuestClock, self).format_dom()

        clk.set("offset", self.offset)
        if self.adjustment:
            clk.set("adjustment", self.adjustment)
        elif self.timezone:
            clk.set("timezone", self.timezone)

        for tm in self.timers:
            clk.append(tm.format_dom())

        return clk

    def add_timer(self, tm):
        self.timers.append(tm)


class LibvirtConfigGuestDevice(LibvirtConfigObject):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestDevice, self).__init__(**kwargs)


class LibvirtConfigGuestInterface(LibvirtConfigGuestDevice):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestInterface, self).__init__(
            root_name="interface",
            **kwargs)

        self.net_type = None
        self.target_dev = None
        self.model = None
        self.mac_addr = None
        self.script = None
        self.source_dev = None
        self.source_mode = "private"
        self.vporttype = None
        self.vportparams = []
        self.filtername = None
        self.filterparams = []
        self.driver_name = None
        self.driver_iommu = False
        self.vhostuser_mode = None
        self.vhostuser_path = None
        self.vhostuser_type = None
        self.vhost_queues = None
        self.vhost_rx_queue_size = None
        self.vhost_tx_queue_size = None
        self.vif_inbound_peak = None
        self.vif_inbound_burst = None
        self.vif_inbound_average = None
        self.vif_outbound_peak = None
        self.vif_outbound_burst = None
        self.vif_outbound_average = None
        self.vlan = None
        self.device_addr = None
        self.mtu = None

    def format_dom(self):
        dev = super(LibvirtConfigGuestInterface, self).format_dom()

        dev.set("type", self.net_type)
        if self.net_type == "hostdev":
            dev.set("managed", "yes")
        dev.append(etree.Element("mac", address=self.mac_addr))
        if self.model:
            dev.append(etree.Element("model", type=self.model))

        drv_elem = None
        if (self.driver_name or
                self.driver_iommu or
                self.net_type == "vhostuser"):

            drv_elem = etree.Element("driver")
            if self.driver_name and self.net_type != "vhostuser":
                # For vhostuser interface we should not set the driver name.
                drv_elem.set("name", self.driver_name)
            if self.driver_iommu:
                drv_elem.set("iommu", "on")

        if drv_elem is not None:
            if self.vhost_queues is not None:
                drv_elem.set('queues', str(self.vhost_queues))
            if self.vhost_rx_queue_size is not None:
                drv_elem.set('rx_queue_size', str(self.vhost_rx_queue_size))
            if self.vhost_tx_queue_size is not None:
                drv_elem.set('tx_queue_size', str(self.vhost_tx_queue_size))

            if (drv_elem.get('name') or drv_elem.get('queues') or
                drv_elem.get('rx_queue_size') or
                drv_elem.get('tx_queue_size') or
                drv_elem.get('iommu')):
                # Append the driver element into the dom only if name
                # or queues or tx/rx or iommu attributes are set.
                dev.append(drv_elem)

        if self.net_type == "ethernet":
            if self.script is not None:
                dev.append(etree.Element("script", path=self.script))
            if self.mtu is not None:
                dev.append(etree.Element("mtu", size=str(self.mtu)))
        elif self.net_type == "direct":
            dev.append(etree.Element("source", dev=self.source_dev,
                                     mode=self.source_mode))
        # elif self.net_type == "hostdev":
        #     source_elem = etree.Element("source")
        #     domain, bus, slot, func = \
        #         pci_utils.get_pci_address_fields(self.source_dev)
        #     addr_elem = etree.Element("address", type='pci')
        #     addr_elem.set("domain", "0x%s" % (domain))
        #     addr_elem.set("bus", "0x%s" % (bus))
        #     addr_elem.set("slot", "0x%s" % (slot))
        #     addr_elem.set("function", "0x%s" % (func))
        #     source_elem.append(addr_elem)
        #     dev.append(source_elem)
        # elif self.net_type == "vhostuser":
        #     dev.append(etree.Element("source", type=self.vhostuser_type,
        #                              mode=self.vhostuser_mode,
        #                              path=self.vhostuser_path))
        elif self.net_type == "bridge":
            dev.append(etree.Element("source", bridge=self.source_dev))
            if self.script is not None:
                dev.append(etree.Element("script", path=self.script))
            if self.mtu is not None:
                dev.append(etree.Element("mtu", size=str(self.mtu)))
        else:
            dev.append(etree.Element("source", bridge=self.source_dev))

        if self.vlan and self.net_type in ("direct", "hostdev"):
            vlan_elem = etree.Element("vlan")
            tag_elem = etree.Element("tag", id=str(self.vlan))
            vlan_elem.append(tag_elem)
            dev.append(vlan_elem)

        if self.target_dev is not None:
            dev.append(etree.Element("target", dev=self.target_dev))

        if self.vporttype is not None:
            vport = etree.Element("virtualport", type=self.vporttype)
            for p in self.vportparams:
                param = etree.Element("parameters")
                param.set(p['key'], p['value'])
                vport.append(param)
            dev.append(vport)

        if self.filtername is not None:
            filter = etree.Element("filterref", filter=self.filtername)
            for p in self.filterparams:
                filter.append(etree.Element("parameter",
                                            name=p['key'],
                                            value=p['value']))
            dev.append(filter)

        if self.vif_inbound_average or self.vif_outbound_average:
            bandwidth = etree.Element("bandwidth")
            if self.vif_inbound_average is not None:
                vif_inbound = etree.Element("inbound",
                average=str(self.vif_inbound_average))
                if self.vif_inbound_peak is not None:
                    vif_inbound.set("peak", str(self.vif_inbound_peak))
                if self.vif_inbound_burst is not None:
                    vif_inbound.set("burst", str(self.vif_inbound_burst))
                bandwidth.append(vif_inbound)

            if self.vif_outbound_average is not None:
                vif_outbound = etree.Element("outbound",
                average=str(self.vif_outbound_average))
                if self.vif_outbound_peak is not None:
                    vif_outbound.set("peak", str(self.vif_outbound_peak))
                if self.vif_outbound_burst is not None:
                    vif_outbound.set("burst", str(self.vif_outbound_burst))
                bandwidth.append(vif_outbound)
            dev.append(bandwidth)

        return dev

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestInterface, self).parse_dom(xmldoc)

        self.net_type = xmldoc.get('type')

        for c in xmldoc:
            if c.tag == 'mac':
                self.mac_addr = c.get('address')
            elif c.tag == 'model':
                self.model = c.get('type')
            elif c.tag == 'driver':
                self.driver_name = c.get('name')
                self.driver_iommu = (c.get('iommu', '') == 'on')
                self.vhost_queues = c.get('queues')
                self.vhost_rx_queue_size = c.get('rx_queue_size')
                self.vhost_tx_queue_size = c.get('tx_queue_size')
            elif c.tag == 'source':
                if self.net_type == 'direct':
                    self.source_dev = c.get('dev')
                    self.source_mode = c.get('mode', 'private')
                elif self.net_type == 'vhostuser':
                    self.vhostuser_type = c.get('type')
                    self.vhostuser_mode = c.get('mode')
                    self.vhostuser_path = c.get('path')
                # elif self.net_type == 'hostdev':
                #     for sub in c:
                #         if sub.tag == 'address' and sub.get('type') == 'pci':
                #             # strip the 0x prefix on each attribute since
                #             # format_dom puts them back on - note that
                #             # LibvirtConfigGuestHostdevPCI does not do this...
                #             self.source_dev = (
                #                 pci_utils.get_pci_address(
                #                     sub.get('domain')[2:],
                #                     sub.get('bus')[2:],
                #                     sub.get('slot')[2:],
                #                     sub.get('function')[2:]
                #                 )
                #             )
                else:
                    self.source_dev = c.get('bridge')
            elif c.tag == 'target':
                self.target_dev = c.get('dev')
            elif c.tag == 'script':
                self.script = c.get('path')
            elif c.tag == 'vlan':
                # NOTE(mriedem): The vlan element can have multiple tag
                # sub-elements but we're currently only storing a single tag
                # id in the vlan attribute.
                for sub in c:
                    if sub.tag == 'tag' and sub.get('id'):
                        self.vlan = int(sub.get('id'))
                        break
            elif c.tag == 'virtualport':
                self.vporttype = c.get('type')
                for sub in c:
                    if sub.tag == 'parameters':
                        for k, v in dict(sub.attrib).items():
                            self.add_vport_param(k, v)
            elif c.tag == 'filterref':
                self.filtername = c.get('filter')
                for sub in c:
                    if sub.tag == 'parameter':
                        self.add_filter_param(sub.get('name'),
                                              sub.get('value'))
            elif c.tag == 'bandwidth':
                for sub in c:
                    # Note that only average is mandatory, burst and peak are
                    # optional (and all are ints).
                    if sub.tag == 'inbound':
                        self.vif_inbound_average = int(sub.get('average'))
                        if sub.get('burst'):
                            self.vif_inbound_burst = int(sub.get('burst'))
                        if sub.get('peak'):
                            self.vif_inbound_peak = int(sub.get('peak'))
                    elif sub.tag == 'outbound':
                        self.vif_outbound_average = int(sub.get('average'))
                        if sub.get('burst'):
                            self.vif_outbound_burst = int(sub.get('burst'))
                        if sub.get('peak'):
                            self.vif_outbound_peak = int(sub.get('peak'))
            elif c.tag == 'address':
                obj = LibvirtConfigGuestDeviceAddress.parse_dom(c)
                self.device_addr = obj
            elif c.tag == 'mtu':
                self.mtu = int(c.get('size'))

    def add_filter_param(self, key, value):
        self.filterparams.append({'key': key, 'value': value})

    def add_vport_param(self, key, value):
        self.vportparams.append({'key': key, 'value': value})


class LibvirtConfigGuestDisk(LibvirtConfigGuestDevice):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestDisk, self).__init__(root_name="disk",
                                                     **kwargs)

        self.source_type = "file"
        self.source_device = "disk"
        self.driver_name = None
        self.driver_format = None
        self.driver_cache = None
        self.driver_discard = None
        self.driver_io = None
        self.driver_iommu = False
        self.source_path = None
        self.source_protocol = None
        self.source_name = None
        self.source_hosts = []
        self.source_ports = []
        self.target_dev = None
        self.target_path = None
        self.target_bus = None
        self.auth_username = None
        self.auth_secret_type = None
        self.auth_secret_uuid = None
        self.serial = None
        self.disk_read_bytes_sec = None
        self.disk_read_iops_sec = None
        self.disk_write_bytes_sec = None
        self.disk_write_iops_sec = None
        self.disk_total_bytes_sec = None
        self.disk_total_iops_sec = None
        self.disk_read_bytes_sec_max = None
        self.disk_write_bytes_sec_max = None
        self.disk_total_bytes_sec_max = None
        self.disk_read_iops_sec_max = None
        self.disk_write_iops_sec_max = None
        self.disk_total_iops_sec_max = None
        self.disk_size_iops_sec = None
        self.logical_block_size = None
        self.physical_block_size = None
        self.readonly = False
        self.shareable = False
        self.snapshot = None
        self.backing_store = None
        self.device_addr = None
        self.boot_order = None
        self.mirror = None
        self.encryption = None

    def _format_iotune(self, dev):
        iotune = etree.Element("iotune")

        if self.disk_read_bytes_sec is not None:
            iotune.append(self._text_node("read_bytes_sec",
                          self.disk_read_bytes_sec))

        if self.disk_read_iops_sec is not None:
            iotune.append(self._text_node("read_iops_sec",
                          self.disk_read_iops_sec))

        if self.disk_write_bytes_sec is not None:
            iotune.append(self._text_node("write_bytes_sec",
                          self.disk_write_bytes_sec))

        if self.disk_write_iops_sec is not None:
            iotune.append(self._text_node("write_iops_sec",
                          self.disk_write_iops_sec))

        if self.disk_total_bytes_sec is not None:
            iotune.append(self._text_node("total_bytes_sec",
                          self.disk_total_bytes_sec))

        if self.disk_total_iops_sec is not None:
            iotune.append(self._text_node("total_iops_sec",
                          self.disk_total_iops_sec))

        if self.disk_read_bytes_sec_max is not None:
            iotune.append(self._text_node("read_bytes_sec_max",
                          self.disk_read_bytes_sec_max))

        if self.disk_write_bytes_sec_max is not None:
            iotune.append(self._text_node("write_bytes_sec_max",
                          self.disk_write_bytes_sec_max))

        if self.disk_total_bytes_sec_max is not None:
            iotune.append(self._text_node("total_bytes_sec_max",
                          self.disk_total_bytes_sec_max))

        if self.disk_read_iops_sec_max is not None:
            iotune.append(self._text_node("read_iops_sec_max",
                          self.disk_read_iops_sec_max))

        if self.disk_write_iops_sec_max is not None:
            iotune.append(self._text_node("write_iops_sec_max",
                          self.disk_write_iops_sec_max))

        if self.disk_total_iops_sec_max is not None:
            iotune.append(self._text_node("total_iops_sec_max",
                          self.disk_total_iops_sec_max))

        if self.disk_size_iops_sec is not None:
            iotune.append(self._text_node("size_iops_sec",
                          self.disk_size_iops_sec))

        if len(iotune) > 0:
            dev.append(iotune)

    def format_dom(self):
        dev = super(LibvirtConfigGuestDisk, self).format_dom()

        dev.set("type", self.source_type)
        dev.set("device", self.source_device)
        if any((self.driver_name, self.driver_format, self.driver_cache,
                self.driver_discard, self.driver_iommu)):
            drv = etree.Element("driver")
            if self.driver_name is not None:
                drv.set("name", self.driver_name)
            if self.driver_format is not None:
                drv.set("type", self.driver_format)
            if self.driver_cache is not None:
                drv.set("cache", self.driver_cache)
            if self.driver_discard is not None:
                drv.set("discard", self.driver_discard)
            if self.driver_io is not None:
                drv.set("io", self.driver_io)
            if self.driver_iommu:
                drv.set("iommu", "on")
            dev.append(drv)

        if self.source_type == "file" and self.source_path:
            dev.append(etree.Element("source", file=self.source_path))
        elif self.source_type == "block":
            dev.append(etree.Element("source", dev=self.source_path))
        elif self.source_type == "mount":
            dev.append(etree.Element("source", dir=self.source_path))
        elif self.source_type == "network" and self.source_protocol:
            source = etree.Element("source", protocol=self.source_protocol)
            if self.source_name is not None:
                source.set('name', self.source_name)
            hosts_info = zip(self.source_hosts, self.source_ports)
            for name, port in hosts_info:
                host = etree.Element('host', name=name)
                if port is not None:
                    host.set('port', port)
                source.append(host)
            dev.append(source)

        if self.auth_secret_type is not None:
            auth = etree.Element("auth")
            auth.set("username", self.auth_username)
            auth.append(etree.Element("secret", type=self.auth_secret_type,
                                      uuid=self.auth_secret_uuid))
            dev.append(auth)

        if self.source_type == "mount":
            dev.append(etree.Element("target", dir=self.target_path))
        else:
            dev.append(etree.Element("target", dev=self.target_dev,
                                     bus=self.target_bus))

        if self.serial is not None:
            dev.append(self._text_node("serial", self.serial))

        self._format_iotune(dev)

        # Block size tuning
        if (self.logical_block_size is not None or
                self.physical_block_size is not None):

            blockio = etree.Element("blockio")
            if self.logical_block_size is not None:
                blockio.set('logical_block_size', self.logical_block_size)

            if self.physical_block_size is not None:
                blockio.set('physical_block_size', self.physical_block_size)

            dev.append(blockio)

        if self.readonly:
            dev.append(etree.Element("readonly"))
        if self.shareable:
            dev.append(etree.Element("shareable"))

        if self.boot_order:
            dev.append(etree.Element("boot", order=self.boot_order))

        if self.device_addr:
            dev.append(self.device_addr.format_dom())

        if self.encryption:
            dev.append(self.encryption.format_dom())

        return dev

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestDisk, self).parse_dom(xmldoc)
        self.source_type = xmldoc.get('type')
        self.source_device = xmldoc.get('device')
        self.snapshot = xmldoc.get('snapshot')

        for c in xmldoc:
            if c.tag == 'driver':
                self.driver_name = c.get('name')
                self.driver_format = c.get('type')
                self.driver_cache = c.get('cache')
                self.driver_discard = c.get('discard')
                self.driver_io = c.get('io')
                self.driver_iommu = c.get('iommu', '') == "on"
            elif c.tag == 'source':
                if self.source_type == 'file':
                    self.source_path = c.get('file')
                elif self.source_type == 'block':
                    self.source_path = c.get('dev')
                elif self.source_type == 'mount':
                    self.source_path = c.get('dir')
                elif self.source_type == 'network':
                    self.source_protocol = c.get('protocol')
                    self.source_name = c.get('name')
                    for sub in c:
                        if sub.tag == 'host':
                            self.source_hosts.append(sub.get('name'))
                            self.source_ports.append(sub.get('port'))

            elif c.tag == 'serial':
                self.serial = c.text
            elif c.tag == 'target':
                if self.source_type == 'mount':
                    self.target_path = c.get('dir')
                else:
                    self.target_dev = c.get('dev')

                self.target_bus = c.get('bus', None)
            elif c.tag == 'backingStore':
                b = LibvirtConfigGuestDiskBackingStore()
                b.parse_dom(c)
                self.backing_store = b
            elif c.tag == 'readonly':
                self.readonly = True
            elif c.tag == 'shareable':
                self.shareable = True
            elif c.tag == 'address':
                obj = LibvirtConfigGuestDeviceAddress.parse_dom(c)
                self.device_addr = obj
            elif c.tag == 'boot':
                self.boot_order = c.get('order')
            # elif c.tag == 'mirror':
            #     m = LibvirtConfigGuestDiskMirror()
            #     m.parse_dom(c)
            #     self.mirror = m
            # elif c.tag == 'encryption':
            #     e = LibvirtConfigGuestDiskEncryption()
            #     e.parse_dom(c)
            #     self.encryption = e


class LibvirtConfigGuestDiskBackingStore(LibvirtConfigObject):
    def __init__(self, **kwargs):
        super(LibvirtConfigGuestDiskBackingStore, self).__init__(
            root_name="backingStore", **kwargs)

        self.index = None
        self.source_type = None
        self.source_file = None
        self.source_protocol = None
        self.source_name = None
        self.source_hosts = []
        self.source_ports = []
        self.driver_name = None
        self.driver_format = None
        self.backing_store = None

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestDiskBackingStore, self).parse_dom(xmldoc)

        self.source_type = xmldoc.get('type')
        self.index = xmldoc.get('index')

        for c in xmldoc:
            if c.tag == 'driver':
                self.driver_name = c.get('name')
                self.driver_format = c.get('type')
            elif c.tag == 'source':
                self.source_file = c.get('file')
                self.source_protocol = c.get('protocol')
                self.source_name = c.get('name')
                for d in c:
                    if d.tag == 'host':
                        self.source_hosts.append(d.get('name'))
                        self.source_ports.append(d.get('port'))
            elif c.tag == 'backingStore':
                if len(c):
                    self.backing_store = LibvirtConfigGuestDiskBackingStore()
                    self.backing_store.parse_dom(c)


class LibvirtConfigGuestDeviceAddress(LibvirtConfigObject):
    def __init__(self, type=None, **kwargs):
        super(LibvirtConfigGuestDeviceAddress, self).__init__(
            root_name='address', **kwargs)
        self.type = type

    def format_dom(self):
        xml = super(LibvirtConfigGuestDeviceAddress, self).format_dom()
        xml.set("type", self.type)
        return xml

    @staticmethod
    def parse_dom(xmldoc):
        addr_type = xmldoc.get('type')
        if addr_type == 'pci':
            obj = LibvirtConfigGuestDeviceAddressPCI()
        elif addr_type == 'drive':
            obj = LibvirtConfigGuestDeviceAddressDrive()
        else:
            return None
        obj.parse_dom(xmldoc)
        return obj


class LibvirtConfigGuestDeviceAddressPCI(LibvirtConfigGuestDeviceAddress):
    def __init__(self, **kwargs):
        super(LibvirtConfigGuestDeviceAddressPCI, self).\
                __init__(type='pci', **kwargs)
        self.domain = None
        self.bus = None
        self.slot = None
        self.function = None

    def format_dom(self):
        xml = super(LibvirtConfigGuestDeviceAddressPCI, self).format_dom()

        if self.domain is not None:
            xml.set("domain", str(self.domain))
        if self.bus is not None:
            xml.set("bus", str(self.bus))
        if self.slot is not None:
            xml.set("slot", str(self.slot))
        if self.function is not None:
            xml.set("function", str(self.function))

        return xml

    def parse_dom(self, xmldoc):
        self.domain = xmldoc.get('domain')
        self.bus = xmldoc.get('bus')
        self.slot = xmldoc.get('slot')
        self.function = xmldoc.get('function')

    def format_address(self):
        if self.domain is not None:
            return '%s:%s:%s.%s' % (self.domain[2:], self.bus[2:], self.slot[2:], self.function[2:])


class LibvirtConfigGuestDeviceAddressDrive(LibvirtConfigGuestDeviceAddress):
    def __init__(self, **kwargs):
        super(LibvirtConfigGuestDeviceAddressDrive, self).\
                __init__(type='drive', **kwargs)
        self.controller = None
        self.bus = None
        self.target = None
        self.unit = None

    def format_dom(self):
        xml = super(LibvirtConfigGuestDeviceAddressDrive, self).format_dom()

        if self.controller is not None:
            xml.set("controller", str(self.controller))
        if self.bus is not None:
            xml.set("bus", str(self.bus))
        if self.target is not None:
            xml.set("target", str(self.target))
        if self.unit is not None:
            xml.set("unit", str(self.unit))

        return xml

    def parse_dom(self, xmldoc):
        self.controller = xmldoc.get('controller')
        self.bus = xmldoc.get('bus')
        self.target = xmldoc.get('target')
        self.unit = xmldoc.get('unit')

    def format_address(self):
        return None


class LibvirtConfigGuestCharDeviceLog(LibvirtConfigObject):
    """Represents a sub-element to a character device."""

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestCharDeviceLog, self).__init__(root_name="log",
                                                              **kwargs)
        self.file = None
        self.append = "off"

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestCharDeviceLog, self).parse_dom(xmldoc)
        self.file = xmldoc.get("file")
        self.append = xmldoc.get("append")

    def format_dom(self):
        log = super(LibvirtConfigGuestCharDeviceLog, self).format_dom()
        log.set("file", self.file)
        log.set("append", self.append)
        return log


class LibvirtConfigGuestCharBase(LibvirtConfigGuestDevice):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestCharBase, self).__init__(**kwargs)

        self.type = "pty"
        self.source_path = None
        self.listen_port = None
        self.listen_host = None
        self.log = None

    def format_dom(self):
        dev = super(LibvirtConfigGuestCharBase, self).format_dom()

        dev.set("type", self.type)

        if self.type == "file":
            dev.append(etree.Element("source", path=self.source_path))
        elif self.type == "unix":
            dev.append(etree.Element("source", mode="bind",
                                    path=self.source_path))
        elif self.type == "tcp":
            dev.append(etree.Element("source", mode="bind",
                                     host=self.listen_host,
                                     service=str(self.listen_port)))

        if self.log:
            dev.append(self.log.format_dom())

        return dev


class LibvirtConfigGuestChar(LibvirtConfigGuestCharBase):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestChar, self).__init__(**kwargs)

        self.target_port = None
        self.target_type = None

    def format_dom(self):
        dev = super(LibvirtConfigGuestChar, self).format_dom()

        if self.target_port is not None or self.target_type is not None:
            target = etree.Element("target")
            if self.target_port is not None:
                target.set("port", str(self.target_port))
            if self.target_type is not None:
                target.set("type", self.target_type)
            dev.append(target)

        return dev


class LibvirtConfigGuestSerial(LibvirtConfigGuestChar):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestSerial, self).__init__(root_name="serial",
                                                       **kwargs)


class LibvirtConfigGuestChannel(LibvirtConfigGuestCharBase):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestChannel, self).__init__(root_name="channel",
                                                        **kwargs)

        self.target_type = "virtio"
        self.target_name = None

    def format_dom(self):
        dev = super(LibvirtConfigGuestChannel, self).format_dom()

        target = etree.Element("target", type=self.target_type)
        if self.target_name is not None:
            target.set("name", self.target_name)
        dev.append(target)

        return dev

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestChannel, self).parse_dom(xmldoc)

        self.type = xmldoc.get('type')
        for c in xmldoc:
            if c.tag == 'target':
                self.target_type = c.get('type')
                self.target_name = c.get('name')


class LibvirtConfigGuestInput(LibvirtConfigGuestDevice):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestInput, self).__init__(root_name="input",
                                                      **kwargs)

        self.type = "tablet"
        self.bus = "usb"
        self.driver_iommu = False

    def format_dom(self):
        dev = super(LibvirtConfigGuestInput, self).format_dom()

        dev.set("type", self.type)
        dev.set("bus", self.bus)
        if self.driver_iommu:
            dev.append(etree.Element('driver', iommu="on"))

        return dev

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestInput, self).parse_dom(xmldoc)

        self.type = xmldoc.get('type')
        self.bus = xmldoc.get('bus')


class LibvirtConfigGuestRedirect(LibvirtConfigGuestDevice):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestRedirect, self).__init__(root_name="redirdev", **kwargs)

        self.type = "spicevmc"

    def format_dom(self):
        dev = super(LibvirtConfigGuestRedirect, self).format_dom()

        dev.set("type", self.type)

        return dev

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestRedirect, self).parse_dom(xmldoc)

        self.type = xmldoc.get('type')


class LibvirtConfigGuestGraphics(LibvirtConfigGuestDevice):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestGraphics, self).__init__(root_name="graphics",
                                                         **kwargs)

        self.type = "vnc"
        self.autoport = True
        self.keymap = None
        self.listen = None
        self.port = None
        self.passwd = None
        self.image_compression = None
        self.jpeg_compression = None
        self.zlib_compression = None
        self.stream_mode = None
        self.clipboard = None
        self.mouse_mode = None

    def format_dom(self):
        dev = super(LibvirtConfigGuestGraphics, self).format_dom()
        dev.set("type", self.type)
        if self.autoport:
            dev.set("autoport", "yes")
        else:
            dev.set("autoport", "no")
        if self.keymap:
            dev.set("keymap", self.keymap)
        if self.listen:
            dev.set("listen", self.listen)
        if self.passwd:
            dev.set("passwd", self.passwd)
        if self.image_compression:
            dev.append(etree.Element("image", compression=self.image_compression))
        if self.jpeg_compression:
            dev.append(etree.Element("jpeg", compression=self.jpeg_compression))
        if self.zlib_compression:
            dev.append(etree.Element("zlib", compression=self.zlib_compression))
        if self.stream_mode:
            dev.append(etree.Element("streaming", mode=self.stream_mode))
        if self.clipboard:
            dev.append(etree.Element("clipboard", copypaste=self.clipboard))
        if self.mouse_mode:
            dev.append(etree.Element("mouse", mode=self.mouse_mode))

        return dev

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestGraphics, self).parse_dom(xmldoc)

        self.type = xmldoc.get('type')
        self.keymap = xmldoc.get('keymap')
        self.listen = xmldoc.get('listen')
        self.port = xmldoc.get('port')
        self.passwd = xmldoc.get('passwd')


class LibvirtConfigGuestVideo(LibvirtConfigGuestDevice):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestVideo, self).__init__(root_name="video",
                                                      **kwargs)

        self.type = 'cirrus'
        self.vram = None
        self.heads = None
        self.driver_iommu = False

    def format_dom(self):
        dev = super(LibvirtConfigGuestVideo, self).format_dom()

        model = etree.Element("model")
        model.set("type", self.type)

        if self.vram:
            model.set("vram", str(self.vram))

        if self.heads:
            model.set("heads", str(self.heads))

        dev.append(model)

        if self.driver_iommu:
            dev.append(etree.Element("driver", iommu="on"))

        return dev

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestVideo, self).parse_dom(xmldoc)
        for c in xmldoc:
            if c.tag == 'model':
                self.type = c.get('type')


class LibvirtConfigGuestSound(LibvirtConfigGuestDevice):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestSound, self).__init__(root_name="sound",
                                                      **kwargs)

        self.model = 'ich6'

    def format_dom(self):
        dev = super(LibvirtConfigGuestSound, self).format_dom()
        dev.set("model", self.model)

        return dev

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestSound, self).parse_dom(xmldoc)
        self.model = xmldoc.get('model')


class LibvirtConfigMemoryBalloon(LibvirtConfigGuestDevice):
    def __init__(self, **kwargs):
        super(LibvirtConfigMemoryBalloon, self).__init__(
            root_name='memballoon',
            **kwargs)
        self.model = None
        self.period = None
        self.driver_iommu = False

    def format_dom(self):
        dev = super(LibvirtConfigMemoryBalloon, self).format_dom()
        dev.set('model', str(self.model))
        if self.period is not None:
            dev.append(etree.Element('stats', period=str(self.period)))
        if self.driver_iommu:
            dev.append(etree.Element('driver', iommu='on'))
        return dev

    def parse_dom(self, xmldoc):
        super(LibvirtConfigMemoryBalloon, self).parse_dom(xmldoc)
        self.model = xmldoc.get('model')
        for c in xmldoc:
            if c.tag == 'stats':
                self.period = c.get('period', 10)


class LibvirtConfigGuestSMBIOS(LibvirtConfigObject):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestSMBIOS, self).__init__(root_name="smbios",
                                                       **kwargs)

        self.mode = "sysinfo"

    def format_dom(self):
        smbios = super(LibvirtConfigGuestSMBIOS, self).format_dom()
        smbios.set("mode", self.mode)

        return smbios

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestSMBIOS, self).parse_dom(xmldoc)
        self.model = xmldoc.get('model', 'sysinfo')


class LibvirtConfigGuestFeature(LibvirtConfigObject):

    def __init__(self, name, **kwargs):
        super(LibvirtConfigGuestFeature, self).__init__(root_name=name,
                                                        **kwargs)


class LibvirtConfigGuestFeatureACPI(LibvirtConfigGuestFeature):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestFeatureACPI, self).__init__("acpi",
                                                            **kwargs)


class LibvirtConfigGuestFeatureAPIC(LibvirtConfigGuestFeature):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestFeatureAPIC, self).__init__("apic",
                                                            **kwargs)


class LibvirtConfigGuestFeatureVmport(LibvirtConfigGuestFeature):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestFeatureVmport, self).__init__("vmport", **kwargs)
        self.state = "off"

    def format_dom(self):
        root = super(LibvirtConfigGuestFeatureVmport, self).format_dom()

        root.set("state", self.state)
        return root


class LibvirtConfigGuestFeatureHyperV(LibvirtConfigGuestFeature):

    # QEMU requires at least this value to be set
    MIN_SPINLOCK_RETRIES = 4095
    # The spoofed vendor_id can be any alphanumeric string
    SPOOFED_VENDOR_ID = "1234567890ab"

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestFeatureHyperV, self).__init__("hyperv",
                                                              **kwargs)

        self.relaxed = False
        self.vapic = False
        self.spinlocks = False
        self.spinlock_retries = self.MIN_SPINLOCK_RETRIES
        self.vendorid_spoof = False
        self.vendorid = self.SPOOFED_VENDOR_ID

    def format_dom(self):
        root = super(LibvirtConfigGuestFeatureHyperV, self).format_dom()

        if self.relaxed:
            root.append(etree.Element("relaxed", state="on"))
        if self.vapic:
            root.append(etree.Element("vapic", state="on"))
        if self.spinlocks:
            root.append(etree.Element("spinlocks", state="on",
                                      retries=str(self.spinlock_retries)))
        if self.vendorid_spoof:
            root.append(etree.Element("vendor_id", state="on",
                                      value=self.vendorid))

        return root


class LibvirtConfigGuestSysinfo(LibvirtConfigObject):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuestSysinfo, self).__init__(root_name="sysinfo",
                                                        **kwargs)

        self.type = "smbios"
        self.bios_vendor = None
        self.bios_version = None
        self.system_manufacturer = None
        self.system_product = None
        self.system_version = None
        self.system_serial = None
        self.system_uuid = None
        self.system_family = None

    def format_dom(self):
        sysinfo = super(LibvirtConfigGuestSysinfo, self).format_dom()

        sysinfo.set("type", self.type)

        bios = etree.Element("bios")
        system = etree.Element("system")

        if self.bios_vendor is not None:
            bios.append(self._text_node("entry", self.bios_vendor,
                                        name="vendor"))

        if self.bios_version is not None:
            bios.append(self._text_node("entry", self.bios_version,
                                        name="version"))

        if self.system_manufacturer is not None:
            system.append(self._text_node("entry", self.system_manufacturer,
                                          name="manufacturer"))

        if self.system_product is not None:
            system.append(self._text_node("entry", self.system_product,
                                          name="product"))

        if self.system_version is not None:
            system.append(self._text_node("entry", self.system_version,
                                          name="version"))

        if self.system_serial is not None:
            system.append(self._text_node("entry", self.system_serial,
                                          name="serial"))

        if self.system_uuid is not None:
            system.append(self._text_node("entry", self.system_uuid,
                                          name="uuid"))

        if self.system_family is not None:
            system.append(self._text_node("entry", self.system_family,
                                          name="family"))

        if len(list(bios)) > 0:
            sysinfo.append(bios)

        if len(list(system)) > 0:
            sysinfo.append(system)

        return sysinfo

    def parse_dom(self, xmldoc):
        super(LibvirtConfigGuestSysinfo, self).parse_dom(xmldoc)
        self.type = xmldoc.get('type', 'smbios')
        for c in xmldoc:
            for d in c:
                if d.tag == 'entry':
                    if 'manufacturer' == d.get('name'):
                        self.system_manufacturer = d.text
                    elif 'product' == d.get('name'):
                        self.system_product = d.text
                    elif 'version' == d.get('name'):
                        self.system_version = d.text
                    elif 'serial' == d.get('name'):
                        self.system_serial = d.text
                    elif 'uuid' == d.get('name'):
                        self.system_uuid = d.text
                    elif 'family' == d.get('name'):
                        self.system_family = d.text


# class LibvirtConfigCommandLine(LibvirtConfigObject):
#
#     def __init__(self, **kwargs):
#         super(LibvirtConfigCommandLine, self).__init__(root_name="qemu:commandline", **kwargs)
#
#         self.env_name = "LD_LIBRARY_PATH"
#         self.env_value = None
#
#     def format_dom(self):
#         root = super(LibvirtConfigCommandLine, self).format_dom()
#         if self.env_value:
#             root.append(etree.Element("qemu:env", name=self.env_name, value=self.env_value))
#             # root.set("value", self.env_value)
#         return root


class LibvirtConfigGuest(LibvirtConfigObject):

    def __init__(self, **kwargs):
        super(LibvirtConfigGuest, self).__init__(root_name="domain", **kwargs)

        self.virt_type = None
        self.ns_uri = "http://libvirt.org/schemas/domain/qemu/1.0"
        self.ns_prefix = "qemu"
        self.uuid = None
        self.name = None
        self.memory = 500 * Mi
        self.max_memory_size = None
        self.max_memory_slots = 0
        self.membacking = None
        self.memtune = None
        self.numatune = None
        self.vcpus = 1
        self.cpuset = None
        self.cpu = None
        self.cputune = None
        self.features = []
        self.clock = None
        self.sysinfo = None
        self.os_type = None
        self.os_loader = None
        self.os_loader_type = None
        self.nvram = None
        self.os_kernel = None
        self.os_initrd = None
        self.os_cmdline = None
        self.os_root = None
        self.os_init_path = None
        self.os_boot_dev = []
        self.os_smbios = None
        self.os_mach_type = None
        self.os_bootmenu = False
        self.devices = []
        self.metadata = []
        self.commandline = []

    def _format_basic_props(self, root):
        root.append(self._text_node("uuid", self.uuid))
        root.append(self._text_node("name", self.name))
        root.append(self._text_node("memory", self.memory))
        if self.max_memory_size is not None:
            max_memory = self._text_node("maxMemory", self.max_memory_size)
            max_memory.set("slots", str(self.max_memory_slots))
            root.append(max_memory)
        if self.membacking is not None:
            root.append(self.membacking.format_dom())
        if self.memtune is not None:
            root.append(self.memtune.format_dom())
        if self.numatune is not None:
            root.append(self.numatune.format_dom())
        if self.cpuset is not None:
            vcpu = self._text_node("vcpu", self.vcpus)
            vcpu.set("cpuset", self.cpuset)
            root.append(vcpu)
        else:
            vcpu = self._text_node("vcpu", self.vcpus)
            vcpu.set("placement", "auto")
            root.append(vcpu)

        if len(self.metadata) > 0:
            metadata = etree.Element("metadata")
            for m in self.metadata:
                metadata.append(m.format_dom())
            root.append(metadata)

    def _format_os(self, root):
        os = etree.Element("os")
        type_node = self._text_node("type", self.os_type)
        if self.os_mach_type is not None:
            type_node.set("machine", self.os_mach_type)
        os.append(type_node)
        if self.os_kernel is not None:
            os.append(self._text_node("kernel", self.os_kernel))
        if self.os_loader is not None:
            # Generate XML nodes for UEFI boot.
            if self.os_loader_type == "pflash":
                loader = self._text_node("loader", self.os_loader)
                loader.set("type", "pflash")
                loader.set("readonly", "yes")
                os.append(loader)
            else:
                os.append(self._text_node("loader", self.os_loader))
        if self.nvram is not None:
            os.append(self._text_node("nvram", self.nvram))
        if self.os_initrd is not None:
            os.append(self._text_node("initrd", self.os_initrd))
        if self.os_cmdline is not None:
            os.append(self._text_node("cmdline", self.os_cmdline))
        if self.os_root is not None:
            os.append(self._text_node("root", self.os_root))
        if self.os_init_path is not None:
            os.append(self._text_node("init", self.os_init_path))

        for boot_dev in self.os_boot_dev:
            os.append(etree.Element("boot", dev=boot_dev))

        if self.os_smbios is not None:
            os.append(self.os_smbios.format_dom())

        if self.os_bootmenu:
            os.append(etree.Element("bootmenu", enable="yes"))
        root.append(os)

    def _format_features(self, root):
        if len(self.features) > 0:
            features = etree.Element("features")
            for feat in self.features:
                features.append(feat.format_dom())
            root.append(features)

    def _format_devices(self, root):
        if len(self.devices) == 0:
            return
        devices = etree.Element("devices")
        for dev in self.devices:
            devices.append(dev.format_dom())
        root.append(devices)

    def _format_commandline(self, root):
        commandline = etree.Element("{" + self.ns_uri + "}commandline")
        qemu_attr = list()
        attr = etree.Element("{" + self.ns_uri + "}env")
        attr.set("name", "LD_LIBRARY_PATH")
        attr.set("value", "/usr/local/libexec")
        qemu_attr.append(attr)
        for attr in qemu_attr:
            commandline.append(attr)
        root.append(commandline)

    def format_dom(self):
        root = super(LibvirtConfigGuest, self).format_dom()
        # root = etree.Element("domain", nsmap={'qemu': 'http://libvirt.org/schemas/domain/qemu/1.0'})
        root.set("type", self.virt_type)

        self._format_basic_props(root)

        if self.sysinfo is not None:
            root.append(self.sysinfo.format_dom())

        self._format_os(root)
        self._format_features(root)

        if self.cputune is not None:
            root.append(self.cputune.format_dom())

        if self.clock is not None:
            root.append(self.clock.format_dom())

        if self.cpu is not None:
            root.append(self.cpu.format_dom())

        self._format_devices(root)
        self._format_commandline(root)
        return root

    def _parse_basic_props(self, xmldoc):
        # memmbacking, memtune, numatune, metadata are skipped just because
        # corresponding config types do not implement parse_dom method
        if xmldoc.tag == 'uuid':
            self.uuid = xmldoc.text
        elif xmldoc.tag == 'name':
            self.name = xmldoc.text
        elif xmldoc.tag == 'memory':
            self.memory = int(xmldoc.text)
        elif xmldoc.tag == 'vcpu':
            self.vcpus = int(xmldoc.text)
            # if xmldoc.get('cpuset') is not None:
            #     self.cpuset = hardware.parse_cpu_spec(xmldoc.get('cpuset'))

    def _parse_os(self, xmldoc):
        for c in xmldoc:
            if c.tag == 'type':
                self.os_type = c.text
                self.os_mach_type = c.get('machine')
            elif c.tag == 'kernel':
                self.os_kernel = c.text
            elif c.tag == 'smbios':
                self.os_smbios = LibvirtConfigGuestSMBIOS()
            elif c.tag == 'loader':
                self.os_loader = c.text
                if c.get('type') == 'pflash':
                    self.os_loader_type = 'pflash'
            elif c.tag == 'initrd':
                self.os_initrd = c.text
            elif c.tag == 'cmdline':
                self.os_cmdline = c.text
            elif c.tag == 'root':
                self.os_root = c.text
            elif c.tag == 'init':
                self.os_init_path = c.text
            elif c.tag == 'boot':
                self.os_boot_dev.append(c.get('dev'))
            elif c.tag == 'bootmenu':
                if c.get('enable') == 'yes':
                    self.os_bootmenu = True

    def _parse_features(self, xmldoc):
        for c in xmldoc:
            if c.tag == 'acpi':
                self.features.append(LibvirtConfigGuestFeatureACPI())
            elif c.tag == 'apic':
                self.features.append(LibvirtConfigGuestFeatureAPIC())
            elif c.tag == 'hyperv':
                hv = LibvirtConfigGuestFeatureHyperV()
                for d in c:
                    if d.tag == 'relaxed':
                        if 'on' == d.get('state', 'off'):
                            hv.relaxed = True
                        else:
                            hv.relaxed = False
                    if d.tag == 'vapic':
                        if 'on' == d.get('state', 'off'):
                            hv.vapic = True
                        else:
                            hv.vapic = False
                    if d.tag == 'spinlocks':
                        if 'on' == d.get('state', 'off'):
                            hv.spinlocks = True
                        else:
                            hv.spinlocks = False
                        hv.spinlock_retries = d.get('retries', 8191)
                self.features.append(hv)

    def _parse_clock(self, xmldoc):
        clk = LibvirtConfigGuestClock()
        clk.offset = xmldoc.get('offset', 'utc')
        for c in xmldoc:
            if c.tag == 'timer':
                ti = LibvirtConfigGuestTimer()
                ti.name = c.get('name')
                if c.get('tickpolicy'):
                    ti.tickpolicy = c.get('tickpolicy')
                if c.get('present'):
                    ti.present = c.get('present')
                clk.add_timer(ti)
        self.clock = clk

    def parse_dom(self, xmldoc):
        self.virt_type = xmldoc.get('type')
        for c in xmldoc:
            if c.tag == 'devices':
                for d in c:
                    if d.tag == 'disk':
                        obj = LibvirtConfigGuestDisk()
                        obj.parse_dom(d)
                        self.devices.append(obj)
                    elif d.tag == 'graphics':
                        obj = LibvirtConfigGuestGraphics()
                        obj.parse_dom(d)
                        self.devices.append(obj)
                    elif d.tag == 'input':
                        obj = LibvirtConfigGuestInput()
                        obj.parse_dom(d)
                        self.devices.append(obj)
                    elif d.tag == 'redirdev':
                        obj = LibvirtConfigGuestRedirect()
                        obj.parse_dom(d)
                        self.devices.append(obj)
                    elif d.tag == 'channel':
                        obj = LibvirtConfigGuestChannel()
                        obj.parse_dom(d)
                        self.devices.append(obj)
                    elif d.tag == 'graphic':
                        obj = LibvirtConfigGuestGraphics()
                        obj.parse_dom(d)
                        self.devices.append(obj)
                    elif d.tag == 'video':
                        obj = LibvirtConfigGuestVideo()
                        obj.parse_dom(d)
                        self.devices.append(obj)
                    elif d.tag == 'sound':
                        obj = LibvirtConfigGuestSound()
                        obj.parse_dom(d)
                        self.devices.append(obj)
                    elif d.tag == 'memballoon':
                        obj = LibvirtConfigMemoryBalloon()
                        obj.parse_dom(d)
                        self.devices.append(obj)
                    # elif d.tag == 'filesystem':
                    #     obj = LibvirtConfigGuestFilesys()
                    #     obj.parse_dom(d)
                    #     self.devices.append(obj)
                    # elif d.tag == 'hostdev' and d.get('type') == 'pci':
                    #     obj = LibvirtConfigGuestHostdevPCI()
                    #     obj.parse_dom(d)
                    #     self.devices.append(obj)
                    # elif d.tag == 'hostdev' and d.get('type') == 'mdev':
                    #     obj = LibvirtConfigGuestHostdevMDEV()
                    #     obj.parse_dom(d)
                    #     self.devices.append(obj)
                    elif d.tag == 'interface':
                        obj = LibvirtConfigGuestInterface()
                        obj.parse_dom(d)
                        self.devices.append(obj)
                    # elif d.tag == 'memory' and d.get('model') == 'nvdimm':
                    #     obj = LibvirtConfigGuestVPMEM()
                    #     obj.parse_dom(d)
                    #     self.devices.append(obj)
            elif c.tag == 'sysinfo':
                obj = LibvirtConfigGuestSysinfo()
                obj.parse_dom(c)
                self.sysinfo = obj
            elif c.tag == 'features':
                self._parse_features(c)
            elif c.tag == 'clock':
                self._parse_clock(c)
            elif c.tag == 'cpu':
                obj = LibvirtConfigGuestCPU()
                obj.parse_dom(c)
                self.cpu = obj
            elif c.tag == 'os':
                self._parse_os(c)
            else:
                self._parse_basic_props(c)

    def add_device(self, dev):
        self.devices.append(dev)

    def set_clock(self, clk):
        self.clock = clk
