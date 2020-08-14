import requests
import time
name = "test3"
name1 = "test11"
# down_url = "http://172.16.1.30:5000/api/v1/iso/download?filename=12"
down_url = "http://172.16.1.11:50001/api/v1/template/download?image_id=5d6c7c81-27b8-4226-bc59-1609e258f845"
r = requests.get(down_url)
f = open(r"{}.mp4".format(name1), "wb")
t1 = time.time()
print('开始下载视频' )
for chunk in r.iter_content(chunk_size=5 * 1024 * 1024):# 每次下载
    if chunk:
        f.write(chunk)
print('视频下载完成！！！ %s'% (time.time() - t1))
