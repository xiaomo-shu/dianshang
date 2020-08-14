import os

# Binary kilo unit
Ki = 1024
# Binary mega unit
Mi = Ki ** 2

Gi = Ki ** 3

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_DIR = "/usr/local/yzy-kvm"
SERVER_DEFAULT_PORT = 50000
SCHEDULER_DEFAULT_PORT = 50009
COMPUTE_DEFAULT_PORT = 50001
MONITOR_DEFAULT_PORT = 50002
TERMINAL_DEFAULT_PORT = 50003
WEB_DEFAULT_PORT = 50004
VOI_TERMINAL_DEFAULT_PORT = 50005

CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'yzy_kvm.ini')
EDUCATION_TYPE = 1
PERSONAL_TYPE = 2
DEFAULT_SYS_PATH = '/opt/instances'
DEFAULT_DATA_PATH = '/opt/datas'
IMAGE_CACHE_DIRECTORY_NAME = '_base'
DEFAULT_ISO_PATH = '/opt/iso/'
IMAGE_FILE_PREFIX = 'version_%s_'
LOG_FILE_PATH = '/var/log/yzy_kvm/'
LOG_DOWN_PATH = '/var/log/yzy_kvm/log_down'

# 终端日志文件地址
TERMINAL_LOG_PATH = '/opt/terminal/log/'
TERMINAL_UPGRADE_PATH = '/opt/terminal/soft/'

# 存储角色
TEMPLATE_SYS = 1
TEMPLATE_DATA = 2
INSTANCE_SYS = 3
INSTANCE_DATA = 4

# 磁盘角色，系统盘/数据盘
IMAGE_TYPE_SYSTEM = 'system'
IMAGE_TYPE_DATA = 'data'

# 个人桌面中的随机桌面
RANDOM_DESKTOP = 1
# 个人桌面中的静态桌面
STATIC_DESKTOP = 2

# 终端状态
TERMINAL_OFFLINE = 0
TERMINAL_ONLINE = 1

# 状态相关
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_SHUTDOWN = "shutdown"
STATUS_RESTARTING = "restarting"
STATUS_SHUTDOWNING = "shutdowning"
STATUS_UPDATING = "updating"
STATUS_ERROR = "error"
STATUS_DOWNLOADING = "downloading"
STATUS_DELETING = "deleting"

MAX_THREADS = 8

SHUTDOWN_TIMEOUT = 90

IMAGE_TYPE = {
    'windows_xp': 'winxp',
    'windows_7': 'win7',
    'windows_7_x64': 'win7',
    'windows_8': 'win8',
    'windows_8_x64': 'win8',
    'windows_10': 'win10',
    'windows_10_x64': 'win10',
    'linux': 'linux',
    'Linux': 'linux',
    'other': 'other',
    'Other': 'other'
}


# IMAGE_TYPE_REVERT = {
#     'windows_xp': 'Windows XP',
#     'windows_7': 'Windows 7 32 bit',
#     'windows_7_x64': 'Windows 7 64 bit',
#     'windows_8': 'Windows 8 32 bit',
#     'windows_8_x64': 'Windows 8 64 bit',
#     'windows_10': 'Windows 10 32 bit',
#     'windows_10_x64': 'Windows 10 64 bit',
#     'linux': 'Linux',
#     'other': 'Other'
# }

# VOI共享盘大小 单位G
VOI_SHARE_DISK_MIN = 5
VOI_SHARE_DISK_MAX = 500

# VOI共享盘前缀
VOI_SHARE_BASE_PREFIX = 'voi_%s_'

# 网卡Bond支持的类型
BOND_MODE = {
    0: "balance-rr",
    1: "active-backup",
    6: "balance-alb"
}
# 节点角色
ROLE_MASTER_AND_COMPUTE = 1
ROLE_SLAVE_AND_COMPUTE = 2
ROLE_MASTER = 3
ROLE_SLAVE = 4
ROLE_COMPUTE = 5
