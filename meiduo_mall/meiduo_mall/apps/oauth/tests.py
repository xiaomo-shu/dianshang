from django.test import TestCase
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
# Create your tests here.


if __name__ == "__main__":
    ## pip install itsdangerous
    secret_key = 'smart'
    # 使用itsdanagerous包进行数据加密
    req_dict = {'openid': 'xlakdkdk9911200929kkdkd'}
    serializer = Serializer(secret_key=secret_key, expires_in=3)
    res_data = serializer.dumps(req_dict) # bytes
    print(res_data)

    import time
    time.sleep(5)

    try:
        serializer2 = Serializer(secret_key='smart', expires_in=3)
        res_dict = serializer2.loads(res_data)
        print(res_dict)
    except BadData as e:
        print(e)

    # req_dict = {
    #     'name': 'python',
    #     'age': 18
    # }

    # 把字典数据转换成查询字符串
    # res_data = urlencode(req_dict)
    # print(type(res_data))
    # print(res_data)

    # query_str = "name=itcast&age=11&age=12"
    # # 把查询字符串转化成字典，需要注意: 字典中key对应value是list
    # res_dict = parse_qs(query_str)
    # print(type(res_dict))
    # print(res_dict)

    # 发起一个网络请求
    # req_url = 'http://api.meiduo.site:8000/mobiles/13155667788/count/'
    # response = urlopen(req_url)
    # res_data = response.read() # bytes
    # print(type(res_data))
    # print(res_data)






