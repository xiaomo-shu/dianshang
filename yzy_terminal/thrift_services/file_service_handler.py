import sys
import os
import traceback
import logging
from yzy_terminal.thrift_protocols.terminal import FileService
from yzy_terminal.thrift_protocols.terminal.ttypes import *
from common.config import SERVER_CONF

dir_map = {FileType.LOG: SERVER_CONF.terminal.log_dir,
           FileType.SOFT: SERVER_CONF.terminal.soft_dir,
           FileType.PATCH: SERVER_CONF.terminal.patch_dir}



class FileServiceHandler:
    def get_file_size(self, file_name, file_type):  # ;(self, 1:string fileName);
        logging.debug("Terminal request: file_name {}, file_type {}".format(file_name, file_type))
        try:
            file_abs_path = dir_map[file_type] + "/" + file_name
            file_size = os.path.getsize(file_abs_path)
            logging.debug('{} size: {} '.format(file_abs_path, file_size))
            return file_size
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            return 0

    def read_bytes(self, read_info): # ;(self, 1:string fileName,2:i64 offset,3:i32 length);
        logging.debug("Terminal request: read_info {}".format(read_info))
        global dir_map
        file_abs_path = dir_map[read_info.file_type] + "/" + read_info.file_name
        if not os.path.exists(file_abs_path):
            logging.debug("Error Exeption file not exists {}".format(file_abs_path))
            return None
        fd = None
        try:
            fd = open(file_abs_path, 'rb')
            fd.seek(read_info.operate_offset)
            read_data = fd.read(read_info.operate_length)
            fd.close()
            return read_data
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            fd.close()
            return None

    def write_bytes(self, write_info, data): # ;(self, 1:string fileName,2:i64 offset,3:i32 length);
        logging.debug("Terminal request: write_info {}, data length {}".format(write_info, len(data)))
        global dir_map
        if len(data) == 0:
            logging.warning("write zero data length ")
            return True
        # if directory not exists, then create it
        if not os.path.exists(dir_map[write_info.file_type]):
            os.mkdir(dir_map[write_info.file_type])
        file_abs_path = dir_map[write_info.file_type] + "/" + write_info.file_name
        ok_file_abs_path = dir_map[write_info.file_type] + "/" + write_info.file_name.split('.')[0] + '.ok'
        fd = None
        try:
            fd = open(file_abs_path, 'ab')
            fd.seek(write_info.operate_offset)
            fd.truncate()
            write_len = fd.write(data)
            fd.close()
            if write_info.operate_offset + write_len == write_info.total_size:
                fd_ok_file = open(ok_file_abs_path, 'wb')
                fd_ok_file.close()
            return True
        except Exception as err:
            logging.error(err)
            logging.error(''.join(traceback.format_exc()))
            fd.close()
            return False

