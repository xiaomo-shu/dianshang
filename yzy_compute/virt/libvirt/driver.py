import logging
import os
import time
import errno
import shutil
import json
import psutil
import math
import functools
from six.moves import range
from . import host
from . import config as vconfig
from . import guest as libvirt_guest
from yzy_compute.virt import configdrive
from common import constants
from common import cmdutils
from common.config import SERVER_CONF as CONF
from yzy_compute import utils
from yzy_compute import exception
from yzy_compute.network.linuxbridge_agent import LinuxBridgeManager


libvirt = None


class LibvirtDriver(object):

    def __init__(self, read_only=False):
        super(LibvirtDriver, self).__init__()

        global libvirt
        if libvirt is None:
            libvirt = utils.import_module('libvirt')

        self._host = host.Host(self._uri(), read_only)
        # self._initiator = None
        # self._fc_wwnns = None
        # self._fc_wwpns = None
        # self._supported_perf_events = []
        # self.__has_hyperthreading = None
        #
        # self.vif_driver = libvirt_vif.LibvirtGenericVIFDriver()

    @staticmethod
    def _uri():
        if CONF.libvirt.virt_type == 'uml':
            uri = CONF.libvirt.connection_uri or 'uml:///system'
        elif CONF.libvirt.virt_type == 'xen':
            uri = CONF.libvirt.connection_uri or 'xen:///'
        elif CONF.libvirt.virt_type == 'lxc':
            uri = CONF.libvirt.connection_uri or 'lxc:///'
        elif CONF.libvirt.virt_type == 'parallels':
            uri = CONF.libvirt.connection_uri or 'parallels:///system'
        else:
            uri = CONF.libvirt.connection_uri or 'qemu:///system'
        return uri

