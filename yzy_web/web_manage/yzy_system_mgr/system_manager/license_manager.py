import logging
import os
# import math
# import configparser
# from thrift.protocol import TBinaryProtocol, TMultiplexedProtocol
# from thrift.transport import TSocket, TTransport
# from ukey import UKeyServer
# from ukey.ttypes import Registry_Info
from web_manage.common import constants
from web_manage.common.log import operation_record
from web_manage.common.utils import get_error_result
from web_manage.common.ukey_tcp_client import UkeyClient
# from web_manage.yzy_system_mgr.models import YzyAuth

logger = logging.getLogger(__name__)


class LicenseManager(object):
    """
    获取的授权信息主要包括以下字段
        UserID: 用户ID
        useType: 0-过期 1-宽限期 2-试用期 3-正式版
        DelayDays: useType为宽限期时的宽限时间，单位为s
        ExpireDays: useType为试用期时的剩余试用时间，单位为s
        IDVTotalSize: IDV授权数
        VDITotalSize: VDI授权数
        VOITotalSize: VOI授权数
        SNDay: 注册时间，需要通过一定方法转换得到具体值
        CopyRight: 0-标准版 1-企业版 2-专业版 3-旗舰版
    """
    def info(self):
        """查询授权激活信息、版本"""
        # config = configparser.ConfigParser()
        # config.read(constants.CONFIG_PATH)
        # # license在web和server中都要读，因此动态获取
        # if "license" in config.sections():
        #     sn = config.get('license', 'sn', fallback=None)
        #     org_name = config.get('license', 'org_name', fallback=None)
        # else:
        #     sn = None
        #     org_name = None

        # obj = YzyAuth.objects.filter(deleted=False).first()
        # if obj:
        #     sn = obj.sn
        #     org_name = obj.organization
        # else:
        #     sn = None
        #     org_name = None
        # try:
        #     registry_info = Registry_Info()
        #     if sn and org_name:
        #         sn = sn.replace('-', '')
        #         sn_array = bytearray(16)
        #         for index in range(int(len(sn) / 2)):
        #             sn_char = sn[index * 2:index * 2 + 2]
        #             sn_array[index] = int(sn_char, 16)
        #         unitname_array = bytearray(org_name, encoding='utf_16_le')
        #         unitname_array.extend(bytearray(256 - len(unitname_array)))
        #         registry_info = Registry_Info(sn_array, unitname_array)
        #
        #     transport = TSocket.TSocket('localhost', 9000)
        #     transport = TTransport.TBufferedTransport(transport)
        #     protocol = TBinaryProtocol.TBinaryProtocol(transport)
        #     protocol = TMultiplexedProtocol.TMultiplexedProtocol(protocol, "UKeyService")
        #     client = UKeyServer.Client(protocol)
        #     transport.open()
        #
        #     auth_info = client.GetAuthorInfo(registry_info)
        #     sn_date_data = list()
        #     sn_date_data.append(str(int('%X' % auth_info.SNDay[1], 16) + 1900))
        #     sn_date_data.append('-')
        #     sn_date_data.append(str(int('%X' % auth_info.SNDay[2], 16) + 1))
        #     sn_date_data.append('-')
        #     sn_date_data.append(str(int('%X' % auth_info.SNDay[3], 16)))
        #     sn_date_data.append(' ')
        #     sn_date_data.append(str(int('%X' % auth_info.SNDay[4], 16)))
        #     sn_date_data.append(':')
        #     sn_date_data.append(str(int('%X' % auth_info.SNDay[5], 16)))
        #     sn_date_data.append(':')
        #     sn_date_data.append(str(int('%X' % auth_info.SNDay[6], 16)))
        #     sn_date = ''.join(sn_date_data)
        #     expire_time = auth_info.ExpireDays
        #     vdi_size = auth_info.VDITotalSize
        #     voi_size = auth_info.VOITotalSize
        #     idv_size = auth_info.IDVTotalSize
        #     transport.close()
        #     logger.info("use_type:%s, copy_right:%s, expire_time:%s, idv_size:%s, "
        #                 "vdi_size:%s, voi_size:%s, delay_days:%s", auth_info.useType,
        #                 auth_info.CopyRight, expire_time, idv_size, vdi_size, voi_size, auth_info.DelayDays)
        #     # if "license" in config.sections():
        #     #     version = config.get('license', 'version', fallback=None)
        #     # else:
        #     version = None
        #     if not version:
        #         version_file = os.path.join(constants.BASE_DIR, 'version')
        #         if os.path.exists(version_file):
        #             with open(version_file, 'r') as fd:
        #                 version = fd.read()
        #     if 1 == auth_info.useType:
        #         expire_time = math.ceil(auth_info.DelayDays/60/60/24)
        #     elif 2 == auth_info.useType:
        #         expire_time = math.ceil(expire_time/60/60/24)
        #     else:
        #         expire_time = 0
        #     return {
        #         "auth_type": auth_info.useType,
        #         "copy_right": auth_info.CopyRight,
        #         "user_id": auth_info.UserID,
        #         "sn_date": sn_date,
        #         "expire_time": expire_time,
        #         "idv_size": idv_size,
        #         "vdi_size": vdi_size,
        #         "voi_size": voi_size,
        #         "org_name": org_name,
        #         "version": version
        #     }
        # except Exception as e:
        #     logger.exception("get auth info failed:%s", e)

        version = None
        try:
            version_file = os.path.join(constants.BASE_DIR, 'version')
            if os.path.exists(version_file):
                with open(version_file, 'r') as fd:
                    version = fd.read()

            client = UkeyClient()
            auth_info = client.get_auth_info()
            # logger.info("auth_info: %s", auth_info)
            return {
                "auth_type": auth_info["use_type"],
                "copy_right": auth_info["copy_right"],
                "user_id": auth_info["user_id"],
                "sn_date": auth_info["sn_day"],
                "expire_time": auth_info["expire_day"],
                "idv_size": auth_info["idv_num"],
                "vdi_size": auth_info["vdi_num"],
                "voi_size": auth_info["voi_num"],
                "org_name": auth_info["unit_name"],
                "version": version
            }
        except Exception as e:
            logger.exception("get auth info failed: %s", str(e))
            return {
                "auth_type": 0,
                "copy_right": 0,
                "user_id": 0,
                "sn_date": "0000-00-00 00:00:00",
                "expire_time": 0,
                "idv_size": 0,
                "vdi_size": 0,
                "voi_size": 0,
                "org_name": None,
                "version": version
            }


    def get_ukey(self):
        """检查是否已插入Ukey"""
        # res = {"result": False}
        # try:
        #     transport = TSocket.TSocket('localhost', 9000)
        #     transport = TTransport.TBufferedTransport(transport)
        #     protocol = TBinaryProtocol.TBinaryProtocol(transport)
        #     protocol = TMultiplexedProtocol.TMultiplexedProtocol(protocol, "UKeyService")
        #     client = UKeyServer.Client(protocol)
        #     transport.open()
        #
        #     logging.info("get ukey transport open success checkUkeyState: %s", client.CheckUkeyState())
        #     if client.CheckUkeyState() == 1:
        #         res['result'] = True
        #     transport.close()
        # except Exception as e:
        #     logging.error("isUkeyPlugin exec error: %s", e)
        #     transport.close()
        #
        # return res

        client = UkeyClient()
        ret = client.is_ukey_plugin()
        if ret:
            if ret.get("code", -1) == 0:
                return get_error_result(data={"result": True})
            else:
                return ret
        else:
            return get_error_result("OtherError")

    # def set_auth_info(self, sn, org_name):
    #     logging.info("set auth info")
    #     config = configparser.ConfigParser()
    #     config.read(constants.CONFIG_PATH)
    #     if "license" not in config.sections():
    #         config.add_section("license")
    #     config.set("license", "sn", sn)
    #     config.set("license", "org_name", org_name)
    #     logger.info("set auth info to %s", constants.CONFIG_PATH)
    #     with open(constants.CONFIG_PATH, 'w') as fd:
    #         config.write(fd)

    @operation_record("正式授权激活", module="Auth")
    def activation(self, sn, org_name):
        """"激活Ukey"""
        # try:
        #     logger.info("sn:%s, org_name:%s", sn, org_name)
        #     sn = sn.replace('-', '')
        #     by_array = bytearray(16)
        #     for index in range(int(len(sn) / 2)):
        #         sn_char = sn[index * 2:index * 2 + 2]
        #         by_array[index] = int(sn_char, 16)
        #     name_array = bytearray(org_name, encoding='utf_16_le')
        #     name_array.extend(bytearray(256 - len(name_array)))
        #     transport = TSocket.TSocket('localhost', 9000)
        #     transport = TTransport.TBufferedTransport(transport)
        #     protocol = TBinaryProtocol.TBinaryProtocol(transport)
        #     protocol = TMultiplexedProtocol.TMultiplexedProtocol(protocol, "UKeyService")
        #     client = UKeyServer.Client(protocol)
        #     transport.open()
        #
        #     if client.CheckUkeyState() == 1:
        #         # registry_info = Registry_Info()
        #         # author_info = client.GetAuthorInfo(registry_info)
        #         # logger.info("use_type:%s, expire_time:%s, vdi_size:%s, voi_size:%s", author_info.useType,
        #         #             author_info.ExpireDays, author_info.VDITotalSize, author_info.VDITotalSize)
        #         # 0-过期 1-宽限期 2-试用期 3-正式版
        #         registry_info = Registry_Info(by_array, name_array)
        #         author_info = client.RegistAuth(registry_info)
        #         logger.info("after register, use_type:%s, copy_right:%s, expire_time:%s, idv_size:%s, vdi_size:%s, "
        #                     "voi_size:%s", author_info.useType, author_info.CopyRight, author_info.ExpireDays,
        #                     author_info.IDVTotalSize, author_info.VDITotalSize, author_info.VDITotalSize)
        #         if author_info.useType == 3:
        #             logger.info("user type is formal, return true")
        #             # self.set_auth_info(sn, org_name)
        #             return get_error_result()
        #         else:
        #             logger.error("the sn or org_name is error, registry failed")
        #             return get_error_result("AuthFailed")
        #     transport.close()
        # except Exception as e:
        #     logger.exception("activate failed:%s", e)
        #     return get_error_result("AuthFailed")
        # return get_error_result("AuthFailed")

        client = UkeyClient()
        # TODO: 确认下序列号的传参格式
        ret = client.ukey_active(unit_name=org_name, sn=sn)
        if ret:
            return ret
        else:
            return get_error_result("OtherError")


