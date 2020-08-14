import os
import logging
from yzy_compute.network import ip_lib
from yzy_compute import exception

# NOTE(toabctl): Don't use /sys/devices/virtual/net here because not all tap
# devices are listed here (i.e. when using Xen)
BRIDGE_FS = "/sys/class/net/"
BRIDGE_INTERFACE_FS = BRIDGE_FS + "%(bridge)s/brif/%(interface)s"
BRIDGE_INTERFACES_FS = BRIDGE_FS + "%s/brif/"
BRIDGE_PORT_FS_FOR_DEVICE = BRIDGE_FS + "%s/brport"
BRIDGE_PATH_FOR_DEVICE = BRIDGE_PORT_FS_FOR_DEVICE + '/bridge'


class BridgeDevice(ip_lib.IPDevice):

    def _ip_link(self, cmd):
        cmd = ['ip', 'link'] + cmd
        ip_wrapper = ip_lib.IPWrapper(self.namespace)
        logging.info("execute cmd:%s", cmd)
        return ip_wrapper.netns.execute(cmd, run_as_root=True)

    @classmethod
    def addbr(cls, name, namespace=None):
        bridge = cls(name, namespace, 'bridge')
        try:
            bridge.link.create()
        except RuntimeError:
            raise
        return bridge

    @classmethod
    def get_interface_bridge(cls, interface):
        try:
            path = os.readlink(BRIDGE_PATH_FOR_DEVICE % interface)
        except OSError:
            return None
        else:
            name = path.rpartition('/')[-1]
            return cls(name)

    def delbr(self):
        return self.link.delete()

    def addif(self, interface):
        return self._ip_link(['set', 'dev', interface, 'master', self.name])

    def delif(self, interface):
        return self._ip_link(['set', 'dev', interface, 'nomaster'])

    def setfd(self, fd):
        return self._ip_link(['set', 'dev', self.name, 'type', 'bridge',
                              'forward_delay', str(fd)])

    def disable_stp(self):
        return self._ip_link(['set', 'dev', self.name, 'type', 'bridge',
                              'stp_state', 0])

    def owns_interface(self, interface):
        return os.path.exists(
            BRIDGE_INTERFACE_FS % {'bridge': self.name,
                                   'interface': interface})

    def get_interfaces(self):
        try:
            return os.listdir(BRIDGE_INTERFACES_FS % self.name)
        except OSError:
            return []
