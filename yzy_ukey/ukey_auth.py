import os
import logging
import rsa
import base64
import struct
import uuid
import hashlib
import datetime
from rsa import PublicKey,transform, core
from ctypes import *
from common.constants import BASE_DIR, LICENSE_DIR

logger = logging.getLogger(__name__)

# cip_text = b'\x9c8T<\xd5.\\\xca\xeb\x1fh\x08HC\x14\\\x1c\x1b\x91d\xf9~\xe93\x7f\xd7&0\x9ci\x83[\x91"]\xa2\x16c\xeb\xec\x83\x075Z]\rQ\xf0\x85\xa5S\x8f/\xdd\xc3\x01\\\xd0\x9cA\x98\x08\xbbV\xe1\xf4\x19\x9fo,\xcbd)\x8bz=\xe4\x84\xf1\x04\xb3'


# def create_cip():
#     with open("cip", "wb") as f:
#         f.write(cip_text)


class UkeyStruct(Structure):
    pass


UkeyStruct._fields_ = [
        ('m_Ver', c_ushort),
        ('m_Type', c_ushort),
        ('m_BirthDay', c_char_p),
        ('m_Agent', c_uint),
        ('m_PID', c_uint),
        ('m_UserID', c_uint),
        ('m_HID', c_char_p),
        ('m_IsMother', c_int),
        ('m_DevType', c_uint)
        # ('m_Reserve', c_ushort)
    ]


class AuthInfoStruct():
    """
    (8, 245, 185, 148, 10, 108, 2, 71, 152,
     b'\xd4\xc6\xd6\xae\xd2\xed\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x8103,
     0, 7, 120, 9, 29, 10, 24, 59, 0, 7776000, 10, 10, 10, 10, 1)
    """
    def __init__(self, authinfo_pack):
        if not (authinfo_pack and isinstance(authinfo_pack, tuple)):
            raise Exception("auth info struct pack is not tuple")
        self.user_id = authinfo_pack[0]         # 用户id
        self.hid = "".join([str(i) for i in authinfo_pack[1:9]])        # 硬件ID
        # unit_name =
        self.unit_name = (authinfo_pack[9].rstrip(b"\x00")).decode("gbk")   # 单位名称
        sn_1, sn_2, sn_3, sn_4, sn_5, sn_6, sn_7, sn_8, sn_9, sn_10, sn_11 = authinfo_pack[10], authinfo_pack[11], \
                                        authinfo_pack[12], authinfo_pack[13], authinfo_pack[14], authinfo_pack[15], \
                                        authinfo_pack[16], authinfo_pack[17], authinfo_pack[18],authinfo_pack[19], \
                                        authinfo_pack[20]
        sn_last = (sn_6 << 40) + (sn_7 << 32) + (sn_8 << 24) + (sn_9 << 16) + (sn_10 << 8) + sn_11
        sn_fields = (sn_1, sn_2, sn_3, sn_4, sn_5, sn_last)
        self.sn = str(uuid.UUID(fields=sn_fields))                                         # 正式序号
        self.use_type = authinfo_pack[21]                                   # 用户类型
        year = authinfo_pack[22] + (authinfo_pack[23] << 8)
        mon = authinfo_pack[24]
        day = authinfo_pack[25]
        hour = authinfo_pack[26]
        min = authinfo_pack[27]
        sec = authinfo_pack[28]
        self.sn_day = datetime.datetime(year=year, month=mon, day=day, hour=hour, minute=min,
                                            second=sec).strftime("%Y-%m-%d %H:%M:%S")
        self.expire_day = authinfo_pack[29]
        self.vdi_num = authinfo_pack[30]
        self.voi_num = authinfo_pack[31]
        self.idv_num = authinfo_pack[32]
        self.teacher_num = authinfo_pack[33]
        self.copy_right = authinfo_pack[34]
        self.active = 0

    def json(self):
        return {
            "user_id": self.user_id,
            "hid": self.hid,
            "unit_name": self.unit_name,
            "sn": self.sn,
            "use_type": self.use_type,
            "sn_day": self.sn_day,
            "expire_day": self.expire_day,
            "vdi_num": self.vdi_num,
            "voi_num": self.voi_num,
            "idv_num": self.idv_num,
            "teacher_num": self.teacher_num,
            "copy_right": self.copy_right,
            "active": self.active
        }


