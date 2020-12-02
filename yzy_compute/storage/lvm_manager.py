import re
import os
import math
import logging
import psutil
from yzy_compute import exception
from common import cmdutils, constants
from jetblack_lvm2 import LVM


class LVMManager(object):

    def get_pvs(self):
        pvs = list()
        with LVM() as lvm:
            for pv in lvm.physical_volumes:
                pvs.append(pv.name)
        logging.info("get pvs path:%s", pvs)
        return pvs

    def get_lv_mount_info(self, vg_name, lv_name):
        mount_info = dict()
        disk_parts = psutil.disk_partitions()
        for disk in disk_parts:
            if "%s-%s" % (vg_name, lv_name) == disk.device.split('/')[-1]:
                mount_info['mountpoint'] = disk.mountpoint
                mount_info['fstype'] = disk.fstype
        return mount_info

    def get_vgs(self):
        vgs = list()
        with LVM() as lvm:
            lvm.scan()
            for vg_name in lvm.list_vg_names():
                with lvm.vg_open(vg_name) as vg:
                    lvs = list()
                    pvs = list()
                    # 获取vg上的所有lv(如果一个VG上面没有LV，在这里遍历会导致flask的worker挂掉重启，所以这里没有lv时，不去获取)
                    if not vg.size == vg.free_size:
                        for lv in vg.logical_volumes:
                            # 过滤掉跟系统相关的lv
                            if lv.name in ['swap', 'home', 'root']:
                                continue
                            mount = self.get_lv_mount_info(vg_name, lv.name)
                            lvs.append({
                                "name": lv.name,
                                "size": math.floor(lv.size/1024/1024/1024),
                                "mount": mount
                            })
                    # 获取组成vg的所有pv
                    for pv in vg.physical_volumes:
                        pvs.append({
                            "name": pv.name,
                            "size": math.floor(pv.size/1024/1024/1024)
                        })
                    vg_info = {
                        "name": vg.name,
                        "size": math.floor(vg.size/1024/1024/1024),
                        "free_size": math.floor(vg.free_size/1024/1024/1024),
                        "lvs": lvs,
                        "pvs": pvs
                    }
                    vgs.append(vg_info)
        logging.info("get vgs return:%s", vgs)
        return vgs

    def get_mounted_part(self):
        mount_path = list()
        out, err = cmdutils.execute('mount', '-t', 'ext4', run_as_root=True, ignore_exit_code=True)
        for mount in out.split('\n'):
            if mount:
                path = mount.split()[0].strip()
                if not path.startswith("/dev/mapper"):
                    mount_path.append(path)
        out, err = cmdutils.execute('mount', '-t', 'xfs', run_as_root=True, ignore_exit_code=True)
        for mount in out.split('\n'):
            if mount:
                path = mount.split()[0].strip()
                if not path.startswith("/dev/mapper"):
                    mount_path.append(path)
        logging.info("get mounted path:%s", mount_path)
        return mount_path

    def extract_disk_name(self, inputstr):
        info = dict()
        mo = re.search(r'.*(?P<name>(scsi|ata)-[\w-]+) -> .*(?P<alias>s[\w-]+)', inputstr, re.MULTILINE)
        if mo:
            info = mo.groupdict('')
            return info
        return info

    def get_unused_part(self):
        out, err = cmdutils.execute('ls', '-l', '/dev/disk/by-id', run_as_root=True, ignore_exit_code=True)
        if err:
            logging.error("get device by-id failed:%s", err)
            return list()
        parts = list()
        for disk_single in out.split('\n'):
            if disk_single.strip() and -1 != disk_single.find('part'):
                ret_info = self.extract_disk_name(disk_single)
                if ret_info:
                    parts.append("/dev/%s" % ret_info['alias'])
        for disk_single in out.split('\n'):
            if disk_single.strip() and -1 == disk_single.find('part'):
                ret_info = self.extract_disk_name(disk_single)
                if ret_info.get('alias') and not ret_info['alias'].startswith('sr'):
                    for part in parts:
                        if ret_info['alias'] in part:
                            break
                    else:
                        parts.append("/dev/%s" % ret_info['alias'])
        logging.info("get all parts from by-id:%s", parts)
        pvs = self.get_pvs()
        mounted = self.get_mounted_part()
        # 过滤掉作为pv的
        for pv in pvs:
            if pv in parts:
                parts.remove(pv)
        # 过滤掉已经挂载使用的
        for mount in mounted:
            if mount in parts:
                parts.remove(mount)
        logging.info("get disk parts info:%s", parts)
        return parts

    def extend_vg(self, vg_name, paths):
        vgs = self.get_vgs()
        for vg in vgs:
            if vg_name == vg['name']:
                break
        else:
            logging.error("the vg %s is not exist", vg_name)
            raise exception.VGNotExists(vg=vg_name)
        pvs = self.get_pvs()
        for path in paths:
            if path in pvs:
                logging.info("the device %s is pv already, skip", path)
            else:
                out, err = cmdutils.execute("pvcreate", "-f", path, run_as_root=True, ignore_exit_code=True)
                if err:
                    logging.error("create pv failed:%s", err)
                    if "not found" in err:
                        err = "'%s'不存在" % path
                    raise exception.PVCreateError(pv=path, error=err)
            out, err = cmdutils.execute("vgextend", vg_name, path, run_as_root=True, ignore_exit_code=True)
            if err:
                logging.error("vgextend failed:%s", err)
                if "is already in volume group" in err:
                    err = "'%s'已经存在于卷组中" % path
                raise exception.VGExtendError(vg=vg_name, error=err)
            logging.info("device %s extend to vg %s success", path, vg_name)

    def extend_lv(self, mount_point, size):
        # 首先判断vg以及lv是否存在
        vgs = self.get_vgs()
        flag = False
        for vg in vgs:
            for lv in vg['lvs']:
                if lv['mount'].get('mountpoint', '') and lv['mount']['mountpoint'] == mount_point:
                    vg_name = vg['name']
                    lv_name = lv['name']
                    flag = True
                    break
            if flag:
                break
        else:
            raise exception.LVNotExists(lv=mount_point)
        flag = False
        for vg in vgs:
            for lv in vg['lvs']:
                # lv存在，还需要获取它的文件系统类型
                if lv_name == lv['name']:
                    fstype = lv['mount'].get('fstype', '')
                    if not fstype:
                        # 临时挂载一次获取文件系统类型
                        out, err = cmdutils.execute("mount", "/dev/%s/%s" % (vg_name, lv_name), "/mnt",
                                                    run_as_root=True, ignore_exit_code=True)
                        if err:
                            logging.error("mount lv error:%s", err)
                            raise exception.LVFormatGetFailed(lv=lv_name)
                        else:
                            fstype = self.get_lv_mount_info(vg_name, lv_name)['fstype']
                            out, err = cmdutils.execute("umount", "/dev/%s/%s" % (vg_name, lv_name),
                                                        run_as_root=True, ignore_exit_code=True)
                            logging.info("umount %s, out:%s , err:%s, fstype:%s", lv_name, out, err, fstype)
                    if not ('ext' in fstype or 'xfs' in fstype):
                        raise exception.UnSupportFileFormat(fstype=fstype)
                    flag = True
                    break
            if flag:
                # 判断卷组是否有空间
                if vg['free_size'] <= 0 or (size > 0 and vg['free_size'] < size):
                    logging.error("the vg has no enough size, lvextend failed")
                    raise exception.VGNoEnoughSize(vg=vg_name)
                break

        # size小于0，分配vg的所有剩余空间给lv
        if size < 0:
            out, err = cmdutils.execute("lvextend", "-l", "+100%FREE", "/dev/%s/%s" % (vg_name, lv_name),
                                        run_as_root=True, ignore_exit_code=True)
        else:
            out, err = cmdutils.execute("lvextend", "-L", "+%sG" % size, "/dev/%s/%s" % (vg_name, lv_name),
                                        run_as_root=True, ignore_exit_code=True)
        if err:
            logging.error("lvextend failed:%s", err)
            # if "not found" in err:
            #     err = "'%s'不存在" % path
            raise exception.LVExtendError(lv=lv_name, error=err)
        logging.info("extend lv end, next is sync the file system")
        # 文件系统同步，如果lv没挂载，则要使用-f选项强制执行
        if "ext" in fstype:
            out, err = cmdutils.execute("resize2fs", "-f", "/dev/%s/%s" % (vg_name, lv_name),
                                        run_as_root=True, ignore_exit_code=True)
        elif "xfs" in fstype:
            out, err = cmdutils.execute("xfs_growfs", "/dev/%s/%s" % (vg_name, lv_name),
                                        run_as_root=True, ignore_exit_code=True)
        if err:
            logging.error("lvextend failed when sync the file system:%s", err)
            raise exception.LVSyncFormatFailed(lv=lv_name)
        logging.info("lvextend success, vg:%s, lv:%s, size:%s", vg_name, lv_name, size)

    def create_lv(self, vg_name, lv_name, size):
        # 首先判断vg以及lv是否存在
        vgs = self.get_vgs()
        for vg in vgs:
            if vg_name == vg['name']:
                # 判断卷组是否有空间
                if vg['free_size'] <= 0 or (size > 0 and vg['free_size'] < size):
                    logging.error("the vg has no enough size, lvextend failed")
                    raise exception.VGNoEnoughSize(vg=vg_name)
                break
        else:
            logging.error("the vg %s is not exist", vg_name)
            raise exception.VGNotExists(vg=vg_name)
        for vg in vgs:
            for lv in vg['lvs']:
                if lv_name == lv['name']:
                    raise exception.LVAlreadyExists(lv=lv_name)
        try:
            # size小于0，分配vg的所有剩余空间给lv
            if size < 0:
                out, err = cmdutils.execute("lvcreate", "-n", lv_name, "-l", "100%FREE", vg_name,
                                            run_as_root=True, ignore_exit_code=True)
            else:
                out, err = cmdutils.execute("lvcreate", "-n", lv_name, "-L", "%sG" % size, vg_name,
                                            run_as_root=True, ignore_exit_code=True)
            if err:
                logging.error("lvcreate failed:%s", err)
                raise exception.LVCreateError(lv=lv_name, error=err)
            logging.info("create lv end, next is format the file system")
            # 默认格式化为ext4
            out, err = cmdutils.execute("mkfs.ext4", "/dev/%s/%s" % (vg_name, lv_name),
                                        run_as_root=True, ignore_exit_code=True)
            if err:
                logging.error("lv format file system error:%s", err)
                raise exception.LVSyncFormatFailed(lv=lv_name)
            mount_point = os.path.join(constants.LV_PATH_PREFIX, lv_name)
            if not os.path.exists(mount_point):
                os.makedirs(mount_point)
            out, err = cmdutils.execute("mount", "/dev/%s/%s" % (vg_name, lv_name), mount_point,
                                        run_as_root=True, ignore_exit_code=True)
            if err:
                logging.error("mount lv error:%s", err)
                raise exception.LVMountError(lv=lv_name, mount_point=mount_point, error=err)
            cmdutils.run_cmd("echo /dev/mapper/%s-%s %s   ext4    defaults   1 2 >> /etc/fstab"
                             % (vg_name, lv_name, mount_point))
            logging.info("lvcreate success, vg:%s, lv:%s, size:%s", vg_name, lv_name, size)
            return {"mount_point": mount_point}
        except Exception as e:
            logging.error("create lv failed:%s", e)
            cmdutils.execute("lvremove", "-f", vg_name, lv_name, run_as_root=True, ignore_exit_code=True)
            raise e

    def delete_lv(self, vg_name, lv_name):
        # 首先判断vg以及lv是否存在
        vgs = self.get_vgs()
        for vg in vgs:
            if vg_name == vg['name']:
                for lv in vg['lvs']:
                    # 判断lv是否存在
                    if lv_name == lv['name']:
                        break
                else:
                    raise exception.LVNotExists(lv=lv_name)
                break
        else:
            logging.error("the vg %s is not exist", vg_name)
            raise exception.VGNotExists(vg=vg_name)
        try:
            cmdutils.execute("umount", "/dev/%s/%s" % (vg_name, lv_name), run_as_root=True, ignore_exit_code=True)
            out, err = cmdutils.execute("lvremove", "-f", "/dev/%s/%s" % (vg_name, lv_name),
                                        run_as_root=True, ignore_exit_code=True)
            if err:
                logging.error("lvremove failed:%s", err)
                raise exception.LVRemoveError(lv=lv_name, error=err)
            cmdutils.run_cmd("sed -i '/%s-%s/d' /etc/fstab" % (vg_name, lv_name))
            logging.info("delete lv %s end", lv_name)
        except Exception as e:
            logging.error("delete lv failed:%s", e)
            raise e
