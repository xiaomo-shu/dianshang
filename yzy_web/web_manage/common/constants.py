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
UKEY_DEFAULT_PORT = 50010

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
TERMINAL_RESOURCES_PATH = "/opt/terminal_resources.xlsx"
TERMINAL_HARDWARE_PATH = "/opt/terminal_hardware.xlsx"

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
IMAGE_COMMIT_VERSION = 2

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

# 节点应有的服务
COMPUTE_SERVICE = ["libvirtd", "yzy-compute", "yzy-monitor", "yzy-upgrade"]
NETWORK_SERVICE = ["mariadb", "nginx", "redis", "yzy-web", "yzy-server", "yzy-terminal",
                   "ukey", "top_server", "yzy-terminal-agent", "torrent"]
MASTER_SERVICE = COMPUTE_SERVICE + NETWORK_SERVICE

# 教学分组
EDUCATION_GROUP = 1
# 用户分组
PERSONAL_GROUP = 2

# 课表已启用
COURSE_SCHEDULE_ENABLED = 1
# 课表已禁用
COURSE_SCHEDULE_DISABLED = 0

# 本周有课表
WEEK_OCCUPIED = 1
# 本周无课表
WEEK_NOT_OCCUPIED = 0

# 学期有课表
TERM_OCCUPIED = 1
# 学期无课表
TERM_NOT_OCCUPIED = 0

# BT传输任务类型
BT_DOWNLOAD_TASK = 1
BT_UPLOAD_TASK = 2

# 任务信息状态
TASK_ERROR = "error"
TASK_RUNNING = "running"
TASK_QUEUE = "queue"
TASK_COMPLETE = "complete"

# 任务名称及类型映射关系
NAME_TYPE_MAP = {
    1: "上传镜像",
    2: "发布镜像",
    3: "桌面组批量开机",
    4: "桌面组批量关机",
    5: "桌面组批量重启",
    6: "导出用户数据",
    7: "新建模板",
    8: "复制模板",
    9: "下载模板",
    10: "桌面定时开关机",
    11: "节点定时关机",
    12: "终端定时关机",
    13: "差异盘同传",
    14: "系统盘创建"
}

CHUNKSIZE = Ki * 64  # 64kB

WEB_CLIENT_ID = 101

NFS_MOUNT_POINT_PREFIX = '/opt/nfs_'