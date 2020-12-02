import os

EXT_IONICE = '@IONICE_PATH@'

EXT_KILL = '@KILL_PATH@'

EXT_NICE = '@NICE_PATH@'

EXT_SETSID = '@SETSID_PATH@'
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = '/usr/local/yzy-kvm/'
LOG_PATH = '/var/log/yzy_kvm/'
TERMINAL_LOG_PATH = '/var/log/yzy_kvm/terminal/'

################ compute ########################
# Binary kilo unit
Ki = 1024
# Binary mega unit
Mi = Ki ** 2

Gi = Ki ** 3

# below is host architecture
I686 = 'i686'
X86_64 = 'x86_64'
DEFAULT_MACH_TYPE = 'pc-i440fx-rhel7.2.0'
VOI_MACH_TYPE = 'pc-q35-rhel7.6.0'
DEFAULT_CONFIGDRIVE_PATH = '/opt'

# the default config path
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'yzy_kvm.ini')

# Linux interface max length
DEVICE_NAME_MAX_LEN = 15
MAX_VLAN_POSTFIX_LEN = 5

IP_VERSION_4 = 4
IP_VERSION_6 = 6
IPv4_BITS = 32
IPv6_BITS = 128

BRIDGE_NAME_PREFIX = "brq"
RESOURCE_ID_LENGTH = 11
FLAT_NETWORK_TYPE = 'Flat'
VLAN_NETWORK_TYPE = 'Vlan'
IPv4_ANY = '0.0.0.0/0'
IPv6_ANY = '::/0'
IP_ANY = {IP_VERSION_4: IPv4_ANY, IP_VERSION_6: IPv6_ANY}

IMAGE_TYPE_SYSTEM = 'system'
IMAGE_TYPE_DATA = 'data'
IMAGE_TYPE_SHARE = 'share'
IMAGE_CACHE_DIRECTORY_NAME = '_base'
DISK_FILE_PREFIX = 'disk-'
IMAGE_FILE_PREFIX = 'version_%s_'
IMAGE_COMMIT_VERSION = 2
DISK_TYPE_DEFAULT = 'disk'
INSTANCE_BASE_NAME = 'instance-%08x'
TEMPLATE_BASE_NAME = 'template-%08x'
VOI_FILE_PREFIX = 'voi-'
VOI_BASE_PREFIX = 'voi_%s_'
VOI_SHARE_BASE_PREFIX = 'voi_%s_'
VOI_BASE_NAME = 'voi-%08x'
TFTP_PATH = "/var/lib/tftpboot"
DHCP_CONF = "/etc/dhcp/dhcpd.conf"
DOMAIN_STATE = {
    'nostate': 0,       # no state
    'running': 1,       # the domain is running
    'blocked': 2,       # the domain is blocked on resource
    'paused': 3,        # the domain is paused by user
    'shutdown': 4,      # the domain is being shut down
    'shutoff': 5,       # the domain is shut off
    'crashed': 6,       # the domain is crashed
    'pmsuspended': 7,   # the domain is suspended by guest power management
}
SOFT_REBOOT_SECONDS = 120
DOMAIN_START_WAIT = 10
HARD_REBOOT = 'hard'
SOFT_REBOOT = 'soft'
SYSTEM_BOOT_INDEX = 0

# the virtual machine os type
OS_TYPE_LINUX = 'linux'
OS_TYPE_WINDOWS = 'windows'
OS_TYPE_XP = 'winxp'

_ISO8601_TIME_FORMAT_SUBSECOND = '%Y-%m-%dT%H:%M:%S.%f'
_ISO8601_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
PERFECT_TIME_FORMAT = _ISO8601_TIME_FORMAT_SUBSECOND

CHUNKSIZE = Ki * 64  # 64kB

SERVER_DEFAULT_PORT = 50000
COMPUTE_DEFAULT_PORT = 50001
MONITOR_DEFAULT_PORT = 50002
TERMINAL_DEFAULT_PORT = 50003
VOI_TERMINAL_DEFAULT_PORT = 50005
VOI_TERMINAL_LISTEN_DEFAULT_PORT = 50007
UPGRADE_DEFAULT_PORT = 50008
SCHEDULER_DEFAULT_PORT = 50009
UKEY_DEFAULT_PORT = 50010
WARNING_PLATFORM_PORT = 50011

VOI_TERMINAL_UPGRADE_PORT=50019

BT_TERMINAL_HTTP_PORT = 50020
BT_FILE_TRANS_PORT = 50021
BT_SERVER_API_PORT = 50022

DEFAULT_SPICE_PORT = 5900

QEMU_AUTO_START_DIR = "/opt/qemu/autostart"

