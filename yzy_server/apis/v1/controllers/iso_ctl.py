from flask import jsonify, request, current_app, Response
import logging
import requests
import time
from yzy_server.database.apis import get_nodes_by_uuids
from common.utils import build_result, is_netmask, is_ip_addr, create_uuid, check_vlan_id


logger = logging.getLogger(__name__)


def down_iso_file(iso_file, sum_size = 11036459008):
    name1 = "test_%s"% time.time()
    down_url = "http://172.16.1.30:5000/api/v1/iso/download?filename=%s"% iso_file

    # "image_id": "5d6c7c81-27b8-4226-bc59-1609e258f845"

    r = requests.get(down_url, stream=True )
    f = open(r"{}.mp4".format(name1), "wb")
    t1 = time.time()
    logger.info('开始下载...........')
    sum = 0
    for chunk in r.iter_content(chunk_size=5 * 1024 * 1024):  # 每次下载
        if chunk:
            f.write(chunk)
            sum += len(chunk)

    def send_process():
        while 1:
            process = sum / sum_size# 每次读取20M
            if process > 100:
                break
            yield process

    response = Response(send_process(), content_type='application/octet-stream')
    # response.headers["Content-disposition"] = 'attachment; filename=%s' % fullfilename  # 如果不加上这行代码，导致下图的问题
    return response
    # logger.info('下载完成！！！ %s' % (time.time() - t1))
    # return build_result("Success")


def down_image_file(image_id, image_type):
    """
    通知各个计算节点下载镜像消息
    :param image_id: 镜像ID
    :param image_type: 镜像的类型,system or data
    :return:
    """
    nodes = get_nodes_by_uuids([])
    for node in nodes:
        if node.role != "compute":
            continue
        ip = node.ip
        url = "http://%s:50000/api/v1"% ip
        data = {
            "command": "download",
            "handler": "TemplateHandler",
            "data": {
                "image_id": image_id,
                "image_type": image_type,
                "endpoint": "http://172.16.1.56:5000",
                "url": "/api/v1/image/download"
            }
        }
        rep = requests.post(url, json=data)
        logger.info(rep.json())

    return build_result("Success")