class EnDeCrypt:

    def __init__(self, pub_pem="pub_keys.pem", pri_pem=None):
        self.pub_key = None
        if pub_pem == "pub_keys.pem":
            pub_pem = os.path.join(BASE_DIR, "config", pub_pem)
        with open(pub_pem, "rb") as x:
            f = x.read()
            self.pub_key = rsa.PublicKey.load_pkcs1(f)

    def pubDecrypt(self, cipher_text):
        # import pdb; pdb.set_trace()
        # public_key = PublicKey.load_pkcs1(self.pub_key)
        encrypted = transform.bytes2int(cipher_text)
        decrypted = core.decrypt_int(encrypted, self.pub_key.e, self.pub_key.n)
        text = transform.int2bytes(decrypted)
        # import pdb; pdb.set_trace()
        if len(text) > 0 and text[0] == 1:
            pos = text.find(b'\x00')
            if pos > 0:
                # logger.info(text[pos + 1:])
                return text[pos + 1:].strip(b'\xcc')
            else:
                return None

    # def pubDecrypt_bak(self, cipher_text):
    #     public_key = PublicKey.load_pkcs1_openssl_pem(self.pub_key)
    #     ciphertext = transform.bytes2int(cipher_text)
    #     decrypted = core.decrypt_int(ciphertext, public_key.e, public_key.n)
    #     text = transform.int2bytes(decrypted)[127:]
    #     logger.info(base64.b64encode(text))

    def decrypt(self, data: bytes):
        num = transform.bytes2int(data)
        decrypto = core.decrypt_int(num, self.pub_key.e, self.pub_key.n)
        out = transform.int2bytes(decrypto)
        logger.info(out)
        sep_idx = out.index(b"\x00", 2)
        out = out[sep_idx + 1:]
        return out



