import os
import logging
import psutil
from yzy_compute import exception
from common import cmdutils, constants


class NFSManager(object):

    def _write_fstab(self, nfs_server, name):
        cmdutils.run_cmd("sed -i '/{}/d' /etc/fstab".format('nfs_' + name))
        cmdutils.run_cmd("echo {}   {}   nfs    defaults,nosuid,noexec,nodev,noatime,nodiratime,"
                         "vers=3,rsize=1048576,wsize=1048576   1 2 >> /etc/fstab".
                         format(nfs_server, constants.NFS_MOUNT_POINT_PREFIX + name))

    def mount_nfs(self, nfs_server, name):
        if not os.path.exists(constants.NFS_MOUNT_POINT_PREFIX + name):
            os.mkdir(constants.NFS_MOUNT_POINT_PREFIX + name)
        out, err = cmdutils.execute("mount", "-v", run_as_root=True, ignore_exit_code=True)
        if constants.NFS_MOUNT_POINT_PREFIX + name in out:
            logging.info("the device is in mount status, go on")
        else:
            out, err = cmdutils.execute('mount', '-t', 'nfs', '-o',
                                        'nosuid,noexec,nodev,noatime,nodiratime,vers=3,rsize=1048576,wsize=1048576',
                                        '{}'.format(nfs_server), '{}'.format(constants.NFS_MOUNT_POINT_PREFIX + name),
                                        run_as_root=True, ignore_exit_code=True)
            logging.info("mount {}, out:{} , err:{}".format(constants.NFS_MOUNT_POINT_PREFIX + name, out, err))
            if err:
                logging.error("mount nfs error:%s", err)
                return
        # 修改开机自动挂载
        self._write_fstab(nfs_server, name)
        disk_usage = psutil.disk_usage(constants.NFS_MOUNT_POINT_PREFIX + name)
        return disk_usage.used, disk_usage.free, disk_usage.total

    def umount_nfs(self, name):
        out, err = cmdutils.execute("mount", "-v", run_as_root=True, ignore_exit_code=True)
        if constants.NFS_MOUNT_POINT_PREFIX + name not in out:
            logging.info("the device is not in mount status, go on")
        else:
            out, err = cmdutils.execute("umount", "{}".format(constants.NFS_MOUNT_POINT_PREFIX + name),
                                        run_as_root=True, ignore_exit_code=True)
            if err:
                logging.error("umount nfs error:%s", err)
            else:  # 修改开机自动挂载
                cmdutils.run_cmd("sed -i '/{}/d' /etc/fstab".format('nfs_' + name))
        logging.info("umount {}, out:{} , err:{}".format(constants.NFS_MOUNT_POINT_PREFIX + name, out, err))