import os
import hashlib
import logging
from common.http import HTTPClient
from .image_data import ImageService


class NodeService(object):

    def __init__(self, **kwargs):
        self.endpoint = kwargs.get('endpoint', None)
        if self.endpoint:
            self.http_client = HTTPClient(self.endpoint, timeout=600)

    def ha_sync(self, url, path, md5=None):
        if not os.path.exists(path):
            dir_path = os.path.dirname(path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            self.download(url, path, md5)
        else:
            logging.debug("the file %s already exists", path)

    def download(self, url, path, md5=None):
        try:
            logging.info("sync the file:%s", path)
            # the stream args must be true, otherwise the download will be failed
            url = '%s?path=%s' % (url, path)
            resp, image_chunks = self.http_client.get(url)
        except Exception as e:
            logging.error("sync error:%s", e)
            raise

        logging.info("data is none, open the dst_path:%s", path)
        data = open(path, 'wb')
        close_file = True

        if data is None:
            return image_chunks
        else:
            md5_sum = hashlib.md5()
            try:
                for chunk in image_chunks:
                    md5_sum.update(chunk)
                    data.write(chunk)
                if md5:
                    logging.info("check md5, source:%s, file:%s", md5, md5_sum.hexdigest())
                    if md5_sum.hexdigest() != md5:
                        logging.error("the source md5_sum:%s, the dest md5_sum:%s", md5, md5_sum.hexdigest())
                        raise Exception("the file md5 sum check failed")
            except Exception as ex:
                logging.error("Error writing to %(path)s: %(exception)s",
                              {'path': path, 'exception': ex})
                try:
                    os.remove(path)
                except:
                    pass
                raise ex
            finally:
                if close_file:
                    # Ensure that the data is pushed all the way down to
                    # persistent storage. This ensures that in the event of a
                    # subsequent host crash we don't have running instances
                    # using a corrupt backing file.
                    data.flush()
                    ImageService()._safe_fsync(data)
                    data.close()