class Ukey:

    def __init__(self, pub_pem=""):
        # self.header_length = 24
        self.format_str = "<I8B64sIHH8BI8BQIIIII"
        self.license_dir = LICENSE_DIR
        self.ukey_struct_1 = c_void_p(0)
        self.p_ukey_struct = byref(self.ukey_struct_1)
        self.ukey_struct = UkeyStruct()
        self.FLAG_ADMINPIN = 1
        self.FLAG_USERPIN = 0
        self.PIN = b"FFFFFFFFFFFFFFFF"
        self.admin_pin = c_char_p(self.PIN)
        self.SUCCESS = 0
        self.FAIL = -1
        self.pub_pem = pub_pem
        dll_path = os.path.join(os.getcwd(), "libRockeyARM.so.0.3")
        logger.info(dll_path)
        self.libc = cdll.LoadLibrary(dll_path)

        # self.libc.Dongle_Open.argtypes = [POINTER(UkeyStruct), c_int]
        # self.libc.Dongle_Open.restype = c_int
        # self.libc.Dongle_Enum.argtypes = [POINTER(UkeyStruct), POINTER(c_int)]
        # self.libc.Dongle_Enum.restype = c_int
        # self.libc.Dongle_VerifyPIN.argtypes = [UkeyStruct, c_int, c_char_p, POINTER(c_int)]
        # self.libc.Dongle_VerifyPIN.restype = c_int
        # self.libc.Dongle_ReadFile.argtypes = [UkeyStruct, c_ushort, c_ushort, POINTER(c_ubyte), c_int]
        # self.libc.Dongle_ReadFile.restype = c_int

    def ukey_open(self, inx=0):
        # ukey_struct = UkeyStruct()
        u_count = c_int(0)
        u_inx = c_int(inx)
        ret = self.libc.Dongle_Enum(None, byref(u_count))
        logger.info("ukey count : %s, return: %s"% (u_count, ret))
        if ret:
            return self.FAIL

        ret = self.libc.Dongle_Open(self.p_ukey_struct, u_inx)
        logger.info("open ukey return: %s"% ret)
        # import pdb; pdb.set_trace()
        logger.info("struct %s" % self.ukey_struct_1)
        return ret

    def ukey_close(self):
        try:
            if self.ukey_struct_1:
                self.libc.Dongle_Close(self.ukey_struct_1)
        except Exception as e:
            logger.error("", exc_info=True)

    def ukey_read(self):
        file_id = 1
        file_offset = 0
        file_data = create_string_buffer(1024)
        n_remain_count = c_int()
        # ukey_struct = c_void_p()
        # p_pkt_data = byref(ukey_struct)
        ret = self.libc.Dongle_VerifyPIN(self.ukey_struct_1, self.FLAG_ADMINPIN, self.admin_pin, byref(n_remain_count))
        logger.info("verify pin return: 0X%08X, remain_count: %s"% (ret, n_remain_count))
        ret = self.libc.Dongle_ReadFile(self.ukey_struct_1, file_id, file_offset, byref(file_data), sizeof(file_data))
        logger.info(file_data.raw.rstrip(b"\xcc"))
        logger.info("read file return: 0X%08X"% ret)
        return ret, file_data.raw.rstrip(b"\xcc")

    def parse_encrypt_info(self, base64_str):
        en_str = base64.b64decode(base64_str)
        return struct.unpack(self.format_str, en_str)

    def read_license_info(self):
        """读取并校验试用授权文件
        读取试用授权文件里的授权信息
        试用授权文件两部分拼接而成，“####” 分割：
        1、原始加密试用授权文件内容
        2、记录使用天数：b_now_date, days, count, b_sign
            b_now_date: 更新日期
            days: 剩余天数
            count: 当天更新次数
            b_sign: 签名
        3、状态， 0-过期 1-宽限期 2-试用期 3-正式版

        :return:
        """
        # import pdb;pdb.set_trace()
        if not os.path.exists(self.license_dir):
            try:
                os.makedirs(self.license_dir)
            except:
                logger.info("error: the license_dir create fail")
                raise Exception("the license dir create error")

        license_path = os.path.join(self.license_dir, "license.lic")
        if not os.path.exists(license_path):
            logger.info("error: the license not exist: %s", license_path)
            raise Exception("the license not exist")

        # 对试用授权文件解密，其内容以 b"####" 为分隔符分成两部分：原始信息 + 代码写入信息
        with open(license_path, "rb") as f:
            file_bin = f.read()
        items = file_bin.split(b"####")

        if len(items) < 2:
            file_bin = items[0]
            sign_encryt = None
        else:
            file_bin, sign_encryt = items[0], items[1]

        try:
            file_bin = file_bin.rstrip(b'\x00')
            _encryt = EnDeCrypt(pub_pem=self.pub_pem)
            base64_str = _encryt.pubDecrypt(file_bin)
            if not base64_str:
                logger.info("license file pub decrypt error !!!")
                # self.ukey_close()
                return None
            # auth_info = self.parse_encrypt_info(base64_str)
            auth_info_struct = self.parse_encrypt_info(base64_str)
            if not auth_info_struct:
                logger.error("ukey file parse error")
                return False

            # 0-过期 1-宽限期 2-试用期 3-正式版
            auth_info = AuthInfoStruct(auth_info_struct)
            # 如果有代码写入信息部分，则校验
            # TODO: 此处没有利用b_now_date校验系统日期
            if sign_encryt:
                expire_format_str = "<10sII32s"
                b_now_date, left_days, count, b_sign = struct.unpack(expire_format_str, sign_encryt)

                if left_days <= 0:
                    # 过期
                    auth_info.use_type = 0
                else:
                    auth_info.use_type = 2
                    auth_info.expire_day = left_days
            else:
                auth_info.expire_day = int(auth_info.expire_day / 60 / 60 / 24)

            return auth_info
        except Exception as e:
            logger.exception(str(e), exc_info=True)
            return None

    def pack_expire_string(self, sn_day, _now_str, days):
        sign_str = "%s%s%d"% (sn_day, _now_str, days)
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    def update_license_date(self):
        """更新试用授权文件的代码写入信息部分，用于判断用户是否修改了系统时间，以维持试用授权继续有效
        每天更新试用授权文件一次
        试用授权文件两部分拼接而成，“####” 分割：
        1、原始加密试用授权文件内容
        2、记录使用天数：b_now_date, days, count, b_sign
            b_now_date: 更新日期
            days: 剩余天数
            count: 当天更新次数
            b_sign: 签名
        :return:
        """
        if not os.path.exists(self.license_dir):
            try:
                os.makedirs(self.license_dir)
            except:
                logger.info("error: the license_dir create fail")
                return False, "the license dir create error"

        active_file = os.path.join(self.license_dir, "activate")
        # 已经激活过，只读取Ukey
        if os.path.exists(active_file):
            ukey_info = self.check_and_open_ukey()
            with open(active_file, "r") as f:
                active_file_data  = f.read()

            if not ukey_info:
                if len(active_file_data[32:]) > 2:
                    return True, "the extend date expire"
                with open(active_file, "w") as f:
                    f.write(active_file_data + "1")

                return True, "in extend date"
            else:
                with open(active_file, "w") as f:
                    f.write(active_file_data[:32])
                return True, "the server active"
        # 未激活过，只读取试用授权文件
        else:
            license_path = os.path.join(self.license_dir, "license.lic")
            if not os.path.exists(license_path):
                logger.info("error: the license not exist")
                return False, "the license not exist"

            # 对试用授权文件解密，其内容以 b"####" 为分隔符分成两部分：原始信息 + 代码写入信息
            expire_format_str = "<10sII32s"
            file_data = b""
            with open(license_path, "rb") as f:
                file_data = f.read()
            file_items = file_data.split(b"####")
            file_bin = file_items[0].rstrip(b"\x00")
            _encryt = EnDeCrypt(pub_pem=self.pub_pem)
            base64_str = _encryt.pubDecrypt(file_bin)
            if not base64_str:
                logger.info("ukey file pub decrypt error !!!")
                return False, "ukey file pub decrypt error"

            # 对原始信息部分解码
            format_str = "<I8B64sIHH8BI8BQIIIII"
            en_str = base64.b64decode(base64_str)
            auth_struct = struct.unpack(format_str, en_str)
            logger.info(auth_struct)
            auth_info = AuthInfoStruct(auth_struct)
            # TODO：sn_day：试用授权文件生成的日期时间，注意读到的原始值是否是合法的日期值
            sn_day = ("00000" + str(auth_info.sn_day))[-19:]
            _now = datetime.datetime.now()

            sn_day_date = datetime.datetime.strptime(sn_day, "%Y-%m-%d %H:%M:%S")
            b_sn_day = sn_day.encode("utf-8")
            date_str = _now.strftime("%Y-%m-%d")

            # 如果试用授权文件第一次被读取，则只包含原始信息
            if len(file_items) == 1:
                # 试用授权文件已用天数
                _days = (_now.date() - sn_day_date.date()).days
                # expire_day = int(int(auth_info.expire_day) / 60 * 60 * 24)
                if _days < 0:
                    # 今天早于试用授权文件生成日期，说明用户修改了系统日期
                    logger.info("warning system date has modified")
                    return False, "system date has modified"

                left_days = 90 - _days

                # 向试用授权文件中增加代码写入信息
                b_date_str = date_str.encode("utf-8")
                # b_days = str(_days).encode("utf-8")
                b_sign_str = self.pack_expire_string(sn_day, date_str, left_days).encode("utf-8")
                expire_str = struct.pack(expire_format_str, b_date_str, left_days, 0, b_sign_str)
                with open(license_path, "wb") as f:
                    f.write(file_items[0])
                    f.write(b"####")
                    f.write(expire_str)
                return True, "success"

            # 如果试用授权文件包含两部分信息，则校验代码写入信息
            elif len(file_items) == 2:
                encrypt_str, sign_str = file_items
                b_now_date, left_days, count, b_sign = struct.unpack(expire_format_str, sign_str)
                # 校验代码写入信息的签名
                _sign = hashlib.md5(b_sn_day + b_now_date + str(left_days).encode()).hexdigest()
                if _sign != b_sign.decode():
                    logger.info("license file is bad")
                    return False, "license file is bad"
                # 校验用户是否修改了系统时间
                pre_date_str = b_now_date.decode()
                pre_date_obj = datetime.datetime.strptime(pre_date_str, "%Y-%m-%d")
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                if pre_date_obj > date_obj:
                    logger.info("warning system date has modified")
                    return False, "system date has modified"
                elif pre_date_obj == date_obj:
                    if count > 10:
                        logger.info("warning modifiy license file too many")
                        return False, "modifiy license file too many"
                    count += 1
                else:
                    count = 0

                left_days -= 1
                if left_days < 0:
                    logger.info("warning expire")
                    return False, "expire"

                # 更新试用授权文件
                b_date_str = date_str.encode("utf-8")
                # b_days = str(_days).encode("utf-8")
                b_sign_str = self.pack_expire_string(sn_day, date_str, left_days).encode("utf-8")
                expire_str = struct.pack(expire_format_str, b_date_str, left_days, count, b_sign_str)
                with open(license_path, "wb") as f:
                    f.write(encrypt_str)
                    f.write(b"####")
                    f.write(expire_str)

                return True, "success"
            else:
                logger.info("warning license file is bad")
                return False, "license file is bad"

    # 633ee8b6e3ca4aca0971855f7f7f0bfa
    def get_activation_file(self):
        """读取激活文件
        文件activate中保存签名
        unit_name, sn 的md5值
        :return:
        """
        active_str = ""
        active_file = os.path.join(self.license_dir, "activate")
        if not os.path.exists(active_file):
            return active_str

        with open(active_file, "r") as f:
            active_str = f.read()
        return active_str[:32]

    def active_sn(self, unit_name, sn):
        """写激活文件"""
        active_file = os.path.join(self.license_dir, "activate")
        # if not os.path.exists(active_file):
        active_str = hashlib.md5((unit_name + sn).encode()).hexdigest()
        with open(active_file, "w") as f:
            f.write(active_str)
        return True

    def delete_activate_file(self):
        active_file = os.path.join(self.license_dir, "activate")
        if os.path.exists(active_file):
            try:
                os.remove(active_file)
            except:
                pass

    def check_and_open_ukey(self):
        """
        打开读取ukey加密内容
        :return:
        """
        try:
            ret = self.ukey_open()
            logger.info("open ukey return: %s" % ret)
            if ret:
                logger.info("open ukey fail !!!")
                raise Exception("open ukey fail !")

            ret, file_data = self.ukey_read()
            if ret:
                logger.info("ukey file read error !!!!")
                raise Exception("ukey file read error !")
            # with open("auth.lic", "wb") as f:
            #     f.write(file_data)
            return file_data
        except Exception as e:
            logger.error("ukey check fail")
            return False
        finally:
            self.ukey_close()

    def read_ukey_info(self):
        """读取Ukey内的信息
        解密ukey内容
        返回:auth_info_struct
        :return:
        """
        file_data = self.check_and_open_ukey()
        if not file_data:
            # logger.error("ukey open and read fail")
            return False

        _encryt = EnDeCrypt(pub_pem=self.pub_pem)
        base64_str = _encryt.pubDecrypt(file_data)
        if not base64_str:
            logger.error("ukey file pub decrypt error !!!")
            return False

        auth_info_struct = self.parse_encrypt_info(base64_str)
        if not auth_info_struct:
            logger.error("ukey file parse error")
            return False

        auth_info = AuthInfoStruct(auth_info_struct)
        return auth_info

    def read_auth_info(self, is_ukey=False):
        """读取授权激活信息：Ukey/试用授权文件"""
        is_ukey = False
        active_file_data = None
        try:
            try:
                auth_info_struct = self.read_ukey_info()
                if not auth_info_struct:
                    logger.info("ukey file pub decrypt error !!!")
                    raise Exception("ukey info read fail")
                is_ukey = True
            except:
                logger.info("warning: ukey read fail")
                # 读不到ukey, 判断是否激活过
                active_file = os.path.join(self.license_dir, "activate")
                if os.path.exists(active_file):
                    # 激活过
                    with open(active_file, "r") as f:
                        active_file_data = f.read()

                # 判断授权读取授权文件
                auth_info_struct = self.read_license_info()
        except:
            logger.info("auth ukey or license error")
            return None

        logger.info(auth_info_struct)
        if not auth_info_struct:
            logger.error("read auth info error")
            return auth_info_struct
        # 0-过期 1-宽限期 2-试用期 3-正式版
        if is_ukey:
            # 如果本地激活文件保存的单位名称、序列号与Ukey中读到的一致，说明该Ukey已激活
            active_str = self.get_activation_file()
            unit_name = auth_info_struct.unit_name
            sn = str(auth_info_struct.sn)
            sign_str = hashlib.md5((unit_name + sn).encode()).hexdigest()
            if sign_str == active_str:
                auth_info_struct.use_type = 3
                auth_info_struct.active = True
            else:
                auth_info_struct.use_type = 0
        else:
            # TODO: active_file_data[32:]是什么？只有一种情况进入宽限期？
            if active_file_data and len(active_file_data[32:]) > 2:
                auth_info_struct.use_type = 0
            elif active_file_data and len(active_file_data[32:]) <= 2:
                auth_info_struct.use_type = 1

        # self.ukey_close()
        return auth_info_struct


if __name__ == "__main__":
    ukey = Ukey(pub_pem="pub_keys.pem")
    # auth_info = ukey.read_auth_info()
    # ukey.ukey_open()
    # ret, file_data = ukey.ukey_read()
    # _encryt = EnDeCrypt()
    # # _encryt.pubDecrypt(file_data)
    # with open("cip", "wb") as f:
    #     f.write(file_data)
    # # create_cip()
    # _encryt.pubDecrypt(file_data)
    # ukey.check_and_open_ukey()
    ukey.read_license_info()
    auth_info = ukey.read_auth_info()
    logger.info(auth_info.json())
