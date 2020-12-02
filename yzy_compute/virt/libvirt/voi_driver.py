import logging
import os
import re
import shutil
import functools
import uuid
from common import cmdutils
from common import constants
from yzy_compute import utils, exception
from common.config import SERVER_CONF as CONF
from .driver import LibvirtDriver
from . import config as vconfig
from . import storage_config as sconfig


libvirt = utils.import_module('libvirt')


class VoiLibvirtDriver(LibvirtDriver):

    def _prepare_iso_disk(self, disk):
        logging.info("prepare disk for instance, disk:%s", disk)
        # system disk and data disk in different position
        base_path = disk['base_path']
        # create the disk file
        disk_file = "%s/%s%s" % (base_path, constants.VOI_FILE_PREFIX, disk['uuid'])
        cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', disk_file, disk['size'], run_as_root=True)
        logging.info("create the disk %s success", disk_file)
        return disk_file

    def _prepare_voi_disk(self, disk):
        logging.info("prepare disk for voi, disk:%s", disk)
        # system disk and data disk in different position
        base_path = disk['base_path']
        backing_dir = os.path.join(base_path, constants.IMAGE_CACHE_DIRECTORY_NAME)
        if not os.path.isdir(backing_dir):
            utils.ensure_tree(backing_dir)
        version = disk.get('image_version', 0)
        dest_file_name = constants.VOI_BASE_PREFIX % str(version) + disk['uuid']
        if version > constants.IMAGE_COMMIT_VERSION:
            dest_file_name = constants.VOI_BASE_PREFIX % str(constants.IMAGE_COMMIT_VERSION) + disk['uuid']

        dest_file = os.path.join(backing_dir, dest_file_name)
        if os.path.exists(dest_file):
            logging.info("the file %s already exist", dest_file)
            disk_file = "%s/%s%s" % (base_path, constants.VOI_FILE_PREFIX, disk['uuid'])
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', disk_file, '-o',
                             'backing_file=%s' % dest_file, run_as_root=True)
            logging.info("create the diff disk %s success", disk_file)
            return disk_file
        # 第一步是生成base镜像文件
        # 终端样机上传
        if disk.get('upload', None):
            logging.info("move % to %s", disk['upload'], dest_file)
            shutil.move(disk['upload'], dest_file)
            logging.info("move the image %s to %s success", disk['upload'], dest_file)
        # 基于基础镜像创建
        elif disk.get('image_id', None):
            source_file = utils.get_backing_file(version, disk['image_id'], base_path)
            logging.info("copy %s to %s", source_file, dest_file)
            shutil.copy(source_file, dest_file)
            logging.info("copy the image %s to %s success", source_file, dest_file)
        # ISO全新创建
        else:
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', dest_file, disk['size'], run_as_root=True)
            logging.info("create the backing disk %s success", dest_file)
        # 第二步是建立差异磁盘文件
        disk_file = "%s/%s%s" % (base_path, constants.VOI_FILE_PREFIX, disk['uuid'])
        cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', disk_file, '-o',
                         'backing_file=%s' % dest_file, run_as_root=True)
        logging.info("create the diff disk %s success", disk_file)
        return disk_file

    def _configure_guest_by_virt_type(self, guest, virt_type, instance):
        if virt_type in ("kvm", "qemu"):
            guestarch = utils.canonicalize()
            if guestarch in (constants.I686, constants.X86_64):
                guest.sysinfo = self._get_guest_config_sysinfo(instance)
                guest.os_smbios = vconfig.LibvirtConfigGuestSMBIOS()
                guest.os_smbios.mode = 'emulate'
            guest.os_mach_type = constants.VOI_MACH_TYPE
            guest.os_loader_type = "pflash"
            guest.os_loader = "/usr/share/OVMF/OVMF_CODE.secboot.fd"
            guest.nvram = "/var/lib/libvirt/qemu/nvram/%s_VARS.fd" % instance['base_name']

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

    def _set_features(self, guest, os_type, virt_type):
        # if there is not acpi, the shutdown cmd could not work
        if virt_type not in ("lxc", "uml", "parallels", "xen"):
            guest.features.append(vconfig.LibvirtConfigGuestFeatureACPI())
            guest.features.append(vconfig.LibvirtConfigGuestFeatureAPIC())
            guest.features.append(vconfig.LibvirtConfigGuestFeatureVmport())

    def _get_guest_config(self, instance, network_info, disk_info):
        logging.info("_get_guest_config begin, instance:%s", instance['name'])
        virt_type = CONF.libvirt.virt_type
        guest = vconfig.LibvirtConfigGuest()
        guest.virt_type = virt_type
        guest.name = instance['base_name']
        guest.uuid = instance['uuid']
        guest.memory = int(instance['ram'] * constants.Ki)
        guest.vcpus = instance['vcpus']
        # guest.cpu = self._get_guest_cpu_config(guest.vcpus)

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

        # 鼠标不同步问题，uefi模式下才会有这个问题
        usbhost = vconfig.LibvirtConfigGuestUSBHostController()
        # uefi时，默认是 qemu-xhci，会导致鼠标没办法用
        usbhost.model = 'piix3-uhci'
        guest.add_device(usbhost)
        # usb tablet,解决鼠标漂移问题
        if CONF.vnc.enabled or (
                CONF.spice.enabled and not CONF.spice.agent_enabled):
            pointer = self._get_guest_usb_tablet()
            if pointer:
                guest.add_device(pointer)

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
            # instance_path = utils.get_instance_path(instance)
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

    def create_voi_template(self, instance, network_info, disk_info, power_on=True, iso=False, configdrive=True):
        for disk in disk_info:
            if constants.DISK_TYPE_DEFAULT == disk.get('type', 'disk') and not disk.get('path'):
                if iso:
                    disk_file = self._prepare_iso_disk(disk)
                else:
                    disk_file = self._prepare_voi_disk(disk)
                disk['path'] = disk_file
        try:
            guest = self._create_domain(instance, network_info, disk_info, configdrive=configdrive, power_on=power_on)
        except Exception as e:
            # domain is already running
            if isinstance(e, libvirt.libvirtError) and 55 == e.get_error_code():
                logging.info("domain already running, skip")
                guest = self._host.get_guest(instance)
                return guest, False
            try:
                self.destroy(instance)
            except:
                pass
            raise e
        return guest, True

    def cleanup(self, instance, destroy_disks=True):

        if destroy_disks:
            try:
                disk_config_path = os.path.join(constants.DEFAULT_CONFIGDRIVE_PATH, '%s.config' % instance['uuid'])
                token_file = os.path.join(constants.TOKEN_PATH, instance['uuid'])
                os.remove(token_file)
                logging.info("delete token file:%s", token_file)
                os.remove(disk_config_path)
                logging.info("delete configdrive file:%s", disk_config_path)
            except Exception as e:
                logging.error("delete configdrive file error:%s", e)

        self._undefine_domain(instance, support_uefi=True)

    def destroy(self, instance, destroy_disks=True):
        """when delete instance, it will be called"""
        self._destroy(instance)
        self.cleanup(instance, destroy_disks)

    def delete_voi_template(self, instance, images):
        try:
            self.destroy(instance)
        except:
            pass
        for image in images:
            try:
                logging.info("delete voi template file:%s", image['image_path'])
                if os.path.exists(image['image_path']):
                    os.remove(image['image_path'])
                # 删除种子
                torrent_path = image['image_path'] + ".torrent"
                if os.path.exists(torrent_path):
                    os.remove(torrent_path)
            except Exception as e:
                logging.error("delete failed:%s", e)

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
        if conf:
            if attach:
                conf.source_path = path
            else:
                conf.source_path = ''
            conf.boot_order = None
            try:
                guest.change_cdrom_path(conf, True, live)
                logging.info("change cdrom %s path success", conf.target_dev)
            except Exception as e:
                logging.error("change cdrom %s path failed:%s", conf.target_dev, e)
                raise exception.ChangeCdromPathError(domain=instance['uuid'], error=str(e))
        else:
            raise exception.CdromNotExist(domain=instance['uuid'])

    def save_template(self, version, images, is_upload=False):
        """
        :param version: the template version
        :param images: the template device info
            {
                "disk_file": "",
                "backing_file": "",
                "base_file": "",
                "commit_file": ""
            }
        :return:
        """
        for image in images:
            dest_base = os.path.join(image['base_path'], constants.IMAGE_CACHE_DIRECTORY_NAME)
            file_name = constants.VOI_FILE_PREFIX + image['image_id']
            source_file = os.path.join(image['base_path'], file_name)
            dest_file_name = constants.VOI_BASE_PREFIX % str(version) + image['image_id']
            # if version > constants.IMAGE_COMMIT_VERSION:
            #     dest_file_name = constants.VOI_BASE_PREFIX % str(constants.IMAGE_COMMIT_VERSION) + image['image_id']
            dest_file = os.path.join(dest_base, dest_file_name)
            logging.info("move %s to %s", source_file, dest_file)
            # if not is_upload:
            shutil.move(source_file, dest_file)
            # else:
            #     os.remove(source_file)

            # 保留2个版本, 0 , 1, 2
            if version > constants.IMAGE_COMMIT_VERSION:
                commit_file = os.path.join(dest_base, constants.VOI_BASE_PREFIX % str(constants.IMAGE_COMMIT_VERSION) +
                                           image['image_id'])
                if image['need_commit']:
                    logging.info("commit the diff file:%s", commit_file)
                    stdout, stderr = cmdutils.execute('qemu-img', 'commit', '-f', 'qcow2', commit_file, run_as_root=True)
                    if stderr:
                        raise exception.ImageCommitError(image=commit_file, error=stderr)

                    base_file = os.path.join(dest_base, constants.VOI_BASE_PREFIX % str(1) + image['image_id'])
                    # stdout, stderr = cmdutils.execute('qemu-img', 'rebase', '-u', '-b', base_file, dest_file, run_as_root=True)
                    # if stderr:
                    #     raise exception.ImageCommitError(image=commit_file, error=stderr)
                    try:
                        logging.info("delete the diff file after commit: %s" % commit_file)
                        os.remove(commit_file)
                        torrent_file = commit_file + ".torrent"
                        if os.path.exists(torrent_file):
                            os.remove(torrent_file)
                        base_torrent_file = base_file + ".torrent"
                        if os.path.exists(base_torrent_file):
                            os.remove(base_torrent_file)
                    except:
                        pass
                    # 需要修改backing_file
                    logging.info("rebase the dest_file: %s", dest_file)
                    stdout, stderr = cmdutils.execute('qemu-img', 'rebase', '-u', '-b', base_file, dest_file,
                                                      run_as_root=True)
                    if stderr:
                        raise exception.ImageRebaseError(image=commit_file, error=stderr)

                os.rename(dest_file, commit_file)
                dest_file = commit_file
                logging.info("merge the diff file end")
            else:
                if is_upload:
                    backing_file = constants.VOI_BASE_PREFIX % str(version - 1) + image['image_id']
                    # 需要修改backing_file
                    logging.info("version %s rebase the dest_file: %s", version, dest_file)
                    stdout, stderr = cmdutils.execute('qemu-img', 'rebase', '-u', '-b', backing_file, dest_file,
                                                      run_as_root=True)
                    if stderr:
                        raise exception.ImageRebaseError(image=dest_file, error=stderr)

            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', source_file, '-o',
                             'backing_file=%s' % dest_file, run_as_root=True)

            # else:
            #     cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', source_file, '-o',
            #                      'backing_file=%s' % dest_file, run_as_root=True)

    def detach_iso_template(self, instance, configdrive=True):
        self.detach_cdrom(instance, configdrive)
        self.change_cdrom_path(instance, "", live=False)

    def rollback(self, rollback_version, cur_version, images):
        if rollback_version != 0 and cur_version > constants.IMAGE_COMMIT_VERSION:
            rollback_version = 1
            cur_version = 2

        for image in images:
            file_name = constants.VOI_FILE_PREFIX + image['image_id']
            disk_file = os.path.join(image['base_path'], file_name)
            backing_file_name = constants.VOI_BASE_PREFIX % str(rollback_version) + image['image_id']
            backing_dir = os.path.join(image['base_path'], constants.IMAGE_CACHE_DIRECTORY_NAME)
            backing_file = os.path.join(backing_dir, backing_file_name)
            try:
                logging.info("delete file %s", disk_file)
                os.remove(disk_file)
            except:
                pass
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', disk_file, '-o',
                             'backing_file=%s' % backing_file, run_as_root=True)
            logging.info("rollback the version, image:%s", image)
            delete_file = os.path.join(backing_dir, constants.VOI_BASE_PREFIX % str(cur_version)
                                       + image['image_id'])
            try:
                logging.info("delete file %s", delete_file)
                os.remove(delete_file)
                # 删除种子文件
                torrent_file = delete_file + ".torrent"
                if os.path.exists(torrent_file):
                    os.remove(torrent_file)

                stdout, stderror = cmdutils.execute('qemu-img info %s' % disk_file,
                                                    shell=True, timeout=20, run_as_root=True)
                # 获取该盘的大小
                logging.info("qemu-img info execute end, stdout:%s, stderror:%s", stdout, stderror)
                current_size = int(re.search(r"virtual size: (\d+)G \((\d+) bytes\)", stdout).group(1))
                image["size"] = current_size
            except Exception as e:
                logging.error("", exc_info=True)
                pass

        return images

    def create_data_file(self, instance, disk, version):
        backing_dir = os.path.join(disk['base_path'], constants.IMAGE_CACHE_DIRECTORY_NAME)
        backing_file_name = constants.VOI_BASE_PREFIX % str(0) + disk['uuid']
        backing_file = os.path.join(backing_dir, backing_file_name)
        logging.info("create base file %s", backing_file)
        cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', backing_file, disk['size'], run_as_root=True)
        # 默认基础镜像
        diff_file = backing_file
        # 只保留两个版本
        if version <= constants.IMAGE_COMMIT_VERSION:
            for i in range(version):
                file_name = constants.VOI_BASE_PREFIX % str(i + 1) + disk['uuid']
                base_file_name = constants.VOI_BASE_PREFIX % str(i) + disk['uuid']
                diff_file = os.path.join(backing_dir, file_name)
                base_file = os.path.join(backing_dir, base_file_name)
                logging.info("create diff file %s, backing_file:%s", diff_file, base_file)
                cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', diff_file, '-o',
                                 'backing_file=%s' % base_file, run_as_root=True)
        else:
            file_name = constants.VOI_BASE_PREFIX % str(version - 1) + disk['uuid']
            base_file_name = constants.VOI_BASE_PREFIX % str(0) + disk['uuid']
            diff_file = os.path.join(backing_dir, file_name)
            base_file = os.path.join(backing_dir, base_file_name)
            logging.info("create diff file %s, backing_file:%s", diff_file, base_file)
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', diff_file, '-o',
                             'backing_file=%s' % base_file, run_as_root=True)
            file_name = constants.VOI_BASE_PREFIX % str(version) + disk['uuid']
            base_file_name = constants.VOI_BASE_PREFIX % str(version - 1) + disk['uuid']
            diff_file = os.path.join(backing_dir, file_name)
            base_file = os.path.join(backing_dir, base_file_name)
            logging.info("create diff file %s, backing_file:%s", diff_file, base_file)
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', diff_file, '-o',
                             'backing_file=%s' % base_file, run_as_root=True)
        logging.info("create base file end")
        # 下面是基于最后一个差异盘创建模板目前使用的差异盘
        disk_file_name = constants.VOI_FILE_PREFIX + disk['uuid']
        disk_file = os.path.join(disk['base_path'], disk_file_name)
        logging.info("create diff file %s, backing_file:%s", disk_file, diff_file)
        cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', disk_file, '-o',
                         'backing_file=%s' % diff_file, run_as_root=True)
        guest = self._host.get_guest(instance)
        disk['path'] = disk_file
        disk['order'] = False
        storage_configs = self._get_guest_storage_config([disk])
        for config in storage_configs:
            try:
                guest.attach_device(config, True, False)
                logging.info("attach disk %s success", disk['path'])
            except Exception as e:
                logging.error("attach disk failed:%s", e)
                raise exception.ChangeCdromPathError(domain=instance['uuid'], error=str(e))
        return True

    def create_share_disk(self, disk, version):
        backing_dir = os.path.join(disk['base_path'], constants.IMAGE_CACHE_DIRECTORY_NAME)
        backing_file_name = constants.VOI_SHARE_BASE_PREFIX % str(0) + disk['uuid']
        backing_file = os.path.join(backing_dir, backing_file_name)
        logging.info("create voi share disk base file %s", backing_file)
        disk_size = "%sG" % disk["size"]
        cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', backing_file, disk_size, run_as_root=True)
        # 默认基础镜像
        diff_file = backing_file
        # 只保留两个版本
        if version <= constants.IMAGE_COMMIT_VERSION:
            for i in range(version):
                file_name = constants.VOI_SHARE_BASE_PREFIX % str(i + 1) + disk['uuid']
                base_file_name = constants.VOI_SHARE_BASE_PREFIX % str(i) + disk['uuid']
                diff_file = os.path.join(backing_dir, file_name)
                base_file = os.path.join(backing_dir, base_file_name)
                logging.info("create share disk diff file %s, backing_file:%s", diff_file, base_file)
                cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', diff_file, '-o',
                                 'backing_file=%s' % base_file, run_as_root=True)
        else:
            file_name = constants.VOI_SHARE_BASE_PREFIX % str(version - 1) + disk['uuid']
            base_file_name = constants.VOI_SHARE_BASE_PREFIX % str(0) + disk['uuid']
            diff_file = os.path.join(backing_dir, file_name)
            base_file = os.path.join(backing_dir, base_file_name)
            logging.info("create share disk diff file %s, backing_file:%s", diff_file, base_file)
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', diff_file, '-o',
                             'backing_file=%s' % base_file, run_as_root=True)
            file_name = constants.VOI_SHARE_BASE_PREFIX % str(version) + disk['uuid']
            base_file_name = constants.VOI_SHARE_BASE_PREFIX % str(version - 1) + disk['uuid']
            diff_file = os.path.join(backing_dir, file_name)
            base_file = os.path.join(backing_dir, base_file_name)
            logging.info("create share disk diff file %s, backing_file:%s", diff_file, base_file)
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', diff_file, '-o',
                             'backing_file=%s' % base_file, run_as_root=True)
        logging.info("create voi share disk base file end")
        return True

    def delete_share_disk(self, disk, version):
        backing_dir = os.path.join(disk['base_path'], constants.IMAGE_CACHE_DIRECTORY_NAME)
        logging.info("delete voi share disk: %s, version: %s", disk, version )
        for i in range(int(version) + 1):
            file_name = constants.VOI_SHARE_BASE_PREFIX % str(i) + disk['uuid']
            file_path = os.path.join(backing_dir, file_name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

        logging.info("delete voi share disk base file end")
        return True

    def resize_disk(self, images):
        for image in images:
            base_path = image['base_path']
            image_file = os.path.join(base_path, constants.VOI_FILE_PREFIX + image['image_id'])
            try:
                # 先查出该盘的大小
                stdout, stderror = cmdutils.execute('qemu-img info %s' % image_file,
                                                    shell=True, timeout=20, run_as_root=True)
                logging.info("qemu-img info execute end, stdout:%s, stderror:%s", stdout, stderror)
                current_size = int(re.search(r"virtual size: (\d+)G \((\d+) bytes\)", stdout).group(1))
                logging.info("resize file %s", image_file)
                size = '+%sG' % (int(image['tag_size']) - current_size)
                cmdutils.execute('qemu-img', 'resize', image_file, size, run_as_root=True)
            except Exception as e:
                logging.error("resize image file failed:%s", e)
                raise exception.ImageResizeError(image=image_file, error=e)
        logging.info("resize image success")
        return True

    # def detach_disk(self, instance, base_path, disk_uuid, delete_base=False):
    #     logging.info("detach instance:%s, base_path:%s, disk_uuid:%s", instance['uuid'], base_path, disk_uuid)
    #     disk_path = os.path.join(base_path, constants.VOI_FILE_PREFIX + disk_uuid)
    #     guest = self._host.get_guest(instance)
    #     devs = guest.get_all_devices(vconfig.LibvirtConfigGuestDisk)
    #     conf = None
    #     for dev in devs:
    #         if disk_path == dev.source_path:
    #             conf = dev
    #             break
    #     if conf:
    #         try:
    #             guest.detach_device(conf, True, False)
    #             try:
    #                 os.remove(disk_path)
    #                 # if delete_base:
    #                 #     backing_file = utils.get_backing_file(1, disk_uuid, base_path)
    #                 #     os.remove(backing_file)
    #             except:
    #                 pass
    #             logging.info("detach path %s success", disk_path)
    #         except Exception as e:
    #             logging.error("detach path failed:%s", e)
    #             raise exception.ChangeCdromPathError(domain=instance['uuid'], error=str(e))
    #     else:
    #         raise exception.CdromNotExist(domain=instance['uuid'])

    def copy_images(self, images):
        images.sort(key=lambda x:x['image_path'])
        pre_image = None
        for image in images:
            try:
                logging.info("copy file from %s to %s", image['image_path'], image['dest_path'])
                shutil.copy(image['image_path'], image['dest_path'])
                if pre_image and pre_image["type"] == image["type"]:
                    backing_file = pre_image['dest_path']
                    dest_path = image['dest_path']
                    stdout, stderr = cmdutils.execute('qemu-img', 'rebase', '-u', '-b', backing_file, dest_path,
                                                      run_as_root=True)
                    if stderr:
                        raise exception.ImageRebaseError(image=dest_path, error=stderr)
                pre_image = image
            except IOError as e:
                logging.error("copy image failed:%s", e)
                raise exception.ImageCopyIOError(image['image_path'])
        logging.info("copy new image success")
        return True

    def convert(self, template):
        logging.info("start convert, source:%s, dest:%s", template['image_path'], template['new_path'])
        if template['need_convert']:
            logging.info("convert from %s to %s", template['image_path'], template['new_path'])
            cmdutils.execute('qemu-img', 'convert', '-f', 'qcow2', '-O', 'qcow2',
                             template['image_path'], template['new_path'], run_as_root=True)
        else:
            logging.info("generate base image from origin image")
            try:
                shutil.copy(template['image_path'], template['new_path'])
            except IOError as e:
                logging.error("copy image failed:%s", e)
                raise exception.ImageCopyIOError(template['image_path'])
        logging.info("generat new image success")
        return {'path': template['new_path']}

    def reset_instance(self, instance, images):
        logging.info("reset the vi template:%s", instance)
        try:
            self.change_cdrom_path(instance, '', attach=False)
        except:
            pass
        self._destroy(instance)
        for image in images:
            logging.info("delete the file:%s", image['image_path'])
            try:
                os.remove(image['image_path'])
            except:
                pass
            cmdutils.execute('qemu-img', 'create', '-f', 'qcow2', image['image_path'], '-o',
                             'backing_file=%s' % image['backing_path'], run_as_root=True)

    def create_storage_by_name(self, pool_name, path):
        result = self._host.get_storage_by_name(pool_name)
        if not result:
            xml = self._get_storage_xml(pool_name, path)
            self._host.create_storage(xml)
        else:
            logging.info("the storage pool already exist")
            if not result.isActive():
                result.create(libvirt.VIR_STORAGE_POOL_CREATE_WITH_BUILD)
            if not result.autostart():
                result.setAutostart(1)
        return True

    def _get_storage_xml(self, pool_name, path):
        conf = self._get_storage_config(pool_name, path)
        xml = conf.to_xml()
        logging.debug('End _get_storage_xml xml=%(xml)s', {'xml': xml})
        return xml

    def _get_storage_config(self, pool_name, target_path):
        logging.info("_get_storage_config begin, pool_name:%s, target_path:%s", pool_name, target_path)
        storage = sconfig.LibvirtConfigStorage()
        storage.name = pool_name
        storage.uuid = uuid.uuid1()
        storage.target_path = target_path
        logging.info("_get_storage_config end, pool_name:%s", pool_name)
        return storage

    def set_vcpu_and_ram(self, instance, vcpu, ram):
        guest = self._host.get_guest(instance)
        guest.set_vcpu_and_ram(vcpu, ram, True, True)

    def define_ha_voi_domain(self, xml_file, instance, network_info, disk_info, power_on=True, iso=False, configdrive=True):
        """启用HA时，在备控上定义VOI模板的虚拟机"""
        # for disk in disk_info:
        #     if constants.DISK_TYPE_DEFAULT == disk.get('type', 'disk') and not disk.get('path'):
        #         if iso:
        #             disk_file = self._prepare_iso_disk(disk)
        #         else:
        #             disk_file = self._prepare_voi_disk(disk)
        #         disk['path'] = disk_file
        try:
            guest = self._define_ha_voi_domain(xml_file, instance, network_info, disk_info, configdrive=configdrive, power_on=power_on)
        except Exception as e:
            # domain is already running
            if isinstance(e, libvirt.libvirtError) and 55 == e.get_error_code():
                logging.info("domain already running, skip")
                guest = self._host.get_guest(instance)
                return guest, False
            try:
                self.destroy(instance)
            except:
                pass
            raise e
        return guest, True

    def _define_ha_voi_domain(self, xml_file, instance, network_info, disk_info, configdrive=True, power_on=True):
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
            # instance_path = utils.get_instance_path(instance)
            if configdisk:
                disk_config_path = os.path.join(constants.DEFAULT_CONFIGDRIVE_PATH, '%s.config' % instance['uuid'])
                configdisk['path'] = disk_config_path
                logging.info("update configdrive device %s path to %s", configdisk['dev'], disk_config_path)
                gen_confdrive = functools.partial(self._create_configdrive, instance, network_info, disk_config_path)
        self.plug_vif(network_info)
        # xml = self._get_guest_xml(instance, network_info, disk_info)
        with open(xml_file, "r", encoding="utf8") as fp:
            xml = fp.read()
        if configdisk:
            guest = self._create_guest(xml, post_xml_callback=gen_confdrive, power_on=power_on)
        else:
            guest = self._create_guest(xml, power_on=power_on)
        return guest
