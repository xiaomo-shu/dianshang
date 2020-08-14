import os

EXT_IONICE = '@IONICE_PATH@'

EXT_KILL = '@KILL_PATH@'

EXT_NICE = '@NICE_PATH@'

EXT_SETSID = '@SETSID_PATH@'
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = '/usr/local/yzy-kvm/'
LOG_PATH = '/var/log/yzy_kvm/'

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
COMPUTE_SERVICE = ["libvirtd", "yzy-compute", "yzy-monitor", "yzy_upgrade"]
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

# socket buff
BUF_SIZE = 1024 * 1024

PARALELL_QUEUE = 'yzy_parallel_queue'
PARALELL_NUM = 20


