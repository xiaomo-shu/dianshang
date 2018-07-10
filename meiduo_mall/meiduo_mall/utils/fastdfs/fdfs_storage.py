from django.conf import settings
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.utils.deconstruct import deconstructible


@deconstructible
class FastDFSStorage(Storage):
    """自定义文件存储类"""
    def __init__(self, base_url=None, client_conf=None):
        """
        初始化
        :param base_url: 用于构造图片完整路径使用，图片服务器的域名
        :param client_conf: FastDFS客户端配置文件的路径
        """
        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

    def _save(self, name, content):
        """
        :param name: 上传文件名称
        :param content: 包含上传文件内容的File对象
        :return:
        """
        client = Fdfs_client(self.client_conf)

        ret = client.upload_by_buffer(content.read())

        if ret.get("Status") != "Upload successed.":
            raise Exception("upload file failed")
        file_name = ret.get("Remote file_id")
        return file_name

    def exists(self, name):
        """
        :param name: 上传文件的名称
        :return:
        """
        return False

    def url(self, name):
        """
        返回文件的完整URL路径
        :param name: 数据库中保存的文件名
        :return: 完整的URL
        """
        return self.base_url + name

