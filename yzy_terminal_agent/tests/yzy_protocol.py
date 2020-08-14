from ctypes import *

class YzyProtocolPaket(Structure):
    pass

YzyProtocolPaket._fields_= [

]

class YzyProtocol:

    def __init__(self):
        self.libc = cdll.LoadLibrary("./libyzyProtocol.so")
        self.libc.u32YzyProtocol_PaketCreate.argtypes = [c_int, c_int, c_int, c_int, c_wchar_p,
                                                         c_int, c_int, c_int, c_wchar_p, c_int, c_wchar_p]
        # self.libc.u32YzyProtocol_PaketCreate.restype =

    def create_paket(self, service_code, data_size, data_type, encoding, pu_payload, client_type, req_or_res,
                     token_len, p_token, pu_pkt_size, ppv_pkt_data):
        ret = self.libc.u32YzyProtocol_PaketCreate(service_code, data_size, data_type, encoding, pu_payload, client_type,
                                                   req_or_res, token_len, p_token, pu_pkt_size, ppv_pkt_data)

        return ret


if __name__ == "__main__":
    yzy_protocol = YzyProtocol()
    service_code = 1
    data_size = 50
    data_type = 1
    encoding = 0
    pu_payload = b"hello"
    client_type = 1
    req_or_res = 1
    token = b"12345678"
    token_len = len(token)
    pk_size = c_int()
    pk_ret = create_string_buffer(8196)

    ret = yzy_protocol.create_paket(service_code, data_size, data_type, encoding, pu_payload, client_type, req_or_res,
                                    token_len, token, pk_size, pk_ret)
    print(">>>: %s"% ret)
    print("<<<: %s"% pk_ret.value)



