import os
import time
import datetime
import json
import logging
import functools
from common.constants import IS_REQ, IS_RESP, LICENSE_DIR
from common.errcode import get_error_result
from yzy_ukey.ukey_auth import Ukey
from yzy_ukey.ukey_tcp_protocol import YzyProtocol



AUTH_INFO = dict()
logger = logging.getLogger(__name__)


def print_func(func):
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        logger.debug("request %s START, %s %s"% (func.__name__, str(args), str(kwargs)))
        try:
            ret = func(*args, **kwargs)
        except Exception as e:
            logger.error("", exc_info=True)
            ret = get_error_result("SystemError")
        logger.debug("request %s END: %s" % (func.__name__, ret))
        return ret

    return wrapped_func


class ClientProcessor(object):
    def __init__(self):
        pass

    @print_func
    def get_auth_info(self):
        """查询授权激活信息的接口"""
        global AUTH_INFO
        return AUTH_INFO

    @print_func
    def ukey_active(self, unit_name, sn):
        """激活Ukey的接口"""
        global AUTH_INFO
        # ret = get_error_result()
        # import pdb;pdb.set_trace()
        try:
            # 读取Ukey
            ukey = Ukey(pub_pem="pub_keys.pem")
            auth_struct = ukey.read_ukey_info()
            if not auth_struct:
                logger.error("ukey auth info read error")
                return get_error_result("UkeyOpenFailError")

            # 校验输入的单位名称、序列号与Ukey读到的是否一致
            ukey_uuit_name = auth_struct.unit_name
            ukey_sn = auth_struct.sn
            if ukey_uuit_name != unit_name or ukey_sn.lower() != sn.lower():
                logger.error("ukey active fail, %s != %s or %s != %s"% (ukey_uuit_name, unit_name, ukey_sn, sn))
                return get_error_result("AuthActiveFailError")

            # 在本地写激活文件
            ukey.active_sn(unit_name, sn)

            # 如果能读到授权激活信息（Ukey/试用授权），则更新AUTH_INFO，否则返回激活失败
            auth_info = ukey.read_auth_info()
            if hasattr(auth_info, "json"):
                AUTH_INFO = auth_info.json()
            else:
                # AUTH_INFO = dict()
                logger.error("active ukey fail %s"% auth_info)
                raise Exception("active ukey fail %s" % auth_info)
        except Exception as e:
            # 删除激活文件
            Ukey().delete_activate_file()
            logger.error(str(e), exc_info=True)
            return get_error_result("AuthActiveFailError")

        return get_error_result()

    @print_func
    def is_ukey_plugin(self):
        """检查是否已插入Ukey的接口"""
        try:
            ukey = Ukey(pub_pem="pub_keys.pem")
            file_data = ukey.check_and_open_ukey()
            if not file_data:
                logger.error("ukey not plugin")
                return get_error_result("UkeyNotFoundError")
        except Exception as e:
            # ret["code"] =
            logger.error(str(e), exc_info=True)
            return get_error_result("OtherError")
        return get_error_result()

    @print_func
    def read_license(self):
        """激活试用授权文件的接口，管理平台不存在使用场景，只能在初始化时激活试用授权文件"""
        global AUTH_INFO
        # ret = get_error_result()
        # import pdb;pdb.set_trace()
        try:
            ukey = Ukey(pub_pem="pub_keys.pem")
            auth_struct = ukey.read_license_info()
            if not auth_struct:
                logger.error("ukey auth info read error")
                return get_error_result("LicenseReadError")

            auth_json = auth_struct.json()
            ret = get_error_result(data=auth_json)
            return ret
        except Exception as e:
            # ret["code"] =
            logger.error(str(e), exc_info=True)
            return get_error_result("AuthActiveFailError")
        # return get_error_result()


