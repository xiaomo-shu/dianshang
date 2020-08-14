import six
import time
import logging
from common import encodeutils
from common import constants
from yzy_compute import utils, exception
from yzy_compute.virt.libvirt import config as vconfig


libvirt = None
VIR_DOMAIN_NOSTATE = 0
VIR_DOMAIN_RUNNING = 1
VIR_DOMAIN_BLOCKED = 2
VIR_DOMAIN_PAUSED = 3
VIR_DOMAIN_SHUTDOWN = 4
VIR_DOMAIN_SHUTOFF = 5
VIR_DOMAIN_CRASHED = 6
VIR_DOMAIN_PMSUSPENDED = 7

LIBVIRT_POWER_STATE = {
    VIR_DOMAIN_NOSTATE: constants.DOMAIN_STATE['nostate'],
    VIR_DOMAIN_RUNNING: constants.DOMAIN_STATE['running'],
    # The DOMAIN_BLOCKED state is only valid in Xen.  It means that
    # the VM is running and the vCPU is idle. So, we map it to RUNNING
    VIR_DOMAIN_BLOCKED: constants.DOMAIN_STATE['running'],
    VIR_DOMAIN_PAUSED: constants.DOMAIN_STATE['paused'],
    # The libvirt API doc says that DOMAIN_SHUTDOWN means the domain
    # is being shut down. So technically the domain is still
    # running. SHUTOFF is the real powered off state.  But we will map
    # both to SHUTDOWN anyway.
    # http://libvirt.org/html/libvirt-libvirt.html
    VIR_DOMAIN_SHUTDOWN: constants.DOMAIN_STATE['shutdown'],
    VIR_DOMAIN_SHUTOFF: constants.DOMAIN_STATE['shutdown'],
    VIR_DOMAIN_CRASHED: constants.DOMAIN_STATE['crashed'],
    VIR_DOMAIN_PMSUSPENDED: constants.DOMAIN_STATE['pmsuspended'],
}


class InstanceInfo(object):

    def __init__(self, state, internal_id=None):
        """Create a new Instance Info object

        :param state: Required. The running state, one of the power_state codes
        :param internal_id: Optional. A unique ID for the instance. Need not be
                            related to the Instance.uuid.
        """
        self.state = state
        self.internal_id = internal_id

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.__dict__ == other.__dict__)