BOND_MASTERS = "/sys/class/net/bonding_masters"
BOND_SLAVES = "/sys/devices/virtual/net/%s/bonding/slaves"
############## server #####################
TOKEN_PATH = '/opt/token'
WEBSOCKIFY_PORT = 6080
VOI_POOL_DIR_NAME = 'voi_pool'
DEFAULT_SYS_PATH = '/opt/instances'
DEFAULT_DATA_PATH = '/opt/datas'
DEFAULT_TORRENT_PATH = '/opt/torrent'
VIRTIO_PATH = '/opt/iso/virtio-win.iso'
TERMINAL_RESOURCES_PATH = "/opt/terminal_resources.xlsx"
TERMINAL_HARDWARE_PATH = "/opt/terminal_hardware.xlsx"
SERVER_SYNC_URL = "/api/v1/image/download"
IMAGE_SYNC_URL = "/api/v1/resource_pool/images/download"
HA_SYNC_URL = "/api/v1/node/ha_sync"
DATABASE_BACK_PATH = "/opt/db_back"
ROLE_MASTER_AND_COMPUTE = 1
ROLE_SLAVE_AND_COMPUTE = 2
ROLE_MASTER = 3
ROLE_SLAVE = 4
ROLE_COMPUTE = 5
STATUS_ACTIVE = "active"
STATUS_SHUTDOWN = "shutdown"
STATUS_RESTARTING = "restarting"
STATUS_SHUTDOWNING = "shutdowning"
STATUS_DELETING = "deleting"
STATUS_INACTIVE = "inactive"
STATUS_UPDATING = "updating"
STATUS_SAVING = "saving"
STATUS_ERROR = "error"
STATUS_CREATING = "creating"
STATUS_C_CREATING = "c_creating"
STATUS_INSTALL = "installing"
STATUS_ROLLBACK = "rollback"
STATUS_COPING = "coping"
STATUS_DOWNLOADING = "downloading"
STATUS_UPLOADING = "uploading"
COMPUTE_SERVICE = ["libvirtd", "yzy-compute", "yzy-monitor", "yzy-upgrade"]
NETWORK_SERVICE = ["mariadb", "nginx", "redis", "yzy-web", "yzy-server", "yzy-terminal",
                   "ukey", "top_server", "yzy-terminal-agent", "torrent"]
MASTER_SERVICE = COMPUTE_SERVICE + NETWORK_SERVICE
MAX_THREADS = 8
DEFAULT_MAX_WORKER = 12

# IP系统分配
ALLOCATE_SYS_TYPE = 1
# IP固定分配
ALLOCATE_FIX_TYPE = 2

# 个人桌面中的随机桌面
RANDOM_DESKTOP = 1
# 个人桌面中的静态桌面
STATIC_DESKTOP = 2

# 教学分组
EDUCATION_GROUP = 1
# 用户分组
PERSONAL_GROUP = 2

# 教学桌面
EDUCATION_DESKTOP = 1
# 个人桌面
PERSONAL_DEKSTOP = 2
# 系统桌面
SYSTEM_DESKTOP = 3

# 存储角色
TEMPLATE_SYS = 1
TEMPLATE_DATA = 2
INSTANCE_SYS = 3
INSTANCE_DATA = 4

TEMPLATE_SCHEDULER_PATH = os.path.join(DEFAULT_CONFIGDRIVE_PATH, 'scheduler')
SCHEDULER_MONTH_DAY = 28

# 模板属性关于磁盘的标识
DEVICE_NEED_DELETED = 1
DEVICE_NEED_ADDED = 2


# BT传输任务类型
BT_DOWNLOAD_TASK = 1
BT_UPLOAD_TASK = 2

# BT任务状态
# BT_TASK_INIT = 0
# BT_TASK_CHECKING = 1
# BT_TASK_DOWNING = 2
# BT_TASK_SEEDING = 3
# BT_TASK_FINISH = 5

# BT任务状态
BT_TASK_INIT = 0
BT_TASK_CHECKING_OR_DOWNING = 1
BT_TASK_FINISH = 2
BT_TASK_SEEDING = 3
# BT_TASK_FINISH = 5

# socket buff
BUF_SIZE = 1024 * 1024

PARALELL_QUEUE = 'yzy_parallel_queue'
AUTH_SIZE_KEY = 'yzy_auth_num'
PARALELL_NUM = 20
CHRONYD_CONF = "/etc/chrony.conf"
LV_PATH_PREFIX = '/opt'

# HA相关状态
HA_STATUS_NORMAL = 0
HA_STATUS_FAULT = 1
HA_STATUS_UNKNOWN = 2


# 课表已启用
COURSE_SCHEDULE_ENABLED = 1
# 课表已禁用
COURSE_SCHEDULE_DISABLED = 0

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

LICENSE_DIR = os.path.join(BASE_DIR, "license")
READ_UKEY_INTERVAL = 1 * 60
CID = b'yzy'
VERSION = 1
IS_REQ = 0
IS_RESP = 1
SEQ_ID = 0
CLIENT_ID = 0
SERVER_CLIENT_ID = 201
NFS_MOUNT_POINT_PREFIX = '/opt/nfs_'