class ServiceHandler:

    def __init__(self, client_ip, client_port):
        self.client_ip = client_ip
        self.client_port = client_port

    def processor(self, tcp_socket, protocol_paket):
        client_type = protocol_paket.get_client_type()
        # socket_client = ClientSocket(tcp_socket, client_type)

        data_dict = protocol_paket.data_json()
        logger.debug("[Request] data_dict: %s" % data_dict)
        if protocol_paket.req_or_res == IS_REQ:
            timestamp = data_dict.get("timestamp")
            # logger.debug("Get from client Request head: {}, timestamp: {}".format(protocol_paket, timestamp))
        elif protocol_paket.req_or_res == IS_RESP:
            pass
            # logger.debug("Get from client Response head: {}, data_dict: {}".format(protocol_paket, data_dict))
        else:
            logger.error("req_or_res: {}".format(protocol_paket.req_or_res))
            return False
        cmd = data_dict.get("cmd", "")
        client_processor = ClientProcessor()
        if not hasattr(client_processor, cmd):
            logger.error("[Request] client processor has not cmd %s"% cmd)
            ret_json = get_error_result("UkeyNotFunctionError")
        else:
            params = data_dict.get("params", {})
            processor_func = getattr(client_processor, cmd)
            ret_json = processor_func(**params)
        logger.info("[Response] ret_json: %s", ret_json)
        payload = json.dumps(ret_json).encode('utf-8')
        logger.debug("[Raw Response] payload: %s", payload)
        # payload = re.sub('[\\\]', '', json.dumps(ret_str)).encode('utf-8')
        # logger.debug("terminal {}:{} input creat_paket: payload: {}, token: {}".format(mac, self.client_ip,
        #                                                                                payload, token))
        _size, msg = YzyProtocol().create_paket(protocol_paket.seq_id, protocol_paket.client_id, IS_RESP, payload)
        # logger.debug("[Raw Response] _size: {}, msg: {}".format(_size, msg))
        tcp_socket.send(msg)
        logger.info("[Raw Response] send: size[%s], client_type[%s], client_ip[%s]" % (_size, client_type, self.client_ip))
        return True


def read_auth_info_thread(interval):
    """后台线程，每隔1分钟从Ukey/试用授权文件中读取授权激活信息，并更新AUTH_INFO"""
    logger.info("start read_auth_info_thread")
    count = 1
    try:
        ukey = Ukey(pub_pem="pub_keys.pem")
        # is_update = False
        # auth.lock记录当天是否更新过试用授权文件
        if not os.path.exists(LICENSE_DIR):
            os.makedirs(LICENSE_DIR)
        update_auth_lock = os.path.join(LICENSE_DIR, "auth.lock")
        if not os.path.exists(update_auth_lock):
            with open(update_auth_lock, "w") as f:
                f.write("")
    except Exception as e:
        logger.exception(str(e), exc_info=True)
    # count = 0
    while True:
        global AUTH_INFO
        try:
            _now = datetime.datetime.now().strftime("%Y-%m-%d")
            # 如果不存在auth.lock，则更新试用授权文件
            if not os.path.exists(update_auth_lock):
                with open(update_auth_lock, "w") as f:
                    f.write(_now)
                ret, msg = ukey.update_license_date()
                if not ret:
                    logger.error(msg)
            # 如果存在auth.lock，且其日期不等于今天，则更新试用授权文件和auth.lock
            else:
                update_date = ""
                with open(update_auth_lock, "r") as f:
                    update_date = f.read().rstrip()
                if update_date != _now:
                    ret, msg = ukey.update_license_date()
                    if not ret:
                        logger.error(msg)
                    else:
                        with open(update_auth_lock, "w") as f:
                            f.write(_now)

            # 如果能读到授权激活信息（Ukey/试用授权），则更新AUTH_INFO
            auth_info = ukey.read_auth_info()
            if hasattr(auth_info, "json"):
                AUTH_INFO = auth_info.json()
                count = 1
                time.sleep(interval)
            else:
                # 连续5次读不到ukey数据就清除已有授权信息
                if count <= 5:
                    logger.error("read_auth_info failed at count[%s]: %s" % (count, auth_info))
                    time.sleep(2)
                    count +=1
                else:
                    logger.info("clear global AUTH_INFO")
                    AUTH_INFO = dict()
                    count = 1
                    time.sleep(interval)

            logger.info("AUTH_INFO: %s" % AUTH_INFO)
        except Exception as e:
            logger.exception(str(e), exc_info=True)




