import os
import hashlib
import time
import logging
import netaddr
from common.http import HTTPClient
from common.config import FileOp
from common import constants, utils, cmdutils
from .image_data import ImageService
from yzy_compute.virt.libvirt.voi_driver import VoiLibvirtDriver


class NodeService(object):

    def __init__(self, **kwargs):
        self.endpoint = kwargs.get('endpoint', None)
        if self.endpoint:
            self.http_client = HTTPClient(self.endpoint, timeout=600)

    def ha_sync_voi(self, url, paths, voi_template_list=None, voi_ha_domain_info=None):
        """
        :param url:
        :param paths:
        :param voi_template_list: [
            {
              "disk_path": "/opt/slow/instances/voi-2f23d11d-4462-4a85-a5fd-80ce1b308b12",
              "image_path_list": [
                "/opt/slow/instances/_base/voi_0_2f23d11d-4462-4a85-a5fd-80ce1b308b12"
              ],
              "torrent_path_list": [
                "/opt/slow/instances/_base/voi_0_2f23d11d-4462-4a85-a5fd-80ce1b308b12.torrent"
              ]
            },
            {
              "disk_path": "/opt/slow/datas/voi-901b5c81-3eb6-4e53-8df7-cd01484d5c83",
              "image_path_list": [
                "/opt/slow/datas/_base/voi_0_901b5c81-3eb6-4e53-8df7-cd01484d5c83"
              ],
              "torrent_path_list": [
                "/opt/slow/datas/_base/voi_0_901b5c81-3eb6-4e53-8df7-cd01484d5c83.torrent"
              ]
            }
          ]
        :param voi_ha_domain_info
        :return:
        """
        logging.info("paths: %s, voi_template_list: %s, voi_ha_domain_info: %s", paths, voi_template_list, voi_ha_domain_info)
        # 下载VOI base盘、差分盘、实际启动盘、种子文件
        if voi_template_list:
            for image_path_dict in voi_template_list:
                if image_path_dict["download_base"]:
                    paths.extend(image_path_dict["image_path_list"])
                else:
                    paths.extend(image_path_dict["image_path_list"][1:])
                if image_path_dict.get("torrent_path_list", []):
                    paths.extend(image_path_dict["torrent_path_list"])
                paths.append(image_path_dict["disk_path"])
        # 下载VOI模板XML
        if voi_ha_domain_info:
            paths.extend([info["xml_file"] for info in voi_ha_domain_info])

        for path in paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logging.info("remove file:%s", path)
                except:
                    pass
            else:
                dir_path = os.path.dirname(path)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)

            self.download(url, path)

        # 建立base盘、差分盘、实际启动盘之间的关系链
        if voi_template_list:
            for image_path_dict in voi_template_list:
                # 如果VOI模板有差异盘，建立base盘、差分盘之间的关系链
                if len(image_path_dict["image_path_list"]) > 1:
                    image_path_dict["image_path_list"].sort()
                    pre_image = image_path_dict["image_path_list"][0]
                    for image in image_path_dict["image_path_list"][1:]:
                        stdout, stderr = cmdutils.execute('qemu-img', 'rebase', '-u', '-b', pre_image, image,
                                                          run_as_root=True)
                        if stderr:
                            logging.error("image[%s] rebase error: %s" % (image, stderr))
                        pre_image = image
                # 把VOI实际启动盘加入关系链
                stdout, stderr = cmdutils.execute(
                    'qemu-img', 'rebase', '-u', '-b', image_path_dict["image_path_list"][-1], image_path_dict["disk_path"],
                    run_as_root=True)
                if stderr:
                    logging.error("image[%s] rebase error: %s" % (image_path_dict["disk_path"], stderr))

        # 启用HA时，在备控上定义VOI模板的虚拟机
        if voi_ha_domain_info:
            for info in voi_ha_domain_info:
                logging.info("start define_ha_voi_domain: %s", info)
                guest, T_or_F = VoiLibvirtDriver().define_ha_voi_domain(**info)
                logging.info("define_ha_voi_domain: %s", T_or_F)

        return utils.build_result("Success")

    def ha_sync_file(self, url, paths, check_path=None):
        for _d in paths:
            dir_path = os.path.dirname(_d["path"])
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            if os.path.exists(_d["path"]):
                logging.info("file already exist on backup node, check md5: %s", _d["path"])
                md5_sum = hashlib.md5()
                with open(_d["path"], 'rb') as f:
                    while True:
                        chunk = f.read(constants.CHUNKSIZE)
                        if not chunk:
                            break
                        md5_sum.update(chunk)

                # 如果提供了md5值，则只下载md5值不同的文件；如果未提供，则直接删除已有文件，重新下载
                if _d.get("md5", ""):
                    if md5_sum.hexdigest() == _d["md5"]:
                        logging.info("file ok: %s", _d["path"])
                        continue
                    else:
                        logging.info("file need resync with old md5: %s", _d["path"])
                try:
                    os.remove(_d["path"])
                    logging.info("remove file: %s", _d["path"])
                except:
                    pass

            self.download(url, _d["path"])

        # 删掉指定目录下多余的文件
        if check_path:
            path_list = [_d["path"] for _d in paths]
            for file in os.listdir(check_path):
                file_path = os.path.join(check_path, file)
                if os.path.isfile(file_path):
                    if file_path not in path_list:
                        try:
                            os.remove(file_path)
                            logging.info("check dir path, remove file:%s", file_path)
                        except:
                            pass

    def download(self, url, path, md5=None):
        try:
            logging.info("download the file:%s", path)
            # the stream args must be true, otherwise the download will be failed
            url = '%s?path=%s' % (url, path)
            resp, image_chunks = self.http_client.get(url)
            if resp.headers.get('Content-Type') == 'application/json':
                logging.error("file not exist on master: %s", path)
                return
        except Exception as e:
            logging.error("sync error:%s", e)
            raise

        logging.info("data is none, open the dst_path:%s", path)
        data = open(path, 'wb')
        close_file = True

        if data is None:
            return image_chunks
        else:
            md5_sum = hashlib.md5()
            try:
                for chunk in image_chunks:
                    md5_sum.update(chunk)
                    data.write(chunk)
                if md5:
                    logging.info("check md5, source:%s, file:%s", md5, md5_sum.hexdigest())
                    if md5_sum.hexdigest() != md5:
                        logging.error("the source md5_sum:%s, the dest md5_sum:%s", md5, md5_sum.hexdigest())
                        raise Exception("the file md5 sum check failed")
            except Exception as ex:
                logging.error("Error writing to %(path)s: %(exception)s",
                              {'path': path, 'exception': ex})
                try:
                    os.remove(path)
                except:
                    pass
                raise ex
            finally:
                if close_file:
                    # Ensure that the data is pushed all the way down to
                    # persistent storage. This ensures that in the event of a
                    # subsequent host crash we don't have running instances
                    # using a corrupt backing file.
                    data.flush()
                    ImageService()._safe_fsync(data)
                    data.close()

    def get_data_sync_status(self, paths):
        for path in paths:
            if not os.path.exists(path):
                return False
        return True

    def set_ntp(self, server):
        chronyd_conf = [
            "driftfile /var/lib/chrony/drift",
            "makestep 1.0 3",
            "rtcsync",
            "logdir /var/log/chrony",
            "server %s iburst" % server
        ]
        FileOp(constants.CHRONYD_CONF, 'w').write_with_endline('\n'.join(chronyd_conf))
        logging.info("config ntp end:%s", chronyd_conf)
        cmdutils.run_cmd("timedatectl set-ntp yes")

    def config_ntp(self, ipaddr, netmask):
        is_mask, bits = utils.is_netmask(netmask)
        if not is_mask:
            bits = 24
        net = netaddr.IPNetwork(str(ipaddr) + '/' + str(bits))
        cidr = str(net.network) + '/' + str(net.prefixlen)
        chronyd_conf = [
            "server ntp1.aliyun.com",
            "server ntp2.aliyun.com",
            "server cn.ntp.org.cn",
            "server cn.pool.ntp.org",
            "driftfile /var/lib/chrony/drift",
            "makestep 1.0 3",
            "rtcsync",
            "allow %s" % cidr,
            "local stratum 10",
            "logdir /var/log/chrony"
        ]
        FileOp(constants.CHRONYD_CONF, 'w').write_with_endline('\n'.join(chronyd_conf))
        logging.info("config ntp server:%s", chronyd_conf)
        cmdutils.run_cmd("firewall-cmd --add-service=ntp --permanent")
        cmdutils.run_cmd("firewall-cmd --reload")
        cmdutils.run_cmd("timedatectl set-ntp yes")

    def chunks(self, file_obj, offset=None, chunk_size=64 * 2 ** 10):
        """

        :param file_obj:
        :param offset:
        :param chunk_size:
        :return:
        """
        chunk_size = chunk_size
        try:
            file_obj.seek(offset)
        except:
            pass

        while True:
            data = file_obj.read(chunk_size)
            if not data:
                break
            yield data

    def set_system_time(self, _datetime, time_zone):
        try:
            os.system('timedatectl set-timezone "{}"'.format(time_zone))
            os.system('date -s "{}"'.format(_datetime))
            os.system("hwclock -w")
        except Exception as e:
            logging.error("set system time failed:%s", e)
            return utils.build_result("OtherError")
        return utils.build_result("Success")

    def set_ntp_time(self, ntp_server):
        try:
            if not utils.icmp_ping("114.114.114.114", count=3):
                logging.info("Abnormal network link, set to local time")
                local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                os.system("date -s '{}'".format(local_time))
            for i in range(5):
                ret = os.system('ntpdate "{}"'.format(ntp_server))
                if ret == 0:
                    break
            else:
                logging.error("set ntp time error: Abnormal network environment")
                return utils.build_result("OtherError")
            os.system("hwclock -w")
            return utils.build_result("Success")
        except Exception as e:
            logging.error("set ntp time error:%s", e)
            return utils.build_result("OtherError")