import os
import logging
import json
import ipaddress
import shutil
from yzy_server.database.apis import voi as voi_api
from yzy_server.database import apis as db_api
from yzy_server.database import models
from common.utils import create_uuid, voi_terminal_post
from common.errcode import get_error_result
from common import constants
from common import cmdutils


logger = logging.getLogger(__name__)


class VoiGroupController(object):

    def _check_params(self, data):
        if not data:
            return False
        name = data.get('name', '')
        start_ip = data.get('start_ip', '')
        end_ip = data.get('end_ip', '')
        if not (name and start_ip and end_ip):
            return False
        logger.info("check params ok")
        return True

    def cute_ip_range(self, item, ranges):
        start = ipaddress.IPv4Address(item["start"])
        end = ipaddress.IPv4Address(item["end"])
        # start_int = start._ip
        # end_int = end._ip
        tmp = ranges[:]
        for range in tmp:
            # _start = ipaddress.IPv4Address(range["start"])._ip
            # _end = ipaddress.IPv4Address(range["end"])._ip
            _start = ipaddress.IPv4Address(range["start"])
            _end = ipaddress.IPv4Address(range["end"])
            if start >= _start and end <= _end:
                # if start != _start -1:
                r1 = {"start": _start.compressed, "end": (start - 1).compressed}
                ranges.append(r1)
                # if end + 1 != _end:
                r2 = {"start": (end + 1).compressed, "end": _end.compressed}
                ranges.append(r2)
                ranges.remove(range)
                break
        return

    # def create_dhcp_config(self, dhcp_value, groups, control_node_ip, exclude_group=None):
    #     """
    #     创建dhcp的配置文件
    #     :param groups:
    #     :return:
    #     {
    #         "name": "group1",
    #         "group_type": 1,
    #         "desc": "this is group1",
    #         "start_ip": "",
    #         "end_ip": "",
    #         "dhcp": {
    #             "enable":  True,
    #             "start_ip": "172.16.1.40",
    #             "end_ip": "172.16.1.54",
    #             "netmask": "255.255.255.0",
    #             "gateway": "192.168.27.254",
    #             "dns1" : "8.8.8.8",
    #             "dns2" : "",
    #             "exclude": [
    #                 {"start": "172.16.1.24", "end": "172.16.1.24"},
    #                 {"start": "172.16.1.24", "end": "172.16.1.24"}
    #             ]
    #         }
    #     }
    #     """
    #     lines = ["default-lease-time 600;", "max-lease-time 7200;", "log-facility local7;"]
    #     start_ip = dhcp_value["start_ip"]
    #     end_ip = dhcp_value["end_ip"]
    #     netmask = dhcp_value["netmask"]
    #     gateway = dhcp_value["gateway"]
    #     ip_network = ipaddress.ip_network(start_ip + "/" + netmask, False)
    #     network_str = ip_network.network_address.compressed
    #     lines.append("subnet %s netmask %s {" % (network_str, netmask))
    #     ranges = [{"start": start_ip, "end": end_ip}]
    #     exclude = dhcp_value.get("exclude", [])
    #     for item in exclude:
    #         # if item["start"] == item["end"]:
    #         self.cute_ip_range(item, ranges)
    #     # lines.append("{")
    #     for range in ranges:
    #         lines.append("range %s %s;" % (range["start"], range["end"]))
    #     lines.append("option routers %s;" % gateway)
    #     lines.append("next-server %s;" % control_node_ip)
    #     lines.append('filename="pxelinux.0";')
    #     lines.append("}")
    #
    #     for group in groups:
    #         if group.uuid == exclude_group:
    #             continue
    #         if group.dhcp:
    #
    #             dhcp_conf = json.loads(group.dhcp)
    #             start_ip = dhcp_conf["start_ip"]
    #             end_ip = dhcp_conf["end_ip"]
    #             netmask = dhcp_conf["netmask"]
    #             gateway = dhcp_conf["gateway"]
    #             if not (start_ip and end_ip and netmask and gateway):
    #                 continue
    #
    #             ip_network = ipaddress.ip_network(start_ip + "/" + netmask, False)
    #             network_str = ip_network.network_address.compressed
    #             lines.append("subnet %s netmask %s {" % (network_str, netmask))
    #             ranges = [{"start": start_ip, "end": end_ip}]
    #             exclude = dhcp_conf.get("exclude", [])
    #             for item in exclude:
    #                 # if item["start"] == item["end"]:
    #                 self.cute_ip_range(item, ranges)
    #             # lines.append("{")
    #             for range in ranges:
    #                 lines.append("range %s %s;"% (range["start"], range["end"]))
    #             lines.append("option routers %s;" % gateway)
    #             lines.append("next-server %s;" % control_node_ip)
    #             lines.append('filename="vmlinuz-5.2.8-lfs-9.0";')
    #             lines.append("}")
    #     # 备份
    #     dhcp_conf_path = constants.DHCP_CONF
    #     dhcp_conf_path_bak = constants.DHCP_CONF + ".auto_bak"
    #     if os.path.exists(dhcp_conf_path):
    #         shutil.copy(dhcp_conf_path, dhcp_conf_path_bak)
    #     with open(dhcp_conf_path, "w+") as c:
    #         # for li in lines:
    #         c.write("\n".join(lines))
    #     logger.info("update dhcp config success: %s"% ("\n".join(lines)))
    #     return True

    # def reset_dhcp_server(self):
    #     dhcp_conf_path = constants.DHCP_CONF
    #     dhcp_conf_path_bak = constants.DHCP_CONF + ".auto_bak"
    #     shutil.copy(dhcp_conf_path, dhcp_conf_path + ".tmp")
    #     if os.path.exists(dhcp_conf_path_bak):
    #         shutil.copy(dhcp_conf_path_bak, dhcp_conf_path)
    #     try:
    #         stdout, stderror = cmdutils.execute('systemctl restart dhcpd',
    #                                             shell=True, timeout=20, run_as_root=True)
    #         logger.info("systemctl status dhcpd reset end, stdout:%s, stderror:%s", stdout, stderror)
    #     except Exception as e:
    #         logger.error("", exc_info=True)
    #         return False
    #     return True
        # with open(dhcp_conf_path, "w+") as c:
        #     c.writelines(lines)

    # def update_dhcp_server(self, dhcp_value, exclude_group=None):
    #     control_node = db_api.get_controller_node()
    #     groups = db_api.get_item_with_all(models.YzyVoiGroup, {})
    #     ret = self.create_dhcp_config(dhcp_value, groups, control_node.ip, exclude_group)
    #     # todo 重启dhcp服务
    #     try:
    #         stdout, stderror = cmdutils.execute('systemctl restart dhcpd', shell=True, timeout=20, run_as_root=True)
    #         logger.info("systemctl status dhcpd execute end, stdout:%s, stderror:%s", stdout, stderror)
    #     except Exception as e:
    #         logger.error("", exc_info=True)
    #         self.reset_dhcp_server()
    #
    #     return

    def create_group(self, data):
        """
        创建分组
        """
        if not self._check_params(data):
            return get_error_result("ParamError")

        group = voi_api.get_item_with_first(models.YzyVoiGroup, {'name': data['name']})
        if group:
            return get_error_result("GroupAlreadyExists", name=data['name'])
        group_uuid = create_uuid()
        # dhcp = data.get("dhcp")
        group_value = {
            "uuid": group_uuid,
            "group_type": data.get('group_type', 1),
            "name": data['name'],
            "desc": data['desc'],
            "start_ip": data['start_ip'],
            "end_ip": data['end_ip'],
            # "dhcp" : json.dumps(data["dhcp"]) if dhcp else None
        }
        # if dhcp:
        #     start_ip = dhcp.get("start_ip")
        #     end_ip = dhcp.get("end_ip")
        #     netmask = dhcp.get("netmask")
        #     gateway = dhcp.get("gateway")
        #     if start_ip and end_ip and netmask and gateway:
        #         # 更新DHCP配置
        #         try:
        #             self.update_dhcp_server(dhcp)
        #         except Exception as e:
        #             logger.error("", exc_info=True)
        #             return get_error_result("DhcpConfigUpdateError")

        templates = voi_api.get_item_with_all(models.YzyVoiTemplate, {"all_group": True})
        binds = list()
        for template in templates:
            binds.append({
                "uuid": create_uuid(),
                "template_uuid": template.uuid,
                "group_uuid": group_uuid
            })
        try:
            voi_api.create_voi_group(group_value)
            if binds:
                db_api.insert_with_many(models.YzyVoiTemplateGroups, binds)
            logger.info("create voi group %s success", data['name'])
        except Exception as e:
            logging.info("insert voi group info to db failed:%s", e)
            return get_error_result("GroupCreateError", name=data['name'])
        # if group_value.get("dhcp"):
        #     group_value["dhcp"] = json.loads(group_value["dhcp"])
        return get_error_result("Success", group_value)

    def delete_group(self, group_uuid):
        group = voi_api.get_item_with_first(models.YzyVoiGroup, {"uuid": group_uuid})
        if not group:
            logger.error("group: %s not exist", group_uuid)
            return get_error_result("GroupNotExists", name='')
        if constants.EDUCATION_DESKTOP == group.group_type:
            desktop = voi_api.get_item_with_first(models.YzyVoiDesktop, {"group_uuid": group_uuid})
            if desktop:
                logger.error("group already in use", group_uuid)
                return get_error_result("GroupInUse", name=group.name)
        binds = voi_api.get_item_with_all(models.YzyVoiTemplateGroups, {"group_uuid": group_uuid})
        for bind in binds:
            bind.soft_delete()
        group.soft_delete()
        logger.info("delete voi group %s success", group_uuid)
        ret = voi_terminal_post("/api/v1/voi/terminal/command", {"handler": "WebTerminalHandler",
                                                         "command": "delete_group",
                                                         "data": {
                                                                    "group_uuid": group_uuid
                                                                  }
                                                        }
                            )
        return ret

    def update_group(self, data):
        group_uuid = data.get('uuid', '')
        group = voi_api.get_item_with_first(models.YzyVoiGroup, {"uuid": group_uuid})
        if not group:
            logger.error("group: %s not exist", group_uuid)
            return get_error_result("GroupNotExists", name='')
        try:
            # dhcp_conf = data["value"].get("dhcp")
            # if dhcp_conf:
            #     start_ip = dhcp_conf.get("start_ip")
            #     end_ip = dhcp_conf.get("end_ip")
            #     netmask = dhcp_conf.get("netmask")
            #     gateway = dhcp_conf.get("gateway")
            #     if start_ip and end_ip and netmask and gateway:
            #         # 更新DHCP配置
            #         try:
            #             self.update_dhcp_server(dhcp_conf, group_uuid)
            #         except Exception as e:
            #             logger.error("", exc_info=True)
            #             return get_error_result("DhcpConfigUpdateError")
            #     data['value']["dhcp"] = json.dumps(dhcp_conf)
            group.update(data['value'])
            group.soft_update()
        except Exception as e:
            logger.error("update voi group:%s failed:%s", group_uuid, e, exc_info=True)
            return get_error_result("GroupUpdateError", name=group.name)
        logger.info("update voi group:%s success", group_uuid)
        return get_error_result("Success")
