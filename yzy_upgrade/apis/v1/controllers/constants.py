import os
UPGRADE_DEFAULT_PORT = 50008

UPGRADE_FILE_PATH = "/opt/upgrade"
UPGRADE_TMP_PATH = "/tmp/upgrade"
UPGRADE_KVM_PATH = os.path.join(UPGRADE_TMP_PATH, "yzy_kvmprojects")
SELF_UPGRADE_FLAG = os.path.join(UPGRADE_KVM_PATH, "need_self_upgrade")
UPGRADE_BACKUP_PATH = "/usr/local/upgrade_backup"
UPGRADE_SCRIPT_RELATIVE_PATH = "upgrade_scripts/upgrade/main.sh"
ROLLBACK_SCRIPT_RELATIVE_PATH = "upgrade_scripts/rollback/main.sh"
UPGRADE_FILE_SYNC_URL = "/api/v1/index/sync"
UPGRADE_FILE_DOWNLOAD_URL = "/api/v1/index/download"
SELF_UPGRADE_FILE = "/tmp/self_upgrade"

STATUS_SHUTDOWN = "shutdown"
STATUS_INACTIVE = 'inactive'
STATUS_UPDATING = "updating"
STATUS_SAVING = "saving"
STATUS_CREATING = "creating"
STATUS_C_CREATING = "c_creating"
STATUS_INSTALL = "installing"
STATUS_ROLLBACK = "rollback"
STATUS_COPING = "coping"

ROLE_MASTER_AND_COMPUTE = 1
ROLE_SLAVE_AND_COMPUTE = 2
ROLE_MASTER = 3
ROLE_SLAVE = 4
ROLE_COMPUTE = 5

# 存储角色
TEMPLATE_SYS = 1
TEMPLATE_DATA = 2
IMAGE_TYPE_SYSTEM = 'system'
IMAGE_TYPE_DATA = 'data'

# Binary kilo unit
Ki = 1024
CHUNKSIZE = Ki * 64  # 64kB
MAX_THREADS = 8
