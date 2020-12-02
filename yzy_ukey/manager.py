import os
import sys
project_dir = os.path.abspath("..")
sys.path.insert(0, project_dir)

from common import load_log_config
load_log_config('yzy_ukey')

from yzy_ukey.server import UkeyTcpServer


if __name__ == "__main__":
    UkeyTcpServer().run()
