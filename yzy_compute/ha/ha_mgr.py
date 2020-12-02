import logging
import os
import shutil
import time
from configparser import ConfigParser
# from dynaconf import LazySettings
from common import constants, cmdutils
from common.utils import build_result, compute_post, get_error_result, icmp_ping, server_post
from common.http import HTTPClient
from common.config import SERVER_CONF
from yzy_compute.exception import EnableHaException, DisableHaException, SwitchHaMasterException


# settings = LazySettings(ROOT_PATH_FOR_DYNACONF=constants.BASE_DIR)
# logging.info('[%s]  [%s]  [%s]  [%s]' % (
#     settings.ROOT_PATH_FOR_DYNACONF, settings.SETTINGS_FILE_FOR_DYNACONF, settings.USER, settings.NAME))


class HaManager(object):

    def __init__(self):
        self.mysql_cnf = "/etc/my.cnf.d/mariadb-server.cnf"
        self.keep_cnf = "/etc/keepalived/keepalived.conf"
        self.ha_dir = "/usr/local"
        self.mysql_data_path = "/var/lib/mysql"
        # self.db_user = settings.get('USER', 'root')
        # self.db_pwd = settings.get('PASSWORD', '123qwe,.')
        # self.db_name = settings.get('NAME', 'yzy_kvm_db')
        self.db_user = self.read_config()['user']
        self.db_pwd = self.read_config()['password']
        self.db_name = self.read_config()['name']
        self.db_dump_file = os.path.join(self.ha_dir, "db_dump.sql")
        self.check_brain_file = os.path.join(self.ha_dir, "check.sh")
        self.notify_sh_file = os.path.join(self.ha_dir, "notify.sh")
        self.flag_file = os.path.join(self.ha_dir, "flag.sh")
        self.license_files = ["/usr/local/yzy/bin/license.a", "/usr/local/yzy/bin/license.b"]
        self.sql = "MASTER_HOST='%s', MASTER_USER='replicater', MASTER_PASSWORD='%s'" % ('%s', self.db_pwd)
        self.master_content = [
                "server-id=1",
                "log-bin=node1-bin",
                "relay_log=node1-relay-bin",
                "binlog-do-db=%s" % self.db_name,
                "log_slave_updates=1",
                "auto_increment_increment=2",
                "auto_increment_offset=1",
                "innodb_flush_log_at_trx_commit=1",
                "sync_binlog=1\n"
            ]
        self.backup_content = [
                "server-id=2",
                "log-bin=node2-bin",
                "relay_log=node2-relay-bin",
                "binlog-do-db=%s" % self.db_name,
                "log_slave_updates=1",
                "auto_increment_increment=2",
                "auto_increment_offset=2",
                "innodb_flush_log_at_trx_commit=1",
                "sync_binlog=1\n"
            ]
        self.keep_content = [
"""global_defs {
   script_user root
   enable_script_security
}

vrrp_script check_sh {
    script "%s"
    interval %s
}

vrrp_instance VI_1 {
    state BACKUP
    interface %s
    unicast_src_ip %s
    unicast_peer {
        %s
    }
    virtual_router_id 100
    priority %s
""",
"""    advert_int 5
    authentication {
        auth_type PASS
        auth_pass 1111
    }
    track_script {
        check_sh
    }
    notify_master "%s master"
    notify_backup "%s backup"
    notify_fault "%s backup"
    notify_stop "%s backup"
    virtual_ipaddress {
        %s dev %s
    }
}
"""
        ]

        self.check_brain_content = [
"""#!/bin/bash
for i in `seq 1 %d`
do
  ping -c 1 %s > /dev/null
  if [ $? -eq 0 ]; then
    exit 0
  fi
  sleep 1
done
exit 1
"""
        ]
        self.notify_sh_content = [
"""#!/bin/bash

notify_master() {
    passwd="%s"
    Master_Log_File=$(mysql -uroot -p$passwd -e "show slave status\G" | grep -w Master_Log_File | awk -F": " '{print $2}')
    Relay_Master_Log_File=$(mysql -uroot -p$passwd -e "show slave status\G" | grep -w Relay_Master_Log_File | awk -F": " '{print $2}')
    Read_Master_Log_Pos=$(mysql -uroot -p$passwd -e "show slave status\G" | grep -w Read_Master_Log_Pos | awk -F": " '{print $2}')
    Exec_Master_Log_Pos=$(mysql -uroot -p$passwd -e "show slave status\G" | grep -w Exec_Master_Log_Pos | awk -F": " '{print $2}')
    # 判断并等待slave同步数据完成
    i=1
    while true
    do

        if [ $Master_Log_File = $Relay_Master_Log_File ] && [ $Read_Master_Log_Pos -eq $Exec_Master_Log_Pos ]
        then
            echo "ok"
            break
        else
            sleep 1
            if [ $i -gt 60 ]
            then
                break
            fi
            let i++
            continue
        fi
    done
    
    systemctl enable --now redis
    systemctl enable --now ukey
    systemctl enable --now top_server
    systemctl enable --now torrent
    systemctl enable --now yzy-websockify
    systemctl enable --now yzy-scheduler
    systemctl enable --now yzy-server
    systemctl enable --now yzy-terminal
    systemctl enable --now yzy-terminal-agent
    systemctl enable --now yzy-web
    systemctl enable --now nginx
    # 使用server接口来进行数据库等修改
    sleep 2
    host_ip=`grep unicast_src_ip /etc/keepalived/keepalived.conf | awk '{print $2}'`
    curl -i -X POST -H "Content-type:application/json" -d '{"master_ip": "'$host_ip'"}' http://$host_ip:50000/api/v1/node/master
}

notify_backup() {
    if [ -f "%s" ]; then
        return
    fi
    systemctl disable --now nginx
    systemctl disable --now yzy-web
    systemctl disable --now yzy-terminal
    systemctl disable --now yzy-terminal-agent
    systemctl disable --now yzy-server
    systemctl disable --now yzy-scheduler
    systemctl disable --now yzy-websockify
    systemctl disable --now ukey
    systemctl disable --now top_server
    systemctl disable --now torrent
    systemctl disable --now redis
}

case "$1" in
  master)
    notify_master
    exit 0
  ;;
  backup)
    notify_backup
    exit 0
  ;;
  fault)
    notify_backup
    exit 0
  ;;
  stop)
    notify_backup
    exit 0
  ;;
esac
"""
        ]

    def read_config(self):
        info = dict()
        config = ConfigParser()
        config_path = os.path.join(constants.BASE_DIR, "config", ".secrets.toml")
        config.read(config_path)
        if config.has_section("default"):
            for value in config.items("default"):
                if 'user' == value[0]:
                    info['user'] = value[1].strip("\"'")
                elif 'password' == value[0]:
                    info['password'] = value[1].strip("\"'")
                elif 'name' == value[0]:
                    info['name'] = value[1].strip("\"'")
        if 'user' not in info:
            info['user'] = 'root'
        if 'password' not in info:
            info['password'] = '123qwe,.'
        if 'name' not in info:
            info['name'] = 'yzy_kvm_db'
        return info

    def update_conf(self, conf, conf_list, keyword=None):
        with open(conf, 'r') as fd:
            if keyword:
                content = fd.read()
                pos = content.find(keyword)
                if pos != -1:
                    content = content[:pos+len(keyword)] + '\n'.join(conf_list) + content[pos+len(keyword):]
                else:
                    raise Exception("can`t find keyword: %s" % keyword)
            else:
                content = '\n'.join(conf_list)
        with open(conf, 'w') as fd:
            fd.write(content)
            fd.flush()
            os.fsync(fd.fileno())
            fd.close()

        logging.info("file:%s, content:%s", conf, conf_list)

    def enable_ha(self, vip, netmask, sensitivity, quorum_ip, master_ip, backup_ip, master_nic, backup_nic, paths,
                  voi_template_list, voi_xlms, voi_ha_domain_info, post_data):
        try:
            # TODO: 检查备控磁盘空间是否足够（db_dump_file、VOI模板、ISO库、数据库备份文件）
            # 1、在/etc/my.cnf.d/mariadb-server.cnf的[mysqld]区域增加7个参数**
            self._update_conf(self.mysql_cnf, self.master_content, keyword="[mysqld]\n")

            # 2、关闭mariadb服务，删除原有binlog日志，然后再启动mariadb
            # 3、设置主从复制账户
            # 4、导出已有数据，其中包含了二进制日志文件和位置， 然后去掉文件中创建表的AUTO_INCREMENT
            self._run_cmd("systemctl stop mariadb", EnableHaException)
            self.del_binlog(self.mysql_data_path)
            master_cmd = [
                "systemctl start mariadb",
                "mysql -u{user} -p{pwd} -e \"GRANT REPLICATION SLAVE ON *.* TO 'replicater'@'%' IDENTIFIED BY '{pwd}';"
                "flush privileges;\"".format(user=self.db_user, pwd=self.db_pwd),
                "mysqldump -u{user} -p{pwd} --master-data=1 --databases {db} > {file}".format(
                    user=self.db_user, pwd=self.db_pwd, db=self.db_name, file=self.db_dump_file),
                "sed -i 's#AUTO_INCREMENT=[0-9]*##g' %s" % self.db_dump_file
            ]
            for cmd in master_cmd:
                self._run_cmd(cmd, EnableHaException)

            # 5、在导出sql文件中加入主控IP和复制账户信息
            self._update_conf(self.db_dump_file, [self.sql % master_ip + ', '], keyword="CHANGE MASTER TO ")

            # 通知备控5：下载sql、授权文件、VOI模板的base盘、差异盘、种子文件、XML文件，并在备控上定义模板的虚拟机
            self._notify_backup_sync(master_ip, backup_ip, [self.db_dump_file] + self.license_files + paths,
                                     voi_template_list=voi_template_list, voi_ha_domain_info=voi_ha_domain_info)
            self._remove_file(self.db_dump_file)

            # 通知备控123468：配置mysql和keepalived
            rep_json = self._notify_backup_config(vip, netmask, sensitivity, quorum_ip, master_ip, backup_ip, backup_nic)
            logging.info("_notify_backup_config rep_json: %s", rep_json)
            log_file = rep_json['data'].get('log_file', '')
            log_pos = rep_json['data'].get('log_pos', '4')

            # 6、配置主从复制，需要配置pos，否则在从库进行数据导入，会生成Binlog，这边启动slave线程后，会重复调用导致出错
            # 7、启动slave线程
            master_cmd = [
                "mysql -u{user} -p{pwd} -e \"CHANGE MASTER TO MASTER_HOST='{b_ip}', MASTER_USER='replicater', "
                "MASTER_PASSWORD='{pwd}', MASTER_LOG_FILE='{file}', MASTER_LOG_POS={pos};\"".
                    format(user=self.db_user, pwd=self.db_pwd, b_ip=backup_ip, file=log_file, pos=log_pos),
                "mysql -u{user} -p{pwd} -e \"start slave;\"".format(user=self.db_user, pwd=self.db_pwd)
            ]
            for cmd in master_cmd:
                self._run_cmd(cmd, EnableHaException)

            # 8、配置/etc/keepalived/keepalived.conf文件、check.sh脚本（仲裁IP，敏感度）、notify.sh脚本、flag文件
            # flag文件用于标记本次keepalived启动是初次启动，从而避免先停主控服务再启
            master_content = [
                self.keep_content[0] % (self.check_brain_file, sensitivity + 2, master_nic, master_ip, backup_ip, 100),
                "    nopreempt\n",
                self.keep_content[1] % (self.notify_sh_file, self.notify_sh_file, self.notify_sh_file, self.notify_sh_file,
                                        '%s/%s' % (vip, self._exchange_mask(netmask)), master_nic)
            ]
            self._update_conf(self.keep_cnf, master_content)
            self._update_conf(self.check_brain_file, [self.check_brain_content[0] % (sensitivity, quorum_ip)])
            self._update_conf(self.notify_sh_file, [self.notify_sh_content[0] % (self.db_pwd, self.flag_file)])
            self._update_conf(self.flag_file, ["enable HA"])

            # 9、启动keepalived服务，注意必须先启主控的，VIP才能绑在主控上
            master_cmd = [
                "chmod +x %s" % self.check_brain_file,
                "chmod +x %s" % self.notify_sh_file,
                "systemctl enable --now keepalived"
            ]
            for cmd in master_cmd:
                self._run_cmd(cmd, EnableHaException)

            # 通知备控79：启动keepalived
            self._notify_backup_start(backup_ip)

            # 检查主控上是否有VIP
            self._check_vip(5, vip)

            # 删除flag文件
            self._remove_file(self.flag_file)
            ret = get_error_result()
        except Exception as e:
            logging.exception(str(e), exc_info=True)
            self.disable_ha(master_ip, backup_ip, paths, voi_template_list, voi_xlms, post_data)
            ret = get_error_result("EnableHAError")
        return ret

    def config_backup(self, vip, netmask, sensitivity, quorum_ip, master_ip, backup_ip, backup_nic):
        try:
            # 1、在/etc/my.cnf.d/mariadb-server.cnf的[mysqld]区域增加7个参数**
            self._update_conf(self.mysql_cnf, self.backup_content, keyword="[mysqld]\n")

            # 2、先清空备控节点的所有mysql数据，然后启动mariadb服务
            self.del_file(self.mysql_data_path)
            self._run_cmd("systemctl enable --now mariadb", EnableHaException)

            # 3、设置mysql的root账户密码（从未做过HA的计算节点，mysql无密码；已做过HA的计算节点，mysql有密码）
            try:
                code, out = cmdutils.run_cmd("mysql -u{user} -e \"ALTER USER 'root'@'localhost' IDENTIFIED BY '{pwd}';\"".format(
                user=self.db_user, pwd=self.db_pwd))
            except Exception:
                pass

            # 4、设置主从复制账户
            self._run_cmd("mysql -u{user} -p{pwd} -e \"GRANT REPLICATION SLAVE ON *.* TO 'replicater'@'%' IDENTIFIED BY '{pwd}';"
                "flush privileges;\"".format(user=self.db_user, pwd=self.db_pwd), EnableHaException)

            # 6、导入数据，其中包含了配置主从复制的语句
            self._run_cmd("mysql -u{user} -p{pwd} < {file}".format(
                user=self.db_user, pwd=self.db_pwd, file=self.db_dump_file), EnableHaException)
            time.sleep(2)
            code, out = self._run_cmd("mysql -u{user} -p{pwd} -e \"show master status;\"".format(
                user=self.db_user, pwd=self.db_pwd), EnableHaException)
            log_file = out.split('\t')[-4].split('\n')[-1]
            log_pos = out.split('\t')[-3]
            self._remove_file(self.db_dump_file)
            self._run_cmd("mysql -u{user} -p{pwd} -e \"start slave;\"".format(user=self.db_user, pwd=self.db_pwd),
                          EnableHaException)
            # 临时方案，开启slave后给一定时间进行同步，后期可以改成获取同步状态
            time.sleep(3)
            # 8、配置/etc/keepalived/keepalived.conf文件和check.sh脚本（仲裁IP，敏感度）、notify.sh脚本
            backup_content = [
                self.keep_content[0] % (self.check_brain_file, sensitivity + 2, backup_nic, backup_ip, master_ip, 90),
                self.keep_content[1] % (self.notify_sh_file, self.notify_sh_file, self.notify_sh_file, self.notify_sh_file,
                                        '%s/%s' % (vip, self._exchange_mask(netmask)), backup_nic)
            ]
            self._update_conf(self.keep_cnf, backup_content)
            self._update_conf(self.check_brain_file, [self.check_brain_content[0] % (sensitivity, quorum_ip)])
            self._update_conf(self.notify_sh_file, [self.notify_sh_content[0] % (self.db_pwd, self.flag_file)])

            ret = get_error_result(data={"log_file": log_file, "log_pos": log_pos})
        except Exception as e:
            logging.exception(str(e), exc_info=True)
            ret = get_error_result("ConfigBackupHAError")
        return ret

    def start_backup(self):
        try:
            # 9、启动keepalived服务，注意必须后启备控的，VIP才能绑在主控上
            backup_cmd = [
                "chmod +x %s" % self.check_brain_file,
                "chmod +x %s" % self.notify_sh_file,
                # "mysql -u{user} -p{pwd} -e \"start slave;\"".format(user=self.db_user, pwd=self.db_pwd),
                "systemctl enable --now keepalived"
            ]
            for cmd in backup_cmd:
                self._run_cmd(cmd, EnableHaException)

            ret = get_error_result()
        except Exception as e:
            logging.exception(str(e), exc_info=True)
            ret = get_error_result("StartBackupHAError")
        return ret

    def disable_ha(self, vip_host_ip, peer_host_ip, paths, voi_template_list=None, voi_xlms=None, post_data=None):
        try:
            # 先停peer_host，后停本地vip_host
            self._disable_backup(peer_host_ip, paths, voi_template_list, voi_xlms)
            self._disable_master(vip_host_ip, post_data)
            ret = get_error_result()
        except Exception as e:
            logging.exception(str(e), exc_info=True)
            ret = get_error_result("DisableHAError")
        return ret

    def _disable_master(self, master_ip, post_data=None):
        logging.info("start disable_master")
        # 1、在/etc/my.cnf.d/mariadb-server.cnf删除7个参数**
        self._update_conf_del(self.mysql_cnf, self.master_content + self.backup_content)

        # flag文件用于标记本次keepalived停止是禁用停止，从而避免先停主控服务再启
        self._update_conf(self.flag_file, ["disable HA"])

        # 2、禁用keepalived服务
        # 3、停止slave线程、删除所有复制连接参数、重置bin_log、删除主从复制账户
        # 4、重启mariadb服务
        master_cmd = [
            "systemctl disable --now keepalived",
            "mysql -u{user} -p{pwd} -e \"STOP SLAVE;\"".format(user=self.db_user, pwd=self.db_pwd),
            "mysql -u{user} -p{pwd} -e \"RESET SLAVE ALL;\"".format(user=self.db_user, pwd=self.db_pwd),
            "mysql -u{user} -p{pwd} -e \"RESET MASTER;\"".format(user=self.db_user, pwd=self.db_pwd),
            "mysql -u{user} -p{pwd} -e \"DROP USER IF EXISTS 'replicater'@'%';\"".format(user=self.db_user,
                                                                                         pwd=self.db_pwd),
            "systemctl restart mariadb"
        ]
        for cmd in master_cmd:
            self._run_cmd(cmd)

        # 5、删除keepalived配置文件、相关sh文件、flag文件等
        for file in [self.keep_cnf, self.check_brain_file, self.notify_sh_file, self.db_dump_file, self.flag_file]:
            self._remove_file(file)

        # 清除可能残留的bin_log文件
        self.del_binlog(self.mysql_data_path)

        # 请求server端,变更主控IP
        if post_data:
            ret = server_post('/node/update_ip', post_data)
            logging.info("ret：%s", ret)

        logging.info("disable_master %s success" % master_ip)

    def del_binlog(self, filepath):
        # 删除binlog
        for file in os.listdir(filepath):
            file_path = os.path.join(filepath, file)
            if os.path.isfile(file_path):
                if "master.info" == file or "relay-log.info" == file or \
                        file.startswith("node1-") or file.startswith("node2-"):
                    try:
                        os.remove(file_path)
                    except:
                        pass

    def del_file(self, filepath):
        for file in os.listdir(filepath):
            file_path = os.path.join(filepath, file)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)

    def _disable_backup(self, backup_ip, paths, voi_template_list=None, voi_xlms=None):
        # 备控1234
        _data = {
            "command": "disable_backup",
            "handler": "HaHandler",
            "data": {
                "paths": paths,
                "voi_template_list": voi_template_list,
                "voi_xlms": voi_xlms
            }
        }
        rep_json = compute_post(backup_ip, _data)
        ret_code = rep_json.get("code", -1)
        if ret_code != 0:
            logging.error("disable_backup failed in compute_node: %s" % rep_json['msg'])
            # raise DisableHaException("disable_backup failed in compute_node: %s" % rep_json['msg'])
        logging.info("disable_backup in compute_node %s success" % backup_ip)

    def execute_disable_backup(self, paths, voi_template_list=None, voi_xlms=None):
        logging.info("start execute_disable_backup")
        # 1、在/etc/my.cnf.d/mariadb-server.cnf删除7个参数**
        self._update_conf_del(self.mysql_cnf, self.master_content + self.backup_content)

        # 2、禁用keepalived服务
        # 3、停止slave线程、删除所有复制连接参数、重置bin_log、删除主从复制账户
        # 4、禁用mariadb服务
        master_cmd = [
            "systemctl disable --now keepalived",
            "mysql -u{user} -p{pwd} -e \"STOP SLAVE;\"".format(user=self.db_user, pwd=self.db_pwd),
            "mysql -u{user} -p{pwd} -e \"RESET SLAVE ALL;\"".format(user=self.db_user, pwd=self.db_pwd),
            "mysql -u{user} -p{pwd} -e \"RESET MASTER;\"".format(user=self.db_user, pwd=self.db_pwd),
            "mysql -u{user} -p{pwd} -e \"DROP USER IF EXISTS 'replicater'@'%';\"".format(user=self.db_user,
                                                                                         pwd=self.db_pwd),
            "systemctl disable --now mariadb",
        ]
        for cmd in master_cmd:
            self._run_cmd(cmd)

        # 删除VOI模板的basepan、差异盘、种子文件、XML
        voi_files = list()
        if voi_template_list:
            for image_path_dict in voi_template_list:
                voi_files.append(image_path_dict["disk_path"])
                voi_files.extend(image_path_dict["image_path_list"])
                voi_files.extend(image_path_dict["torrent_path_list"])
        if voi_xlms:
            voi_files.extend(voi_xlms)
        logging.debug("voi_files: %s", voi_files)

        # 5、删除keepalived配置文件、相关sh文件、授权文件、ISO库、数据库备份文件等
        for file in [self.keep_cnf, self.check_brain_file, self.notify_sh_file, self.db_dump_file,
                     self.flag_file] + self.license_files + paths + voi_files:
            self._remove_file(file)

        # 清空mysql的data_dir
        self.del_file(self.mysql_data_path)
        logging.info("finish execute_disable_backup success")
        return get_error_result()

    def switch_ha_master(self, new_vip_host_ip, vip):
        # 重启vip_host（本节点）上的keepalived服务，vip将自动切换至new_vip_host
        self._run_cmd("systemctl restart keepalived", SwitchHaMasterException)
        self._notify_new_vip_host_check(new_vip_host_ip, vip)
        logging.info("switch master to new_vip_host_ip %s success" % new_vip_host_ip)
        return get_error_result()

    def check_vip(self, vip):
        try:
            self._check_vip(5, vip)
            ret = get_error_result()
        except Exception as e:
            logging.exception(str(e), exc_info=True)
            ret = get_error_result("SwitchHaMasterError")
        return ret

    def check_backup_ha_status(self, quorum_ip, sensitivity, paths):
        try:
            code, out = cmdutils.run_cmd("systemctl status keepalived", ignore_log=True)
            if code != 0 or "active (running)" not in out:
                keepalived_status = constants.HA_STATUS_FAULT
                logging.error("keepalived not running")
            else:
                keepalived_status = constants.HA_STATUS_NORMAL

            if quorum_ip:
                if not icmp_ping(quorum_ip, timeout=1, count=sensitivity):
                    quorum_ip_status = constants.HA_STATUS_FAULT
                    logging.error("ping quorum_ip[%s] failed" % quorum_ip)
                else:
                    quorum_ip_status = constants.HA_STATUS_NORMAL
            else:
                quorum_ip_status = constants.HA_STATUS_UNKNOWN

            code, out = cmdutils.run_cmd("mysql -u{user} -p{pwd} -e \"SHOW SLAVE STATUS\G;\" |grep \"Error \"".format(
                user=self.db_user, pwd=self.db_pwd), ignore_log=True)
            if out:
                mysql_slave_status = constants.HA_STATUS_FAULT
                logging.error("mysql slave status error: %s", out)
            else:
                mysql_slave_status = constants.HA_STATUS_NORMAL

            file_sync_status = constants.HA_STATUS_NORMAL
            for path in paths:
                if not os.path.exists(path):
                    file_sync_status = constants.HA_STATUS_FAULT
                    break

            ret = get_error_result("Success", data=[keepalived_status, quorum_ip_status, mysql_slave_status, file_sync_status])
        except Exception as e:
            logging.exception(str(e), exc_info=True)
            ret = get_error_result("OtherError")
        return ret

    # def _download(self, master_ip, url, file_path):
    #     try:
    #         bind = SERVER_CONF.addresses.get_by_default('compute_bind', '')
    #         if bind:
    #             port = bind.split(':')[-1]
    #         else:
    #             port = constants.COMPUTE_DEFAULT_PORT
    #         http_client = HTTPClient(endpoint="http://%s:%s" % (master_ip, port))
    #         url = '%s?file_path=%s' % (url, file_path)
    #         logging.info("download url %s" % url)
    #         resp, package_chunks = http_client.get(url)
    #         return package_chunks
    #     except Exception as e:
    #         logging.error("download file %s error: %s", (file_path, str(e)))
    #         raise

    def _update_conf(self, conf, conf_list, keyword=None):
        line_index = -1
        content = ''
        if keyword:
            with open(conf, 'r') as fd:
                lines = fd.readlines()
                for line_str in lines:
                    if line_str.startswith(keyword):
                        line_index = lines.index(line_str)
                        content = line_str[:len(keyword)] + '\n'.join(conf_list) + line_str[len(keyword):]
                        break
                if line_index == -1:
                    raise Exception("can`t find keyword: %s" % keyword)
                lines[line_index] = content
        else:
            lines = conf_list
        with open(conf, 'w') as fd:
            fd.writelines(lines)
            fd.flush()
            os.fsync(fd.fileno())
            fd.close()

        logging.info("file:%s, content:%s" % (conf, conf_list))

    def _run_cmd(self, cmd_str, exception=None):
        code, out = cmdutils.run_cmd(cmd_str)
        if exception and code != 0:
            raise exception(error=out)
        return code, out

    def _exchange_mask(self, mask):
        """
        转换子网掩码格式
        """

        # 计算二进制字符串中 '1' 的个数
        count_bit = lambda bin_str: len([i for i in bin_str if i == '1'])

        # 分割字符串格式的子网掩码为四段列表
        mask_splited = mask.split('.')

        # 转换各段子网掩码为二进制, 计算十进制
        mask_count = [count_bit(bin(int(i))) for i in mask_splited]

        return sum(mask_count)

    def _check_vip(self, interval, vip):
        for i in range(3 * interval):
            time.sleep(3)
            code, out = cmdutils.run_cmd("ip addr |grep {vip}".format(vip=vip), ignore_log=True)
            if code == 0 and out:
                return True
        raise EnableHaException("check vip timeout")

    def _update_conf_del(self, conf, conf_list):
        del_content = list()
        with open(conf, 'r') as fd:
            lines = fd.readlines()
            for line_str in conf_list:
                if not line_str.endswith("\n"):
                    line_str += "\n"
                if line_str in lines:
                    lines.remove(line_str)
                    del_content.append(line_str)
            # if not del_content:
            #     raise DisableHaException("nothing to delete")
            # elif len(del_content) != 7:
            #     raise DisableHaException("mysql conf deleted lines != 7")
            # else:
            #     pass

        if del_content:
            with open(conf, 'w') as fd:
                fd.writelines(lines)
                fd.flush()
                os.fsync(fd.fileno())
                fd.close()

        logging.info("file: %s, deleted content: %s" % (conf, del_content))

    def _remove_file(self, file_path):
        try:
            os.remove(file_path)
            logging.info("remove %s", file_path)
        except Exception as e:
            logging.error("remove %s failed: %s", (file_path, str(e)))
            # raise DisableHaException(error=str(e))

    # def _start_services(self, vip_host_ip):
    #     services = ["redis", "ukey", "top_server", "torrent", "yzy-server", "yzy-terminal", "yzy-terminal-agent", "yzy-web", "nginx"]
    #     all_cmd = ["systemctl enable --now %s" % s for s in services]
    #     for cmd in all_cmd:
    #         self._run_cmd(cmd)
    #     logging.info("start_services in %s success" % vip_host_ip)

    # def _start_services_backup(self, backup_ip):
    #     # 备控1234
    #     _data = {
    #         "command": "start_services",
    #         "handler": "HaHandler",
    #         "data": {
    #         }
    #     }
    #     rep_json = compute_post(backup_ip, _data)
    #     ret_code = rep_json.get("code", -1)
    #     if ret_code != 0:
    #         logging.error("disable_backup failed in compute_node: %s" % rep_json['msg'])
    #         raise Exception("disable_backup failed in compute_node: %s" % rep_json['msg'])
    #     logging.info("disable_backup in compute_node %s success" % backup_ip)

    def _notify_backup_sync(self, master_ip, backup_ip, paths, voi_template_list=None, voi_ha_domain_info=None):
        bind = SERVER_CONF.addresses.get_by_default('server_bind', '')
        if bind:
            port = bind.split(':')[-1]
        else:
            port = constants.SERVER_DEFAULT_PORT
        endpoint = "http://%s:%s" % (master_ip, port)
        # 同步sql和授权文件
        command_data = {
            "command": "ha_sync_voi",
            "handler": "NodeHandler",
            "data": {
                "url": constants.HA_SYNC_URL,
                "endpoint": endpoint,
                "paths": paths,
                "voi_template_list": voi_template_list,
                "voi_ha_domain_info": voi_ha_domain_info
            }
        }
        logging.info("sync the file %s to %s", ','.join(paths), backup_ip)
        rep_json = compute_post(backup_ip, command_data, timeout=600)
        if rep_json.get("code", -1) != 0:
            logging.error("_notify_backup_sync failed in compute_node: %s" % rep_json['msg'])
            raise EnableHaException("_notify_backup_sync")

    def _notify_backup_config(self, vip, netmask, sensitivity, quorum_ip, master_ip, backup_ip, backup_nic):
        # 通知备控123468
        _data = {
            "command": "config_backup",
            "handler": "HaHandler",
            "data": {
                "vip": vip,
                "netmask": netmask,
                "sensitivity": sensitivity,
                "quorum_ip": quorum_ip,
                "master_ip": master_ip,
                "backup_ip": backup_ip,
                "backup_nic": backup_nic
            }
        }
        rep_json = compute_post(backup_ip, _data)
        if rep_json.get("code", -1) != 0:
            logging.error("_notify_backup_config failed in compute_node: %s" % rep_json['msg'])
            raise EnableHaException("_notify_backup_config")
        return rep_json

    def _notify_backup_start(self, backup_ip):
        # 通知备控79
        _data = {
            "command": "start_backup",
            "handler": "HaHandler",
            "data": {
            }
        }
        rep_json = compute_post(backup_ip, _data)
        if rep_json.get("code", -1) != 0:
            logging.error("_notify_backup_start failed in compute_node: %s" % rep_json['msg'])
            raise EnableHaException("_notify_backup_start")

    def _notify_new_vip_host_check(self, new_vip_host_ip, vip):
        # 通知备控79
        _data = {
            "command": "check_vip",
            "handler": "HaHandler",
            "data": {
                "vip": vip
            }
        }
        rep_json = compute_post(new_vip_host_ip, _data)
        if rep_json.get("code", -1) != 0:
            logging.error("_notify_new_vip_host_check failed in compute_node: %s" % rep_json['msg'])
            raise SwitchHaMasterException("_notify_new_vip_host_check")


