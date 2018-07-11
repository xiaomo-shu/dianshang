import base64
import pickle
from django.test import TestCase

# Create your tests here.


if __name__ == "__main__":
    # cart_dict = {
    #     1: {
    #         'count': 2,
    #         'selected': True
    #     },
    #     3: {
    #         'count': 1,
    #         'selected': True
    #     },
    # }
    #
    # res_data = pickle.dumps(cart_dict) # bytes
    # res_data = base64.b64encode(res_data) # bytes
    # res_data = res_data.decode()
    # print(res_data)

    # cart_data = b'\x80\x03}q\x00(K\x01}q\x01(X\x05\x00\x00\x00countq\x02K\x02X\x08\x00\x00\x00selectedq\x03\x88uK\x03}q\x04(h\x02K\x01h\x03\x88uu.'
    # cart_dict = pickle.loads(cart_data)
    # print(cart_dict)

    cart_data = 'gAN9cQAoSwF9cQEoWAgAAABzZWxlY3RlZHECiFgFAAAAY291bnRxA0sCdUsDfXEEKGgCiGgDSwF1dS4='
    cart_data = cart_data.encode()
    cart_data = base64.b64decode(cart_data)
    cart_dict = pickle.loads(cart_data)
    print(cart_dict)