###################### below is about xml#######################################
    def _get_guest_cpu_config(self, vcpus):
        cpu = vconfig.LibvirtConfigGuestCPU()
        cpu.mode = 'host-model'
        cpu.model = None
        if (vcpus & 1) == 0:
            cpu.sockets = 2
            cpu.cores = int(vcpus / 2)
            cpu.threads = 1
        else:
            cpu.sockets = 1
            cpu.cores = vcpus
            cpu.threads = 1
        return cpu

    def _get_guest_os_type(self, virt_type):
        """
        Returns the guest OS type based on virt type.
        The type element specifies the type of operating system to be booted in the virtual machine.
        hvm indicates that the OS is one designed to run on bare metal, so requires full virtualization
        """
        if virt_type == "lxc":
            ret = "exe"
        elif virt_type == "uml":
            ret = "uml"
        elif virt_type == "xen":
            ret = "xen"
        else:
            ret = "hvm"
        return ret

    def _set_kvm_timers(self, clk, os_type):
        # TODO(berrange) One day this should be per-guest
        # OS type configurable
        tmpit = vconfig.LibvirtConfigGuestTimer()
        tmpit.name = "pit"
        tmpit.tickpolicy = "delay"

        tmrtc = vconfig.LibvirtConfigGuestTimer()
        tmrtc.name = "rtc"
        tmrtc.tickpolicy = "catchup"

        clk.add_timer(tmpit)
        clk.add_timer(tmrtc)

        hpet = False
        guestarch = utils.canonicalize()
        if guestarch in (constants.I686, constants.X86_64):
            # NOTE(rfolco): HPET is a hardware timer for x86 arch.
            # qemu -no-hpet is not supported on non-x86 targets.
            tmhpet = vconfig.LibvirtConfigGuestTimer()
            tmhpet.name = "hpet"
            tmhpet.present = hpet
            clk.add_timer(tmhpet)
        else:
            logging.warning('HPET is not turned on for non-x86 guests in image')

        # Provide Windows guests with the paravirtualized hyperv timer source.
        # This is the windows equiv of kvm-clock, allowing Windows
        # guests to accurately keep time.
        if os_type == 'windows':
            tmhyperv = vconfig.LibvirtConfigGuestTimer()
            tmhyperv.name = "hypervclock"
            tmhyperv.present = True
            clk.add_timer(tmhyperv)

    def _set_clock(self, guest, os_type, virt_type):
        # NOTE(mikal): Microsoft Windows expects the clock to be in
        # "localtime". If the clock is set to UTC, then you can use a
        # registry key to let windows know, but Microsoft says this is
        # buggy in http://support.microsoft.com/kb/2687252
        clk = vconfig.LibvirtConfigGuestClock()
        if os_type == 'windows':
            logging.info('Configuring timezone for windows instance to localtime')
            clk.offset = 'localtime'
        else:
            clk.offset = 'utc'
        guest.set_clock(clk)

        if virt_type == "kvm":
            self._set_kvm_timers(clk, os_type)

    def _get_guest_storage_config(self, disk_info):
        storages = list()
        index = 1
        for disk in disk_info:
            info = vconfig.LibvirtConfigGuestDisk()
            # we only use file as disk
            info.source_type = "file"
            info.source_device = disk.get('type', 'disk')
            info.target_bus = disk.get('bus', 'virtio')
            if disk.get('dev', None):
                info.target_dev = disk['dev']
            info.source_path = disk['path']
            # ['writeback', 'none', 'writethrough', 'directsync', 'unsafe']
            info.driver_cache = "none"
            # the iso disk format is raw
            if disk.get('type') in ['cdrom', 'floppy']:
                info.driver_format = "raw"
            else:
                info.driver_format = "qcow2"
            info.driver_name = "qemu"
            if disk.get('order', True):
                info.boot_order = str(index)
                index += 1
            storages.append(info)
        return storages

    def _get_guest_vif_config(self, network_info):
        nics = list()
        for net in network_info:
            conf = vconfig.LibvirtConfigGuestInterface()
            conf.mac_addr = net['mac_addr']
            conf.model = net.get('model', 'virtio')
            conf.net_type = 'bridge'
            # conf.model = net['model']
            # conf.net_type = net['net_type']
            conf.source_dev = net['bridge']
            conf.target_dev = "tap%s" % (net['port_id'][:constants.RESOURCE_ID_LENGTH])
            nics.append(conf)
        return nics

    def _create_pty_device(self, guest_cfg, char_dev_cls, target_type=None,
                           log_path=None):

        consolepty = char_dev_cls()
        consolepty.target_type = target_type
        consolepty.type = "pty"

        log = vconfig.LibvirtConfigGuestCharDeviceLog()
        log.file = log_path
        consolepty.log = log

        guest_cfg.add_device(consolepty)

    # def _create_serial_consoles(self, guest_cfg, num_ports, char_dev_cls,
    #                             log_path):
    #     for port in six.moves.range(num_ports):
    #         console = char_dev_cls()
    #         console.port = port
    #         console.type = "tcp"
    #         console.listen_host = CONF.serial_console.proxyclient_address
    #         listen_port = serial_console.acquire_port(console.listen_host)
    #         console.listen_port = listen_port
    #         # NOTE: only the first serial console gets the boot messages,
    #         # that's why we attach the logd subdevice only to that.
    #         if port == 0:
    #             log = vconfig.LibvirtConfigGuestCharDeviceLog()
    #             log.file = log_path
    #             console.log = log
    #         guest_cfg.add_device(console)

    def _create_consoles_qemu_kvm(self, guest_cfg, instance, base_path):
        char_dev_cls = vconfig.LibvirtConfigGuestSerial
        instance_path = os.path.join(base_path, instance['uuid'])
        log_path = os.path.join(instance_path, 'console.log')
        try:
            utils.ensure_tree(instance_path)
        except:
            pass
        # self._create_serial_consoles(guest_cfg, num_ports,
        #                              char_dev_cls, log_path)
        self._create_pty_device(guest_cfg, char_dev_cls,
                                log_path=log_path)

    @staticmethod
    def _guest_add_spice_channel(guest):
        if (CONF.spice.enabled and CONF.spice.agent_enabled and
                guest.virt_type not in ('lxc', 'uml', 'xen')):
            channel = vconfig.LibvirtConfigGuestChannel()
            channel.type = 'spicevmc'
            channel.target_name = "com.redhat.spice.0"
            guest.add_device(channel)

    @staticmethod
    def _guest_add_redirected_devices(guest):
        redirdev = vconfig.LibvirtConfigGuestRedirect()
        for i in range(4):
            guest.add_device(redirdev)
        return redirdev

    @staticmethod
    def _guest_add_video_device(instance, guest, spice_token=None):
        # NB some versions of libvirt support both SPICE and VNC
        # at the same time. We're not trying to second guess which
        # those versions are. We'll just let libvirt report the
        # errors appropriately if the user enables both.
        add_video_driver = False
        if CONF.vnc.enabled and guest.virt_type not in ('lxc', 'uml'):
            graphics = vconfig.LibvirtConfigGuestGraphics()
            graphics.type = "vnc"
            if CONF.vnc.keymap:
                graphics.keymap = CONF.vnc.keymap
            graphics.listen = CONF.vnc.server_listen
            guest.add_device(graphics)
            add_video_driver = True
        if CONF.spice.enabled and guest.virt_type not in ('lxc', 'uml', 'xen'):
            if instance.get('spice', True):
                graphics = vconfig.LibvirtConfigGuestGraphics()
                graphics.type = "spice"
                if CONF.spice.keymap:
                    graphics.keymap = CONF.spice.keymap
                graphics.listen = CONF.spice.server_listen
                graphics.image_compression = "auto_glz"
                graphics.jpeg_compression = "always"
                graphics.zlib_compression = "never"
                graphics.stream_mode = "filter"
                graphics.clipboard = "yes"
                graphics.mouse_mode = "client"
                if spice_token and isinstance(spice_token, str):
                    graphics.passwd = spice_token
                guest.add_device(graphics)
                add_video_driver = True
        return add_video_driver

    def _add_video_driver(self, guest):
        video = vconfig.LibvirtConfigGuestVideo()
        # NOTE(ldbragst): The following logic sets the video.type
        # depending on supported defaults given the architecture,
        # virtualization type, and features. The video.type attribute can
        # be overridden by the user with image_meta.properties, which
        # is carried out in the next if statement below this one.
        # guestarch = libvirt_utils.get_arch(image_meta)
        # if guest.os_type == fields.VMMode.XEN:
        #     video.type = 'xen'
        # elif CONF.libvirt.virt_type == 'parallels':
        #     video.type = 'vga'
        # elif guestarch in (fields.Architecture.PPC,
        #                    fields.Architecture.PPC64,
        #                    fields.Architecture.PPC64LE):
        #     # NOTE(ldbragst): PowerKVM doesn't support 'cirrus' be default
        #     # so use 'vga' instead when running on Power hardware.
        #     video.type = 'vga'
        # elif guestarch == fields.Architecture.AARCH64:
        #     # NOTE(kevinz): Only virtio device type is supported by AARCH64
        #     # so use 'virtio' instead when running on AArch64 hardware.
        #     video.type = 'virtio'
        # elif CONF.spice.enabled:
        #     video.type = 'qxl'
        # if image_meta.properties.get('hw_video_model'):
        #     video.type = image_meta.properties.hw_video_model
        #     if not self._video_model_supported(video.type):
        #         raise exception.InvalidVideoMode(model=video.type)

        # Set video memory, only if the flavor's limit is set
        # video_ram = image_meta.properties.get('hw_video_ram', 0)
        # max_vram = int(flavor.extra_specs.get('hw_video:ram_max_mb', 0))
        # if video_ram > max_vram:
        #     raise exception.RequestedVRamTooHigh(req_vram=video_ram,
        #                                          max_vram=max_vram)
        # if max_vram and video_ram:
        #     video.vram = video_ram * units.Mi / units.Ki
        video.type = 'qxl'
        guest.add_device(video)

        # NOTE(sean-k-mooney): return the video device we added
        # for simpler testing.
        return video

    def _add_sound_device(self, guest):
        audio = vconfig.LibvirtConfigGuestSound()
        guest.add_device(audio)
        return audio

    @staticmethod
    def _guest_add_memory_balloon(guest):
        virt_type = guest.virt_type
        # Memory balloon device only support 'qemu/kvm' and 'xen' hypervisor
        if virt_type in ('xen', 'qemu', 'kvm'):
            balloon = vconfig.LibvirtConfigMemoryBalloon()
            if virt_type in ('qemu', 'kvm'):
                balloon.model = 'virtio'
            # balloon.period = CONF.libvirt.mem_stats_period_seconds
            balloon.period = 10
            guest.add_device(balloon)

    def _get_guest_config_sysinfo(self, instance):
        sysinfo = vconfig.LibvirtConfigGuestSysinfo()

        sysinfo.system_manufacturer = 'YZY'
        sysinfo.system_product = 'kvm'
        sysinfo.system_version = '1.0.0'

        sysinfo.system_serial = instance['uuid']
        sysinfo.system_uuid = instance['uuid']

        sysinfo.system_family = "Virtual Machine"

        return sysinfo

    def _configure_guest_by_virt_type(self, guest, virt_type, instance):
        if virt_type in ("kvm", "qemu"):
            guestarch = utils.canonicalize()
            if guestarch in (constants.I686, constants.X86_64):
                guest.sysinfo = self._get_guest_config_sysinfo(instance)
                guest.os_smbios = vconfig.LibvirtConfigGuestSMBIOS()
            guest.os_mach_type = utils.get_default_machine_type()

    def _get_guest_usb_tablet(self):
        tablet = vconfig.LibvirtConfigGuestInput()
        tablet.type = "tablet"
        tablet.bus = "usb"
        return tablet

    def _set_features(self, guest, os_type, virt_type):
        # if there is not acpi, the shutdown cmd could not work
        if virt_type not in ("lxc", "uml", "parallels", "xen"):
            guest.features.append(vconfig.LibvirtConfigGuestFeatureACPI())
            guest.features.append(vconfig.LibvirtConfigGuestFeatureAPIC())

        if (virt_type in ("qemu", "kvm") and
                os_type == 'windows'):
            hv = vconfig.LibvirtConfigGuestFeatureHyperV()
            hv.relaxed = True

            hv.spinlocks = True
            # Increase spinlock retries - value recommended by
            # KVM maintainers who certify Windows guests
            # with Microsoft
            hv.spinlock_retries = 8191
            hv.vapic = True

            # NOTE(kosamara): Spoofing the vendor_id aims to allow the nvidia
            # driver to work on windows VMs. At the moment, the nvidia driver
            # checks for the hyperv vendorid, and if it doesn't find that, it
            # works. In the future, its behaviour could become more strict,
            # checking for the presence of other hyperv feature flags to
            # determine that it's loaded in a VM. If that happens, this
            # workaround will not be enough, and we'll need to drop the whole
            # hyperv element.
            # That would disable some optimizations, reducing the guest's
            # performance.

            guest.features.append(hv)

    def _get_guest_config(self, instance, network_info, disk_info):
        logging.info("_get_guest_config begin, instance:%s", instance['name'])
        virt_type = CONF.libvirt.virt_type
        guest = vconfig.LibvirtConfigGuest()
        guest.virt_type = virt_type
        guest.name = instance['base_name']
        guest.uuid = instance['uuid']
        guest.memory = int(instance['ram'] * constants.Ki)
        guest.vcpus = instance['vcpus']
        guest.cpu = self._get_guest_cpu_config(guest.vcpus)

        guest.os_type = self._get_guest_os_type(virt_type)
        # caps need to known what is
        # caps =
        # 系统启动盘的格式
        # guest.os_boot_dev = ['cdrom', 'hd']
        guest.os_bootmenu = True
        # set the os machine type
        self._configure_guest_by_virt_type(guest, virt_type, instance)
        self._set_features(guest, instance['os_type'], virt_type)
        # what the difference of guest.os_type and instance.os_type
        self._set_clock(guest, instance['os_type'], virt_type)

        # next is disk info
        logging.info("get disk config, instance:%s", instance['name'])
        storage_configs = self._get_guest_storage_config(disk_info)
        for config in storage_configs:
            guest.add_device(config)

        # next is network info
        logging.info("get network config, instance:%s", instance['name'])
        network_configs = self._get_guest_vif_config(network_info)
        for config in network_configs:
            guest.add_device(config)

        # next is about consoles
        # base_path = constants.DEFAULT_SYS_PATH
        # for disk in disk_info:
        #     if constants.SYSTEM_BOOT_INDEX == disk['boot_index']:
        #         base_path = disk['base_path']
        #         break
        # self._create_consoles_qemu_kvm(guest, instance, base_path)

        # usb tablet,解决鼠标漂移问题
        if CONF.vnc.enabled or (
                CONF.spice.enabled and not CONF.spice.agent_enabled):
            pointer = self._get_guest_usb_tablet()
            if pointer:
                guest.add_device(pointer)
        # add usb redirected devices
        self._guest_add_redirected_devices(guest)
        # add spice
        self._guest_add_spice_channel(guest)

        # add video
        spice_token = instance.get("spice_token")
        if self._guest_add_video_device(instance, guest, spice_token):
            self._add_video_driver(guest)
        self._add_sound_device(guest)
        self._guest_add_memory_balloon(guest)
        logging.info("_get_guest_config end, instance:%s", instance['name'])
        return guest

    def _create_configdrive(self, instance, network_info, config_path):
        logging.info('Using config drive')
        # name = 'disk.config'
        # # instance_path = utils.get_instance_path(instance)
        # config_path = os.path.join('/opt', name)

        # Don't overwrite an existing config drive
        # if not os.path.exists(config_path):
        # logging.info("the configdrive device is not exists")
        cdb = configdrive.ConfigDriveBuilder(instance, network_info)
        with cdb:
            logging.info('Creating config drive at %s', config_path)
            try:
                cdb.make_drive(config_path)
            except cmdutils.ProcessExecutionError as e:
                logging.error('Creating config drive failed with '
                              'error: %s', e)

    def plug_vif(self, network_info):
        for network in network_info:
            vif_info = network['vif_info']
            if vif_info.get('vlan_id', None):
                LinuxBridgeManager().ensure_vlan_bridge(int(vif_info['vlan_id']), vif_info['bridge'], vif_info['interface'])
            else:
                LinuxBridgeManager().ensure_bridge(vif_info['bridge'], vif_info['interface'])

    def _create_domain(self, instance, network_info, disk_info, configdrive=True, power_on=True):
        configdisk = None
        if configdrive:
            # when create virtual machine, we add a configdrive disk info
            # the boot_index is same with boot disk, so we put the configdriver file in instance data dir
            cdroms = list()
            for disk in disk_info:
                if "cdrom" == disk.get('type', 'disk'):
                    cdroms.append(disk)
            if cdroms:
                # 获取第一个cdrom用作IP设置
                configdisk = cdroms[0]
                for dev in cdroms:
                    if dev['dev'] < configdisk['dev']:
                        configdisk = dev
            # 如果没有cdrom，则默认加一个
            if not configdisk:
                configdisk = {
                    "bus": "ide",
                    "type": "cdrom",
                    "dev": "hda"
                }
                disk_info.append(configdisk)
            if configdisk:
                disk_config_path = os.path.join(constants.DEFAULT_CONFIGDRIVE_PATH, '%s.config' % instance['uuid'])
                configdisk['path'] = disk_config_path
                logging.info("update configdrive device %s path to %s", configdisk['dev'], disk_config_path)
                gen_confdrive = functools.partial(self._create_configdrive, instance, network_info, disk_config_path)
        self.plug_vif(network_info)
        xml = self._get_guest_xml(instance, network_info, disk_info)
        if configdisk:
            guest = self._create_guest(xml, post_xml_callback=gen_confdrive, power_on=power_on)
        else:
            guest = self._create_guest(xml, power_on=power_on)
        return guest

    def _get_guest_xml(self, instance, network_info, disk_info):
        """
        以下是openstack的disk_info结构，供参考
        {'disk_bus': 'virtio', 'cdrom_bus': 'ide',
        'mapping': {'disk': {'bus': 'virtio', 'boot_index': '1', 'type': 'disk', 'dev': u'vda'},
        'root': {'bus': 'virtio', 'boot_index': '1', 'type': 'disk', 'dev': u'vda'}}}
        """
        conf = self._get_guest_config(instance, network_info, disk_info)
        xml = conf.to_xml()
        logging.debug('End _get_guest_xml xml=%(xml)s', {'xml': xml})
        return xml

    def _create_guest(self, xml=None, domain=None, power_on=True, pause=False,
                      post_xml_callback=None):
        """Create a domain.

        Either domain or xml must be passed in. If both are passed, then
        the domain definition is overwritten from the xml.

        :returns guest.Guest: Guest just created
        """
        if xml:
            logging.info("create guest from xml")
            guest = libvirt_guest.Guest.create(xml, self._host)
            if post_xml_callback is not None:
                post_xml_callback()
        else:
            logging.info("create guest from exist domain")
            guest = libvirt_guest.Guest(domain)
        if power_on or pause:
            guest.launch(pause=pause)
            logging.info("launch guest end")
        logging.info("define domain end")
        return guest

    # create the diff file
    def _prepare_disk(self, server_id, disk):
        logging.info("prepare disk for instance, uuid:%s, disk:%s", server_id, disk)
        # system disk and data disk in different position
        base_path = disk['base_path']
        # if constants.SYSTEM_BOOT_INDEX == disk['boot_index']:
        #     base_path = CONF.libvirt.instances_path
        # else:
        #     base_path = CONF.libvirt.data_path
        base_dir = os.path.join(base_path, server_id)
        utils.ensure_tree(base_dir)

        # create the disk file
        disk_file = "%s/%s%s" % (base_dir, constants.DISK_FILE_PREFIX, disk['uuid'])
        if os.path.exists(disk_file):
            # 实现开机还原
            if disk.get('restore', False):
                try:
                    logging.info("the disk is exists and restore, delete")
                    os.remove(disk_file)
                except:
                    pass
            else:
                logging.info("the disk is exists and not restore, return")
                return disk_file
        if disk.get('image_id', None):
            version = disk.get('image_version', 0)
            if version > 0:
                backing_file = utils.get_backing_file(1, disk['image_id'], base_path)
            else:
                backing_file = utils.get_backing_file(0, disk['image_id'], base_path)
            # if disk.get('size', None):
            #     cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', disk_file, '-o',
            #                      'backing_file=%s' % backing_file,
            #                      disk['size'], run_as_root=True)
            # else:
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', disk_file, '-o',
                                 'backing_file=%s' % backing_file, run_as_root=True)
            logging.info("create the diff disk success")
        else:
            # if there is no backing file, create the disk with size info
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', disk_file, disk['size'], run_as_root=True)
            logging.info("create the diff disk success")
        return disk_file

    def get_info(self, instance, use_cache=True):
        """Retrieve information from libvirt for a specific instance.

        If a libvirt error is encountered during lookup, we might raise a
        NotFound exception or Error exception depending on how severe the
        libvirt error is.

        :param instance: nova.objects.instance.Instance object
        :param use_cache: unused in this driver
        :returns: An InstanceInfo object
        """
        guest = self._host.get_guest(instance)
        return guest.get_info()

    def _clean_shutdown(self, instance, timeout, retry_interval):
        """Attempt to shutdown the instance gracefully.

        :param instance: The instance to be shutdown
        :param timeout: How long to wait in seconds for the instance to
                        shutdown
        :param retry_interval: How often in seconds to signal the instance
                               to shutdown while waiting

        :returns: True if the shutdown succeeded
        """
        logging.info("clean shutdown, instance:%s", instance['name'])
        # List of states that represent a shutdown instance
        SHUTDOWN_STATES = [constants.DOMAIN_STATE['shutdown'],
                           constants.DOMAIN_STATE['crashed']]

        try:
            guest = self._host.get_guest(instance)
        except exception.InstanceNotFound:
            # If the instance has gone then we don't need to
            # wait for it to shutdown
            return True

        state = guest.get_power_state()
        if state in SHUTDOWN_STATES:
            logging.info("Instance already shutdown.")
            return True

        logging.info("Shutting down instance:%s from state %s", instance['name'], state)
        if state == constants.DOMAIN_STATE['paused']:
            try:
                logging.info("resume domain")
                guest.resume()
            except libvirt.libvirtError as e:
                logging.exception("resume domain error:%s", e)
        guest.shutdown()
        retry_countdown = retry_interval

        for sec in range(timeout*2):

            guest = self._host.get_guest(instance)
            state = guest.get_power_state()

            if state in SHUTDOWN_STATES:
                logging.info("Instance shutdown successfully after %s seconds, state:%s", sec/2.0, state)
                return True

            # Note(PhilD): We can't assume that the Guest was able to process
            #              any previous shutdown signal (for example it may
            #              have still been startingup, so within the overall
            #              timeout we re-trigger the shutdown every
            #              retry_interval
            if retry_countdown == 0:
                retry_countdown = retry_interval
                # Instance could shutdown at any time, in which case we
                # will get an exception when we call shutdown
                try:
                    logging.debug("Instance in state %s after %s seconds - resending shutdown", state, sec/2.0)
                    guest.shutdown()
                except libvirt.libvirtError:
                    # Assume this is because its now shutdown, so loop
                    # one more time to clean up.
                    logging.info("Ignoring libvirt exception from shutdown request.")
                    continue
            else:
                retry_countdown -= 1

            time.sleep(0.5)

        logging.info("Instance failed to shutdown in %d seconds.", timeout)
        return False

    def _undefine_domain(self, instance, support_uefi=False):
        try:
            logging.info("undefine domain")
            guest = self._host.get_guest(instance)
            try:
                guest.delete_configuration(support_uefi)
            except libvirt.libvirtError as e:
                errcode = e.get_error_code()
                if errcode == libvirt.VIR_ERR_NO_DOMAIN:
                    logging.info("Called undefine, but domain already gone.")
                else:
                    logging.error('Error from libvirt during undefine. '
                              'Code=%(errcode)s Error=%(e)s',
                              {'errcode': errcode, 'e': e})
        except exception.InstanceNotFound:
            pass

    def destroy(self, instance, destroy_disks=True):
        """when delete instance, it will be called"""
        self._destroy(instance)
        self.cleanup(instance, destroy_disks)

    def _destroy(self, instance, attempt=1):
        try:
            guest = self._host.get_guest(instance)
        except exception.InstanceNotFound:
            guest = None

        # If the instance is already terminated, we're still happy
        # Otherwise, destroy it
        old_domid = -1
        if guest is not None:
            try:
                old_domid = guest.id
                logging.info("destroy instance:%s", instance['name'])
                guest.poweroff()
            except libvirt.libvirtError as e:
                is_okay = False
                errcode = e.get_error_code()
                if errcode == libvirt.VIR_ERR_NO_DOMAIN:
                    # Domain already gone. This can safely be ignored.
                    is_okay = True
                elif errcode == libvirt.VIR_ERR_OPERATION_INVALID:
                    # If the instance is already shut off, we get this:
                    # Code=55 Error=Requested operation is not valid:
                    # domain is not running
                    state = guest.get_power_state()
                    if state == constants.DOMAIN_STATE['shutdown']:
                        is_okay = True
                elif errcode == libvirt.VIR_ERR_INTERNAL_ERROR:
                    errmsg = e.get_error_message()
                    if (CONF.libvirt.virt_type == 'lxc' and
                        errmsg == 'internal error: '
                                  'Some processes refused to die'):
                        # Some processes in the container didn't die
                        # fast enough for libvirt. The container will
                        # eventually die. For now, move on and let
                        # the wait_for_destroy logic take over.
                        is_okay = True
                elif errcode == libvirt.VIR_ERR_OPERATION_TIMEOUT:
                    logging.warning("Cannot destroy instance, operation time out")
                    reason = "operation time out"
                    raise exception.InstancePowerOffFailure(reason=reason)
                elif errcode == libvirt.VIR_ERR_SYSTEM_ERROR:
                    if e.get_int1() == errno.EBUSY:
                        # NOTE(danpb): When libvirt kills a process it sends it
                        # SIGTERM first and waits 10 seconds. If it hasn't gone
                        # it sends SIGKILL and waits another 5 seconds. If it
                        # still hasn't gone then you get this EBUSY error.
                        # Usually when a QEMU process fails to go away upon
                        # SIGKILL it is because it is stuck in an
                        # uninterruptible kernel sleep waiting on I/O from
                        # some non-responsive server.
                        # Given the CPU load of the gate tests though, it is
                        # conceivable that the 15 second timeout is too short,
                        # particularly if the VM running tempest has a high
                        # steal time from the cloud host. ie 15 wallclock
                        # seconds may have passed, but the VM might have only
                        # have a few seconds of scheduled run time.
                        #
                        # TODO(kchamart): Once MIN_LIBVIRT_VERSION
                        # reaches v4.7.0, (a) rewrite the above note,
                        # and (b) remove the following code that retries
                        # _destroy() API call (which gives SIGKILL 30
                        # seconds to take effect) -- because from v4.7.0
                        # onwards, libvirt _automatically_ increases the
                        # timeout to 30 seconds.  This was added in the
                        # following libvirt commits:
                        #
                        #   - 9a4e4b942 (process: wait longer 5->30s on
                        #     hard shutdown)
                        #
                        #   - be2ca0444 (process: wait longer on kill
                        #     per assigned Hostdev)
                        logging.warning('Error from libvirt during '
                                    'destroy. Code=%(errcode)s '
                                    'Error=%(e)s; attempt '
                                    '%(attempt)d of 3 ',
                                    {'errcode': errcode, 'e': e,
                                     'attempt': attempt})
                        # Try up to 3 times before giving up.
                        if attempt < 3:
                            self._destroy(instance, attempt + 1)
                            return

                if not is_okay:
                    logging.error('Error from libvirt during destroy. '
                              'Code=%(errcode)s Error=%(e)s',
                              {'errcode': errcode, 'e': e})

        def _wait_for_destroy(expected_domid):
            """Called at an interval until the VM is gone."""
            # NOTE(vish): If the instance disappears during the destroy
            #             we ignore it so the cleanup can still be
            #             attempted because we would prefer destroy to
            #             never fail.
            try:
                dom_info = self.get_info(instance)
                state = dom_info.state
                new_domid = dom_info.internal_id
            except exception.InstanceNotFound:
                logging.info("During wait destroy, instance disappeared.")
                state = constants.DOMAIN_STATE['shutdown']

            if state == constants.DOMAIN_STATE['shutdown']:
                logging.info("Instance:%s destroyed successfully.", instance['name'])
                return True

            # NOTE(wangpan): If the instance was booted again after destroy,
            #                this may be an endless loop, so check the id of
            #                domain here, if it changed and the instance is
            #                still running, we should destroy it again.
            # see https://bugs.launchpad.net/nova/+bug/1111213 for more details
            if new_domid != expected_domid:
                logging.info("Instance:%s may be started again.", instance['name'])
                kwargs['is_running'] = True

        kwargs = {'is_running': False}
        num = 0
        while num < 5:
            flag = _wait_for_destroy(old_domid)
            if kwargs['is_running']:
                logging.info("Going to destroy instance:%s again.", instance['name'])
                self._destroy(instance)
            if not flag:
                time.sleep(0.5)
                num += 1
            else:
                num += 5

    def cleanup(self, instance, destroy_disks=True):

        if destroy_disks:
            try:
                disk_config_path = os.path.join(constants.DEFAULT_CONFIGDRIVE_PATH, '%s.config' % instance['uuid'])
                os.remove(disk_config_path)
            except Exception as e:
                logging.error("delete configdrive file error:%s", e)
            instance_base = instance.get('sys_base', constants.DEFAULT_SYS_PATH)
            instance_path = os.path.join(instance_base, instance['uuid'])
            try:
                shutil.rmtree(instance_path)
            except OSError as e:
                logging.error('Failed to cleanup directory %(target)s: %(e)s',
                          {'target': instance_path, 'e': e})

            data_path = instance.get('data_base', constants.DEFAULT_DATA_PATH)
            data_path = os.path.join(data_path, instance['uuid'])
            try:
                shutil.rmtree(data_path)
            except OSError as e:
                logging.error('Failed to cleanup directory %(target)s: %(e)s',
                              {'target': data_path, 'e': e})

        self._undefine_domain(instance)

    def _soft_reboot(self, instance):
        """Attempt to shutdown and restart the instance gracefully.

        We use shutdown and create here so we can return if the guest
        responded and actually rebooted. Note that this method only
        succeeds if the guest responds to acpi. Therefore we return
        success or failure so we can fall back to a hard reboot if
        necessary.

        :returns: True if the reboot succeeded
        """
        guest = self._host.get_guest(instance)

        state = guest.get_power_state()
        old_domid = guest.id
        # NOTE(vish): This check allows us to reboot an instance that
        #             is already shutdown.
        if state == constants.DOMAIN_STATE['running']:
            logging.info("instance:%s is running, shutdown", instance['name'])
            guest.shutdown()

        for x in range(constants.SOFT_REBOOT_SECONDS):
            guest = self._host.get_guest(instance)

            state = guest.get_power_state()
            new_domid = guest.id

            # NOTE(ivoks): By checking domain IDs, we make sure we are
            #              not recreating domain that's already running.
            if -1 == old_domid or old_domid != new_domid:
                if state in [constants.DOMAIN_STATE['shutdown'],
                             constants.DOMAIN_STATE['crashed']]:
                    logging.info("Instance:%s shutdown successfully.", instance['name'])
                    self._create_guest(domain=guest._domain)
                    self.wait_for_running(instance)
                    return True
                else:
                    logging.info("Instance may have been rebooted during soft reboot, so return now.")
                    return True
            logging.info("wait shutdown, instance:%s", instance['name'])
            time.sleep(1)
        return False

    def _hard_reboot(self, instance):
        """
        :returns: True if the reboot succeeded
        """
        guest = self._host.get_guest(instance)

        state = guest.get_power_state()
        old_domid = guest.id
        # NOTE(vish): This check allows us to reboot an instance that
        #             is already shutdown.
        if state == constants.DOMAIN_STATE['running']:
            logging.info("instance:%s is running, poweroff", instance['name'])
            guest.poweroff()

        for x in range(constants.SOFT_REBOOT_SECONDS):
            guest = self._host.get_guest(instance)

            state = guest.get_power_state()
            new_domid = guest.id

            # NOTE(ivoks): By checking domain IDs, we make sure we are
            #              not recreating domain that's already running.
            if -1 == old_domid or old_domid != new_domid:
                if state in [constants.DOMAIN_STATE['shutdown'],
                             constants.DOMAIN_STATE['crashed']]:
                    logging.info("Instance:%s poweroff successfully.", instance['name'])
                    self._create_guest(domain=guest._domain)
                    self.wait_for_running(instance)
                    return True
                else:
                    logging.info("Instance may have been rebooted during soft reboot, so return now.")
                    return True
            logging.info("wait shutdown, instance:%s", instance['name'])
            time.sleep(1)
        return False

    # def _hard_reboot(self, instance, network_info, disk_info):
    #     """Reboot a virtual machine, given an instance reference.
    #
    #     Performs a Libvirt reset (if supported) on the domain.
    #
    #     If Libvirt reset is unavailable this method actually destroys and
    #     re-creates the domain to ensure the reboot happens, as the guest
    #     OS cannot ignore this action.
    #     """
    #     # NOTE(mdbooth): In addition to performing a hard reboot of the domain,
    #     # the hard reboot operation is relied upon by operators to be an
    #     # automated attempt to fix as many things as possible about a
    #     # non-functioning instance before resorting to manual intervention.
    #     # With this goal in mind, we tear down all the aspects of an instance
    #     # we can here without losing data. This allows us to re-initialise from
    #     # scratch, and hopefully fix, most aspects of a non-functioning guest.
    #     self.destroy(instance, destroy_disks=False)
    #
    #     # Convert the system metadata to image metadata
    #     # NOTE(mdbooth): This is a workaround for stateless Nova compute
    #     #                https://bugs.launchpad.net/nova/+bug/1349978
    #     base_path = constants.DEFAULT_SYS_PATH
    #     for disk in disk_info:
    #         if constants.SYSTEM_BOOT_INDEX == disk['boot_index']:
    #             base_path = disk['base_path']
    #             break
    #     instance_dir = os.path.join(base_path, instance['uuid'])
    #     utils.ensure_tree(instance_dir)
    #     # NOTE(vish): This could generate the wrong device_format if we are
    #     #             using the raw backend and the images don't exist yet.
    #     #             The create_images_and_backing below doesn't properly
    #     #             regenerate raw backend images, however, so when it
    #     #             does we need to (re)generate the xml after the images
    #     #             are in place.
    #     guest = self._create_domain(instance, network_info, disk_info)
    #     self.wait_for_running(instance)
    #     return guest

    def wait_for_running(self, instance):

        def _wait_for_running(instance):
            state = self.get_info(instance).state

            if state == constants.DOMAIN_STATE['running']:
                logging.info("Instance:%s rebooted successfully.", instance['name'])
                return True

        num = 1
        while num < constants.DOMAIN_START_WAIT:
            flag = _wait_for_running(instance)
            if not flag:
                time.sleep(0.5)
                num += 1
            else:
                num += constants.DOMAIN_START_WAIT

    def power_off(self, instance, timeout=0, retry_interval=0):
        """
        Power off the specified instance.
        :param instance:
            {
                "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                "name": "instance1"
            }
        """
        flag = False
        if timeout:
            flag = self._clean_shutdown(instance, timeout, retry_interval)
        if not flag:
            self._destroy(instance)
        return True

    def pause(self, instance):
        """Pause VM instance."""
        self._host.get_guest(instance).pause()

    def unpause(self, instance):
        """Unpause paused VM instance."""
        guest = self._host.get_guest(instance)
        guest.resume()
        # guest.sync_guest_time()

    def get_guest_spice_port(self, guest):
        port = constants.DEFAULT_SPICE_PORT
        devs = guest.get_all_devices(vconfig.LibvirtConfigGuestGraphics)
        for dev in devs:
            if 'spice' == dev.type:
                port = dev.port
                break
        return port

    def get_guest_port(self, guest):
        port = {
            "vnc_port": 0,
            "spice_port": 0
        }
        devs = guest.get_all_devices(vconfig.LibvirtConfigGuestGraphics)
        for dev in devs:
            if 'vnc' == dev.type:
                port['vnc_port'] = dev.port
                break
        for dev in devs:
            if 'spice' == dev.type:
                port['spice_port'] = dev.port
                break
        return port

    def power_on(self, instance, network_info=None):
        """Power on the specified instance."""
        logging.info("power on the instance:%s", instance['name'])
        result = dict()
        guest = self._host.get_guest(instance)
        # get state
        state = guest.get_power_state()
        if state == constants.DOMAIN_STATE['paused']:
            try:
                guest.resume()
            except:
                pass
            logging.info("domain is paused, resume and return")
            port = self.get_guest_port(guest)
            result['vnc_port'] = port['vnc_port']
            result['state'] = state
            logging.info("the instance already running, return")
            return result
        if state == constants.DOMAIN_STATE['running']:
            port = self.get_guest_port(guest)
            result['vnc_port'] = port['vnc_port']
            result['state'] = state
            logging.info("the instance already running, return")
            return result
        # 利用configdrive重新加载一遍网络信息
        if network_info:
            disk_config_path = os.path.join(constants.DEFAULT_CONFIGDRIVE_PATH, '%s.config' % instance['uuid'])
            self._create_configdrive(instance, network_info, disk_config_path)
            self.plug_vif(network_info)
        guest.launch()
        port = self.get_guest_port(guest)
        result['vnc_port'] = port['vnc_port']
        result['state'] = guest.get_power_state()
        return result

    def reboot(self, instance, reboot_type='soft'):
        """Reboot a virtual machine, given an instance reference."""
        logging.info("begin reboot, type:%s", reboot_type)
        if constants.SOFT_REBOOT == reboot_type:
            try:
                reboot_success = self._soft_reboot(instance)
            except libvirt.libvirtError as e:
                logging.error("Instance soft reboot failed: %s", e)
                reboot_success = False

            if reboot_success:
                logging.info("Instance soft rebooted successfully.")
                return self._host.get_guest(instance)
            else:
                logging.warning("Failed to reboot instance")
        reboot_success = self._hard_reboot(instance)
        if reboot_success:
            logging.info("Instance hard rebooted successfully.")
            return self._host.get_guest(instance)
        else:
            logging.warning("Failed to hard reboot instance")
            return

    # def reboot(self, instance, reboot_type='SOFT', network_info=None, disk_info=None):
    #     """Reboot a virtual machine, given an instance reference."""
    #     if reboot_type == 'SOFT':
    #         # NOTE(vish): This will attempt to do a graceful shutdown/restart.
    #         logging.info("begin soft reboot")
    #         try:
    #             soft_reboot_success = self._soft_reboot(instance)
    #         except libvirt.libvirtError as e:
    #             logging.error("Instance soft reboot failed: %s", e)
    #             soft_reboot_success = False
    #
    #         if soft_reboot_success:
    #             logging.info("Instance soft rebooted successfully.")
    #             return self._host.get_guest(instance)
    #         else:
    #             logging.warning("Failed to soft reboot instance. Trying hard reboot.")
    #             return
    #     return self._hard_reboot(instance, network_info, disk_info)

    def create_instance(self, instance, network_info, disk_info, power_on=True):
        """
        :param instance:
            {
                "uuid": "5fb01aa4-527b-400b-b9fc-8604913742b6",
                "name": "instance1",
                "ram": 1024,
                "vcpus": 2,
                "os_type": "linux",
                "spice_token": "5fb01aa4-527b-400b-b9fc-860491374212"
            }
        :param network_info:
            [
                {
                    "mac_addr": "fa:16:3e:8f:be:ff",
                    "bridge": "brqc74f456b-9f",
                    "port_id":"12fb86f2-b87b-44f0-b44e-38189314bdbd"
                }
            ]
        :param disk_info:
            [
                {"bus": "virtio", "dev": "vdb", "image_id": "8b4eaf72-1d78-11ea-b760-000c2902e179", ...},
                ...
            ]
        """
        if power_on:
            try:
                guest = self._host.get_guest(instance)
                state = guest.get_info().state
                if state == constants.DOMAIN_STATE['running']:
                    logging.info("domain is running, return")
                    return guest, False
                if state == constants.DOMAIN_STATE['paused']:
                    try:
                        guest.resume()
                    except:
                        pass
                    logging.info("domain is paused, resume and return")
                    return guest, False
            except Exception as e:
                logging.error("get guest state error:%s", e)

        for disk in disk_info:
            # if the disk not exists, create. if path attr exists,mean it already exists
            if constants.DISK_TYPE_DEFAULT == disk.get('type', 'disk') and not disk.get('path'):
                disk_file = self._prepare_disk(instance['uuid'], disk)
                # set the disk file path info
                disk['path'] = disk_file
            # write the network info to boot disk
            # if constants.SYSTEM_BOOT_INDEX == disk.get('boot_index'):
            #     NbdManager(instance).modify_guest_meta(disk['path'], network_info)
        try:
            guest = self._create_domain(instance, network_info, disk_info, power_on=power_on)
        except Exception as e:
            if isinstance(e, libvirt.libvirtError):
                # domain is already running
                if 55 == e.get_error_code():
                    logging.info("domain already running, skip")
                    guest = self._host.get_guest(instance)
                    return guest, False
                # 内存无法分配时有此错误
                if 1 == e.get_error_code():
                    pass
            try:
                self.destroy(instance)
            except:
                pass
            raise e
        return guest, True

    def delete_instance(self, instance):
        self.destroy(instance)

    def reset_instance(self, instance, images):
        logging.info("reset the template:%s", instance)
        try:
            self.change_cdrom_path(instance, '', attach=False)
        except:
            pass
        self._destroy(instance)
        for image in images:
            logging.info("delete the file:%s", image)
            base_path = image['base_path']
            instance_dir = os.path.join(base_path, instance['uuid'])
            filename = constants.DISK_FILE_PREFIX + image['image_id']
            source_file = os.path.join(instance_dir, filename)
            try:
                os.remove(source_file)
            except:
                pass
            backing_file = utils.get_backing_file(1, image['image_id'], base_path)
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', source_file, '-o',
                             'backing_file=%s' % backing_file, run_as_root=True)

    # def stop_restore_instance(self, instance, sys_restore, data_restore, timeout=120):
    #     if sys_restore:
    #         self._destroy(instance)
    #     else:
    #         self.power_off(instance, timeout=timeout)
    #     try:
    #         disk_config_path = os.path.join(constants.DEFAULT_CONFIGDRIVE_PATH, '%s.config' % instance['uuid'])
    #         os.remove(disk_config_path)
    #     except Exception as e:
    #         logging.error("delete configdrive file error:%s", e)
    #
    #     if sys_restore:
    #         # 系统盘是否还原
    #         instance_base = instance.get('sys_base', constants.DEFAULT_SYS_PATH)
    #         instance_path = os.path.join(instance_base, instance['uuid'])
    #         try:
    #             shutil.rmtree(instance_path)
    #         except OSError as e:
    #             logging.error('Failed to cleanup directory %(target)s: %(e)s',
    #                       {'target': instance_path, 'e': e})
    #     if data_restore:
    #         # 数据盘是否还原
    #         data_path = instance.get('data_base', constants.DEFAULT_DATA_PATH)
    #         data_path = os.path.join(data_path, instance['uuid'])
    #         try:
    #             shutil.rmtree(data_path)
    #         except OSError as e:
    #             logging.error('Failed to cleanup directory %(target)s: %(e)s',
    #                           {'target': data_path, 'e': e})

    def reboot_restore_instance(self, instance, network_info, disk_info, sys_restore, data_restore):
        # if sys_restore:
        #     self.stop_restore_instance(instance, sys_restore, data_restore)
        # else:
        if sys_restore:
            timeout = 0
        else:
            timeout = 120
        self.power_off(instance, timeout=timeout)
        return self.create_instance(instance, network_info, disk_info)

    def delete_template(self, instance, image_version, images):
        try:
            self.destroy(instance)
        except:
            pass
        if image_version > 0:
            for image in images:
                try:
                    logging.info("delete template version file:%s", image['image_path'])
                    os.remove(image['image_path'])
                except Exception as e:
                    logging.error("delete failed:%s", e)

    def list_instances(self):
        names = []
        for guest in self._host.list_guests(only_running=False):
            names.append(guest.name)

        return names

    def detach_template_cdrom(self, instance, configdrive=True):
        self.detach_cdrom(instance, configdrive)
        self.change_cdrom_path(instance, "", live=False)

    def change_cdrom_path(self, instance, path, attach=True, live=True):
        """
        :param path: the new path of cdrom
        :return:
        """
        logging.info("change instance:%s cdrom path to:%s", instance['uuid'], path)
        guest = self._host.get_guest(instance)
        devs = guest.get_all_devices(vconfig.LibvirtConfigGuestDisk)
        conf = None
        cdroms = list()
        for dev in devs:
            if 'cdrom' == dev.source_device:
                cdroms.append(dev)
        if cdroms:
            # 获取最后一个cdrom进行资源加载，第一个cdrom是用作IP设置
            conf = cdroms[0]
            for dev in cdroms:
                if dev.target_dev > conf.target_dev:
                    conf = dev
        # conf = None
        # for dev in devs:
        #     if 'hdb' == dev.target_dev:
        #         conf = dev
        #         break
        if conf:
            if attach:
                conf.source_path = path
            else:
                conf.source_path = ''
            conf.boot_order = None
            try:
                guest.change_cdrom_path(conf, True, live)
                logging.info("change cdrom path success")
            except Exception as e:
                logging.error("change cdrom path failed:%s", e)
                raise exception.ChangeCdromPathError(domain=instance['uuid'], error=str(e))
        else:
            raise exception.CdromNotExist(domain=instance['uuid'])

    def send_key(self, instance):
        guest = self._host.get_guest(instance)
        return guest.ctrl_alt_del()

    def autostart(self, instance, vif_info, start=True):
        """
        这种自动启动只针对已经有xml文件定义的虚拟机
        :param instance: 虚拟机信息，必须包含base_name参数
        :param vif_info: 虚拟机连接的网桥信息
        :param start: 是否设置为开机启动
        :return:
        """
        logging.info("set instance %s auto start:%s", instance, start)
        autostart_file = os.path.join(constants.QEMU_AUTO_START_DIR, instance['uuid'])
        if start:
            info = {
                "instance": instance,
                "vif_info": vif_info
            }
            with open(autostart_file, 'w') as fd:
                json.dump(info, fd, ensure_ascii=False)
        else:
            try:
                os.remove(autostart_file)
                logging.info("delete the autostart info file")
            except:
                pass
        # guest = self._host.get_guest(instance)
        # status = guest.set_autostart(start)
        # if -1 == status:
        #     raise exception.InstanceAutostartError(instance=instance['name'])

    def get_status(self, instance):
        """get the info of a instance."""
        logging.debug("get the instance:%s info", instance['name'])
        guest = self._host.get_guest(instance)
        # get state
        state = guest.get_power_state()
        port = self.get_guest_port(guest)
        result = {
            "state": state,
            "vnc_port": port['vnc_port'],
            "spice_port": port['spice_port']
        }
        return result

    def autostart_instance(self):
        # 已经设置在libvirtd后面启动，但是为了确保libvirtd已经加载了虚拟机信息，这里再sleep 1s
        time.sleep(1)
        autostart_dir = constants.QEMU_AUTO_START_DIR
        if os.path.exists(autostart_dir):
            for filename in os.listdir(autostart_dir):
                try:
                    logging.info("autostart instance:%s", filename)
                    file_path = os.path.join(autostart_dir, filename)
                    with open(file_path, 'r') as fd:
                        instance_info = json.load(fd)
                    instance = instance_info['instance']
                    try:
                        guest = self._host.get_guest(instance)
                        state = guest.get_info().state
                        if state == constants.DOMAIN_STATE['running']:
                            logging.info("instance already running, skip")
                            continue
                    except Exception as e:
                        logging.error("get guest state error:%s", e)
                        continue
                    vif_info = instance_info['vif_info']
                    network_info = [{"vif_info": vif_info}]
                    self.plug_vif(network_info)
                    self._create_guest(domain=guest._domain, power_on=True)
                except Exception as e:
                    logging.error("autostart instance %s failed:%s", filename, e)

    def attach_disk(self, instance, disk):
        guest = self._host.get_guest(instance)
        if constants.DISK_TYPE_DEFAULT == disk.get('type', 'disk') and not disk.get('path'):
            disk_file = self._prepare_disk(instance['uuid'], disk)
            # set the disk file path info
            disk['path'] = disk_file
        # 不加入boot_order
        disk['order'] = False
        storage_configs = self._get_guest_storage_config([disk])
        for config in storage_configs:
            try:
                guest.attach_device(config, True, False)
                logging.info("attach disk %s success", disk['path'])
            except Exception as e:
                logging.error("attach disk failed:%s", e)
                raise exception.ChangeCdromPathError(domain=instance['uuid'], error=str(e))

    def detach_disk(self, instance, base_path, disk_uuid, delete_base=False):
        logging.info("detach instance:%s, base_path:%s, disk_uuid:%s", instance['uuid'], base_path, disk_uuid)
        disk_base = os.path.join(base_path, instance['uuid'])
        disk_path = os.path.join(disk_base, constants.DISK_FILE_PREFIX + disk_uuid)
        guest = self._host.get_guest(instance)
        devs = guest.get_all_devices(vconfig.LibvirtConfigGuestDisk)
        conf = None
        for dev in devs:
            if disk_path == dev.source_path:
                conf = dev
                break
        if conf:
            try:
                guest.detach_device(conf, True, False)
                try:
                    os.remove(disk_path)
                    if delete_base:
                        backing_file = utils.get_backing_file(1, disk_uuid, base_path)
                        os.remove(backing_file)
                except:
                    pass
                logging.info("detach path %s success", disk_path)
            except Exception as e:
                logging.error("detach path failed:%s", e)
                raise exception.ChangeCdromPathError(domain=instance['uuid'], error=str(e))
        else:
            raise exception.CdromNotExist(domain=instance['uuid'])

    def detach_cdrom(self, instance, configdrive=True):
        logging.info("detach instance:%s, configdrive:%s", instance['uuid'], configdrive)
        guest = self._host.get_guest(instance)
        devs = guest.get_all_devices(vconfig.LibvirtConfigGuestDisk)
        conf = None
        cdroms = list()
        for dev in devs:
            if 'cdrom' == dev.source_device:
                cdroms.append(dev)
        if cdroms:
            # 获取最后一个cdrom
            conf = cdroms[0]
            for dev in cdroms:
                if dev.target_dev > conf.target_dev:
                    conf = dev
        if conf:
            try:
                guest.detach_device(conf, True, False)
                logging.info("detach path %s success", conf.target_dev)
            except Exception as e:
                logging.error("detach path failed:%s", e)
                raise exception.ChangeCdromPathError(domain=instance['uuid'], error=str(e))
        else:
            raise exception.CdromNotExist(domain=instance['uuid'])

    def set_vcpu_and_ram(self, instance, vcpu, ram):
        guest = self._host.get_guest(instance)
        try:
            config = vconfig.LibvirtConfigGuest()
            config.parse_str(guest._domain.XMLDesc(0))
            if vcpu:
                config.vcpus = int(vcpu)
                # 为了兼容之前没有cpu相关配置的虚拟机修改cpu个数
                if not hasattr(config, 'cpu') or not config.cpu:
                    config.cpu = vconfig.LibvirtConfigCPU()
                    config.cpu.mode = 'host-mode'
                    config.cpu.model = None
                if (vcpu & 1) == 0:
                    config.cpu.sockets = 2
                    config.cpu.cores = int(vcpu / 2)
                    config.cpu.threads = 1
                else:
                    config.cpu.sockets = 1
                    config.cpu.cores = vcpu
                    config.cpu.threads = 1
            if ram:
                config.memory = int(ram * constants.Ki)
            xml = config.to_xml()
            guest.create(xml, self._host)
            return True
        except Exception as e:
            raise e

    def check_ram_available(self, allocated):
        available = math.floor(psutil.virtual_memory().available/1024/1024/1024)
        logging.info("available ram:%s", available)
        if allocated > available:
            return False
        return True