class Guest(object):

    def __init__(self, domain):

        global libvirt
        if libvirt is None:
            libvirt = utils.import_module('libvirt')

        self._domain = domain

    def __repr__(self):
        return "<Guest %(id)d %(name)s %(uuid)s>" % {
            'id': self.id,
            'name': self.name,
            'uuid': self.uuid
        }

    @property
    def id(self):
        return self._domain.ID()

    @property
    def uuid(self):
        return self._domain.UUIDString()

    @property
    def name(self):
        return self._domain.name()

    @property
    def _encoded_xml(self):
        return encodeutils.safe_decode(self._domain.XMLDesc(0))

    @classmethod
    def create(cls, xml, host):
        """Create a new Guest

        :param xml: XML definition of the domain to create
        :param host: host.Host connection to define the guest on

        :returns guest.Guest: Guest ready to be launched
        """
        try:
            if six.PY3 and isinstance(xml, six.binary_type):
                xml = xml.decode('utf-8')
            guest = host.write_instance_config(xml)
        except:
            with exception.save_and_reraise_exception():
                logging.error('Error defining a guest with XML: %s',
                          encodeutils.safe_decode(xml))
        return guest

    def launch(self, pause=False):
        """Starts a created guest.

        :param pause: Indicates whether to start and pause the guest
        """
        flags = pause and libvirt.VIR_DOMAIN_START_PAUSED or 0
        logging.info("launch guest, flags:%s", flags)
        try:
            return self._domain.createWithFlags(flags)
        except Exception:
            logging.error('Error launching a defined domain with XML: %s', self._encoded_xml)
            raise

    def poweroff(self):
        """Stops a running guest."""
        self._domain.destroy()

    def resume(self):
        """Resumes a paused guest."""
        logging.info("resume domain")
        self._domain.resume()

    def pause(self):
        """Suspends an active guest

        Process is frozen without further access to CPU resources and
        I/O but the memory used by the domain at the hypervisor level
        will stay allocated.

        See method "resume()" to reactive guest.
        """
        logging.info("suspend domain")
        self._domain.suspend()

    def _get_domain_info(self):
        """Returns information on Guest.

        :returns list: [state, maxMem, memory, nrVirtCpu, cpuTime]
        """
        return self._domain.info()

    def get_power_state(self):
        return self.get_info().state

    def get_info(self):
        """Retrieve information from libvirt for a specific instance name.

        If a libvirt error is encountered during lookup, we might raise a
        NotFound exception or Error exception depending on how severe the
        libvirt error is.
        """
        try:
            dom_info = self._get_domain_info()
        except libvirt.libvirtError as ex:
            error_code = ex.get_error_code()
            if error_code == libvirt.VIR_ERR_NO_DOMAIN:
                raise exception.InstanceNotFound(instance_id=self.uuid)

            msg = ('Error from libvirt while getting domain info for '
                     '%(instance_name)s: [Error Code %(error_code)s] %(ex)s' %
                   {'instance_name': self.name,
                    'error_code': error_code,
                    'ex': ex})
            raise Exception(msg)

        return InstanceInfo(
            state=LIBVIRT_POWER_STATE[dom_info[0]],
            internal_id=self.id)

    def shutdown(self):
        """Shutdown guest"""
        self._domain.shutdown()

    def delete_configuration(self, support_uefi=False):
        """
        Undefines a domain from hypervisor.
        {
            VIR_DOMAIN_UNDEFINE_MANAGED_SAVE	=	1   #Also remove any managed save
            VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA	=	2 #If last use of domain, then also remove any snapshot metadata
            VIR_DOMAIN_UNDEFINE_NVRAM	=	4 (0x4; 1 << 2)  #Also remove any nvram file
            VIR_DOMAIN_UNDEFINE_KEEP_NVRAM	=	8 (0x8; 1 << 3) # Keep nvram file
            #If last use of domain, then also remove any checkpoint metadata Future undefine control flags should come here.
            VIR_DOMAIN_UNDEFINE_CHECKPOINTS_METADATA	=	16 (0x10; 1 << 4)

        }
        """
        try:
            flags = libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE
            if support_uefi:
                flags |= libvirt.VIR_DOMAIN_UNDEFINE_NVRAM
            self._domain.undefineFlags(flags)
        except libvirt.libvirtError:
            logging.error("Error from libvirt during undefineFlags for guest "
                      "%d. Retrying with undefine", self.id)
            self._domain.undefine()
        except AttributeError:
            # Older versions of libvirt don't support undefine flags,
            # trying to remove managed image
            try:
                if self._domain.hasManagedSaveImage(0):
                    self._domain.managedSaveRemove(0)
            except AttributeError:
                pass
            self._domain.undefine()

    def sync_guest_time(self):
        """Try to set VM time to the current value.  This is typically useful
        when clock wasn't running on the VM for some time (e.g. during
        suspension or migration), especially if the time delay exceeds NTP
        tolerance.

        It is not guaranteed that the time is actually set (it depends on guest
        environment, especially QEMU agent presence) or that the set time is
        very precise (NTP in the guest should take care of it if needed).
        """
        t = time.time()
        seconds = int(t)
        nseconds = int((t - seconds) * 10 ** 9)
        try:
            self._domain.setTime(time={'seconds': seconds,
                                       'nseconds': nseconds})
        except libvirt.libvirtError as e:
            code = e.get_error_code()
            if code == libvirt.VIR_ERR_AGENT_UNRESPONSIVE:
                logging.warning('Failed to set time: QEMU agent unresponsive')
            elif code == libvirt.VIR_ERR_OPERATION_UNSUPPORTED:
                logging.warning('Failed to set time: not supported')
            elif code == libvirt.VIR_ERR_ARGUMENT_UNSUPPORTED:
                logging.warning('Failed to set time: agent not configured')
            else:
                logging.warning('Failed to set time: %(reason)s', {'reason': e})
        except Exception as ex:
            # The highest priority is not to let this method crash and thus
            # disrupt its caller in any way.  So we swallow this error here,
            # to be absolutely safe.
            logging.error('Failed to set time: %(reason)s', {'reason': ex})
        else:
            logging.info('Time updated to: %d.%09d', seconds, nseconds)

    def get_all_devices(self, devtype=None):
        """Returns all devices for a guest

        :param devtype: a LibvirtConfigGuestDevice subclass class

        :returns: a list of LibvirtConfigGuestDevice instances
        """

        try:
            config = vconfig.LibvirtConfigGuest()
            config.parse_str(self._domain.XMLDesc(0))
        except Exception:
            return []

        devs = []
        for dev in config.devices:
            if (devtype is None or isinstance(dev, devtype)):
                devs.append(dev)
        return devs

    def change_cdrom_path(self, conf, persistent=False, live=False):
        """Attaches device to the guest.
        VIR_DOMAIN_AFFECT_CURRENT=0 (0x0)	Affect current domain state.
        VIR_DOMAIN_AFFECT_LIVE=1 (0x1; 1 << 0)	Affect running domain state.
        VIR_DOMAIN_AFFECT_CONFIG=2 (0x2; 1 << 1)    Affect persistent domain state.

        :param conf: A LibvirtConfigObject of the device to attach
        :param persistent: A bool to indicate whether the change is
                           persistent or not
        :param live: A bool to indicate whether it affect the guest
                     in running state
        """
        flags = persistent and libvirt.VIR_DOMAIN_AFFECT_CONFIG or 0
        flags |= live and libvirt.VIR_DOMAIN_AFFECT_LIVE or 0
        logging.debug("change cdrom device, flags:%s", flags)
        device_xml = conf.to_xml()
        if six.PY3 and isinstance(device_xml, six.binary_type):
            device_xml = device_xml.decode('utf-8')

        logging.debug("change cdrom device xml: %s", device_xml)
        # 使用update方法替换cdrom中的内容，但是使用此方法，在虚拟机中弹出后，
        # 需要disconnect磁盘然后再调用此方法才能在虚拟机中再看到磁盘内容
        self._domain.updateDeviceFlags(device_xml, flags=flags)
        # self._domain.attachDeviceFlags(device_xml, flags=flags)

    def attach_device(self, conf, persistent=False, live=False):
        """changing CDROM/Floppy device media, altering the graphics configuration such as password,
        reconfiguring the NIC device backend connectivity, etc

        :param conf: A LibvirtConfigObject of the device
        :param persistent: A bool to indicate whether the change is
                           persistent or not
        :param live: A bool to indicate whether it affect the guest
                     in running state

        VIR_DOMAIN_AFFECT_CURRENT=0 (0x0)	Affect current domain state.
        VIR_DOMAIN_AFFECT_LIVE=1 (0x1; 1 << 0)	Affect running domain state.
        VIR_DOMAIN_AFFECT_CONFIG选项会影响xml定义文件
        VIR_DOMAIN_AFFECT_CONFIG=2 (0x2; 1 << 1)    Affect persistent domain state.
        1 << 2 is reserved for virTypedParameterFlags
        """
        flags = persistent and libvirt.VIR_DOMAIN_AFFECT_CONFIG or 0
        flags |= live and libvirt.VIR_DOMAIN_AFFECT_LIVE or 0

        device_xml = conf.to_xml()
        if six.PY3 and isinstance(device_xml, six.binary_type):
            device_xml = device_xml.decode('utf-8')

        logging.debug("change device xml: %s", device_xml)
        self._domain.attachDeviceFlags(device_xml, flags=flags)

    def detach_device(self, conf, persistent=False, live=False):
        """Detaches device to the guest.

        :param conf: A LibvirtConfigObject of the device to detach
        :param persistent: A bool to indicate whether the change is
                           persistent or not
        :param live: A bool to indicate whether it affect the guest
                     in running state
        """
        flags = persistent and libvirt.VIR_DOMAIN_AFFECT_CONFIG or 0
        flags |= live and libvirt.VIR_DOMAIN_AFFECT_LIVE or 0
        logging.debug("detach device, flags:%s", flags)
        device_xml = conf.to_xml()
        if six.PY3 and isinstance(device_xml, six.binary_type):
            device_xml = device_xml.decode('utf-8')

        logging.debug("detach device xml: %s", device_xml)
        self._domain.detachDeviceFlags(device_xml, flags=flags)

    def ctrl_alt_del(self):
        """
        Sends CTRL+ALT+DEL to a VM
        """
        return self._domain.sendKey(0, 0, [29, 56, 111], 3, 0) == 0

    def set_autostart(self, start=True):
        """
        autostart a vm
        """
        return self._domain.setAutostart(start)

    def set_vcpu_and_ram(self, vcpu=None, ram=None, persistent=False, max=False):
        """
        change the number of virtual cpus
        注意当前的设置要在最大设置之后
        """
        flags = persistent and libvirt.VIR_DOMAIN_AFFECT_CONFIG or 0
        flags |= max and libvirt.VIR_DOMAIN_MEM_MAXIMUM or 0
        if vcpu:
            logging.info("set vcpus, vcpu:%s, flags:%s", vcpu, flags)
            self._domain.setVcpusFlags(vcpu, flags=flags)
            self._domain.setVcpusFlags(vcpu, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
        if ram:
            logging.info("set ram, ram:%s, flags:%s", ram, flags)
            self._domain.setMemoryFlags(int(ram * constants.Ki), flags=flags)
            self._domain.setMemoryFlags(int(ram * constants.Ki), libvirt.VIR_DOMAIN_AFFECT_CURRENT)
