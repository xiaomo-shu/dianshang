# coding: utf-8
import json
import datetime
from sqlalchemy import CHAR, Column, DateTime, Index, String, text, Float, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, BIGINT, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = Base.metadata


class BaseModelCtrl(object):
    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in values.items():
            setattr(self, k, v)

    def delete(self):
        self.deleted = True
        self.deleted_at = datetime.datetime.utcnow()


class YzyVoiTerminal(Base, BaseModelCtrl):
    __tablename__ = 'yzy_voi_terminal'
    __table_args__ = (
        Index('terminal_id_ip_index', 'terminal_id', 'ip'),
    )

    id = Column(INTEGER(11), primary_key=True, comment='VOI终端信息表')
    uuid = Column(String(64), nullable=False, comment='终端uuid')
    terminal_id = Column(INTEGER(11), nullable=False, comment='终端序号,不同组可以重复')
    name = Column(String(64), nullable=False, comment='终端名称')
    status = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='终端状态: 0-离线 1-在线，2-维护状态，3-部署状态，4-UEFI模式')
    ip = Column(String(16), nullable=False, comment='终端IP地址')
    mac = Column(String(20), nullable=False, unique=True, comment='终端MAC地址')
    mask = Column(String(15), nullable=False, comment='子网掩码')
    gateway = Column(String(15), nullable=False, comment='网关地址')
    dns1 = Column(String(15), nullable=False)
    dns2 = Column(String(15))
    is_dhcp = Column(CHAR(1), nullable=False, server_default=text("'1'"), comment='dhcp: 1-自动 0-静态')
    platform = Column(String(20), nullable=False, comment='终端CPU架构: arm/x86')
    soft_version = Column(String(50), nullable=False, comment='终端程序版本号: 16.3.8.0')
    register_time = Column(DateTime)
    conf_version = Column(String(20), nullable=False, comment='终端配置版本号')
    setup_info = Column(String(1024), comment='终端设置信息:模式、个性化、windows窗口')
    group_uuid = Column(CHAR(64), comment='组UUID，默认NULL表示未分组')
    disk_residue = Column(Float, comment='剩余磁盘容量，单位：G')
    deleted = Column(BIGINT(11), server_default=text("0"), comment='删除标记')
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_json(self):
        return {
            "terminal_id": self.terminal_id,
            "name": self.name,
            "mac": self.mac,
            "ip": self.ip,
            "mask": self.mask,
            "gateway": self.gateway,
            "dns1": self.dns1,
            "dns2": self.dns2,
            "is_dhcp": int(self.is_dhcp),
            "platform": self.platform,
            "conf_version": int(self.conf_version),
            "soft_version": self.soft_version,
            "setup_info": json.loads(self.setup_info),
            "disk_residue": self.disk_residue
        }

# CREATE TABLE `yzy_voi_torrent_task` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '任务',
#   `uuid` varchar(64) NOT NULL COMMENT '任务uuid',
#   `torrent_name` varchar(64) NOT NULL COMMENT '种子名称',
#   `torrent_path` varchar(200) NOT NULL COMMENT '种子路径',
#   `torrent_size` int(11) NOT NULL DEFAULT 0 COMMENT '种子文件大小',
#   `template_uuid` varchar(64) NOT NULL COMMENT '对应模板uuid',
#   `disk_name` varchar(64) NOT NULL COMMENT '磁盘名称',
#   `terminal_mac` varchar(32) NOT NULL COMMENT '终端mac',
#   `type` tinyint(1) NOT NULL COMMENT '任务类型，0-上传，1-下载',
#   `status` tinyint(1) NOT NULL DEFAULT 0 COMMENT '任务状态，0-初始状态，1-进行中，2-完成',
#   `process` int(5) NOT NULL DEFAULT 0 COMMENT '任务进度',
#   `deleted` bigint(11) NOT NULL DEFAULT 0 COMMENT '删除标志',
#   `deleted_at` datetime DEFAULT NULL,
#   `created_at` datetime DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8


class YzyVoiTorrentTask(Base, BaseModelCtrl):
    __tablename__ = "yzy_voi_torrent_task"
    id = Column(INTEGER(11), primary_key=True, comment='bt上传下载任务id')
    uuid = Column(String(64), nullable=False, comment='任务uuid')
    torrent_id = Column(String(64), nullable=False, comment='种子id')
    torrent_name = Column(String(64), nullable=False, comment='种子名称')
    torrent_path = Column(String(200), nullable=False, comment='种子路径')
    torrent_size = Column(String(64), nullable=False,
                    comment='种子文件大小')
    desktop_name = Column(String(32), nullable=False, comment='桌面组名称')
    template_uuid = Column(String(64), nullable=False, comment='对应模板uuid')
    disk_uuid = Column(String(64), nullable=False, comment='磁盘uuid')
    disk_name = Column(String(64), nullable=False, comment='磁盘名称')
    disk_size = Column(Float, comment='磁盘文件大小，单位：G', nullable=False)
    disk_type = Column(String(32), comment='磁盘类型, system/data', nullable=False)
    save_path = Column(String(200), nullable=False, comment='文件保存路径')
    terminal_mac = Column(String(32), nullable=False, comment='终端mac')
    terminal_ip = Column(String(32), nullable=False, comment='终端ip')
    type = Column(TINYINT(1), nullable=False, comment='任务类型，0-上传，1-下载')
    status = Column(TINYINT(1), nullable=False, comment='任务状态，0-初始状态，1-进行中，2-完成')
    state = Column(String(32), server_default=text(""), nullable=False, comment='任务状态')
    process = Column(INTEGER(11), nullable=False, comment='任务百分比')
    download_rate = Column(INTEGER(11), nullable=False, comment='下载速率', default=0)
    upload_rate = Column(INTEGER(11), nullable=False, comment='上传速率', default=0)
    batch_no = Column(INTEGER(11), nullable=False, comment='任务批次号', default=0)
    sum = Column(INTEGER(5), nullable=False, comment='批次任务总数', default=1)
    deleted = Column(INTEGER(11), server_default=text("0"), nullable=False, comment='删除标志')
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "uuid": self.uuid,
            "torrent_id": self.torrent_id,
            "torrent_path": self.torrent_path,
            "desktop_name": self.desktop_name,
            "template_uuid": self.template_uuid,
            "disk_uuid": self.disk_uuid,
            "disk_name": self.disk_name,
            "disk_type": self.disk_type,
            "save_path": self.save_path
        }


class YzyAdminUser(Base, BaseModelCtrl):
    __tablename__ = 'yzy_admin_user'

    id = Column(BIGINT(11), primary_key=True, comment='管理员用户id')
    username = Column(String(32), nullable=False, comment='账号')
    password = Column(String(64), nullable=False, comment='密码')
    last_login = Column(DateTime, nullable=False, comment='上次登录时间')
    login_ip = Column(String(20), nullable=False, server_default=text("''"), comment='登录ip')
    real_name = Column(String(64), nullable=False, server_default=text("''"), comment='真实姓名')
    role_id = Column(BIGINT(11), nullable=False, comment='角色id')
    email = Column(String(100), nullable=False, server_default=text("''"), comment='email')
    is_superuser = Column(TINYINT(1), nullable=False, server_default=text("0"), comment='是否为超级管理员，0-否，1-是')
    is_active = Column(TINYINT(1), nullable=False, server_default=text("1"), comment='是否激活，0-否，1-是')
    desc = Column(String(200), comment='备注')
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='删除标志')
    deleted_at = Column(DateTime)
    updated_at = Column(DateTime)
    created_at = Column(DateTime)


class YzyNode(Base, BaseModelCtrl):
    __tablename__ = 'yzy_nodes'

    id = Column(INTEGER(11), primary_key=True, comment='服务器节点')
    uuid = Column(String(64), nullable=False, comment='节点uuid')
    ip = Column(String(20), nullable=False, comment='节点ip')
    name = Column(String(64), nullable=False, comment='节点别称')
    hostname = Column(String(64), nullable=False, comment='节点名称')
    resource_pool_uuid = Column(String(64), nullable=False, server_default=text("''"), comment='资源池uuid')
    total_mem = Column(INTEGER(11), nullable=False, comment='节点内存，单位：GB')
    running_mem = Column(INTEGER(11), nullable=False, comment='启动内存，单位：GB')
    single_reserve_mem = Column(INTEGER(11), nullable=False, comment='虚机预留内存，单位：GB')
    total_vcpus = Column(INTEGER(11), nullable=False, comment='节点cpu核数')
    running_vcpus = Column(INTEGER(11), nullable=False, comment='运行cpu核数')
    cpu_utilization = Column(Float(4), comment='运行cpu核数')
    mem_utilization = Column(Float(4), comment='运行cpu核数')
    status = Column(String(20), nullable=False, comment='节点状态  active - 正常开机， abnormal - 异常警告，shutdown - 关机')
    server_version_info = Column(String(64))
    gpu_info = Column(String(100))
    cpu_info = Column(String(100))
    mem_info = Column(String(100))
    sys_img_uuid = Column(String(64))
    data_img_uuid = Column(String(64))
    vm_sys_uuid = Column(String(64))
    vm_data_uuid = Column(String(64))
    type = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='1、计算和主控一体\\n2、计算和备控一体\\n3、主控\\n4、备控\\n5、计算')
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='删除标记')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, comment='创建时间')
    updated_at = Column(DateTime, comment='更新时间')


class YzyInterfaceIp(Base, BaseModelCtrl):
    __tablename__ = 'yzy_interface_ip'

    id = Column(BIGINT(11), primary_key=True, comment='子网卡id')
    uuid = Column(String(64), nullable=False, comment='子网卡uuid')
    name = Column(String(64), nullable=False, comment='网卡子ip名称')
    nic_uuid = Column(String(64), nullable=False, comment='网卡uuid')
    ip = Column(String(32), comment='ip地址')
    netmask = Column(String(32), comment='子网掩码')
    gateway = Column(String(32), comment='网关地址')
    dns1 = Column(String(32), server_default=text("''"), comment='DNS1')
    dns2 = Column(String(32), server_default=text("''"), comment='DNS2')
    is_image = Column(TINYINT(1), server_default=text("0"), comment='状态, 0-非镜像网络，1-镜像网络')
    is_manage = Column(TINYINT(1), server_default=text("0"), comment='状态, 0-非管理网络，1-管理网络')
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='删除标志')
    deleted_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class YzyNodeNetworkInfo(Base, BaseModelCtrl):
    __tablename__ = 'yzy_node_network_info'

    id = Column(INTEGER(11), primary_key=True, comment='节点网络信息')
    uuid = Column(String(64), nullable=False, comment='节点网络uuid')
    nic = Column(String(32), nullable=False, comment='网络接口名称')
    mac = Column(String(32), comment='mac地址')
    node_uuid = Column(String(64), nullable=False, comment='节点uuid')
    speed = Column(INTEGER(11), comment='速度')
    type = Column(TINYINT(1), server_default=text("0"), comment='0-Ethernet，1-bond')
    status = Column(TINYINT(1), server_default=text("0"), comment='状态, 0-未知，1-未激活，2-激活')
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='删除标记')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, comment='创建时间')
    updated_at = Column(DateTime, comment='更新时间')


class YzyVoiTerminalToDesktops(Base, BaseModelCtrl):
    __tablename__ = "yzy_voi_terminal_to_desktops"

    # id = Column(INTEGER(11), primary_key=True)
    # uuid = Column(String(64), nullable=False)
    # terminal_uuid = Column(String(64), nullable=False)
    # desktop_uuid = Column(String(64), nullable=False)
    # current = Column(INTEGER(11), nullable=False, default=0)

    id = Column(INTEGER(11), primary_key=True, comment='终端与桌面组的关联表')
    uuid = Column(String(64), nullable=False)
    terminal_uuid = Column(String(64), nullable=False, comment='终端uuid')
    group_uuid = Column(String(64), nullable=False, comment='分组uuid')
    desktop_group_uuid = Column(String(64), nullable=False, comment='桌面组uuid')
    terminal_mac = Column(String(20), nullable=False, comment='终端MAC地址')
    desktop_is_dhcp = Column(INTEGER(11), nullable=False, default=0, comment='dhcp: 1-自动 0-静态')
    desktop_ip = Column(String(16), nullable=False, comment='桌面IP')
    desktop_mask = Column(String(16), nullable=False, comment='桌面IP子网掩码')
    desktop_gateway = Column(String(16), nullable=False, comment='桌面IP网关')
    desktop_dns1 = Column(String(16), nullable=False, comment='桌面DNS1')
    desktop_dns2 = Column(String(16), default="", comment='桌面DNS2')
    desktop_status = Column(INTEGER(11), nullable=False, default=0, comment='0-离线 1-在线')
    desktop_is_sent = Column(INTEGER(11), nullable=False, default=0, comment='桌面是否已经下发标志 0-未下发 1-已下发')
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='删除标记')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, comment='创建时间')
    updated_at = Column(DateTime, comment='更新时间')


class YzyVoiDesktopGroup(Base, BaseModelCtrl):

    __tablename__ = 'yzy_voi_desktop_group'
    id = Column(INTEGER(11), primary_key=True)
    uuid = Column(String(64), nullable=False)
    name = Column(String(64), nullable=False)
    owner_id = Column(INTEGER(11), default=0)
    group_uuid = Column(String(64), nullable=False)
    template_uuid = Column(String(64), nullable=False)
    # template = relationship("YzyVoiTemplate", backref="desktop_of_voi_template")
    os_type = Column(String(64), default='windows_7_x64')
    sys_restore = Column(INTEGER(11), nullable=False, default=True)
    data_restore = Column(INTEGER(11), nullable=False, default=True)
    sys_reserve_size = Column(INTEGER(11), nullable=False, default=0)
    data_reserve_size = Column(INTEGER(11), nullable=False, default=0)
    prefix = Column(String(128), default='PC')
    use_bottom_ip = Column(INTEGER(1), default=1)
    ip_detail = Column(TEXT)
    active = Column(INTEGER(1), default=0)
    default = Column(INTEGER(1), default=0)
    show_info = Column(INTEGER(1), default=0)
    auto_update = Column(INTEGER(1), default=0)
    diff_mode = Column(INTEGER(1), default=1)
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='删除标记')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, comment='创建时间')
    updated_at = Column(DateTime, comment='更新时间')


class YzyVoiDeviceInfo(Base, BaseModelCtrl):

    __tablename__ = 'yzy_voi_device_info'
    id = Column(INTEGER(11), primary_key=True)
    uuid = Column(String(64), nullable=False)
    type = Column(String(32), nullable=False, default='data')
    device_name = Column(String(32), nullable=False, default='')
    image_id = Column(String(64))
    instance_uuid = Column(String(64), nullable=False)
    boot_index = Column(INTEGER(11), nullable=False, default=-1)
    disk_bus = Column(String(32), default='virtio')
    source_type = Column(String(32), default='file')
    source_device = Column(String(32), default='disk')
    size = Column(INTEGER(11), default=0)
    section = Column(BIGINT(20), default=0)
    used = Column(Float, default=0)
    progress = Column(INTEGER(11), default=0)
    upload_path = Column(String(255), default='')
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='删除标记')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, comment='创建时间')
    updated_at = Column(DateTime, comment='更新时间')


class YzyHaInfo(Base, BaseModelCtrl):
    __tablename__ = "yzy_ha_info"

    id = Column(INTEGER(11), primary_key=True)
    uuid = Column(String(64), nullable=False)
    vip = Column(String(20), nullable=False)
    netmask = Column(String(20), nullable=False)
    quorum_ip = Column(String(20), nullable=False)
    sensitivity = Column(INTEGER(11), nullable=False)
    master_ip = Column(String(20), nullable=False)
    backup_ip = Column(String(20), nullable=False)
    master_nic = Column(String(32), nullable=False)
    backup_nic = Column(String(32), nullable=False)
    master_nic_uuid = Column(String(64), nullable=False)
    backup_nic_uuid = Column(String(64), nullable=False)
    master_uuid = Column(String(64), nullable=False)
    backup_uuid = Column(String(64), nullable=False)
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='删除标记')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, comment='创建时间')
    updated_at = Column(DateTime, comment='更新时间')


class YzyVoiTerminalPerformance(Base, BaseModelCtrl):
    __tablename__ = "yzy_voi_terminal_performance"

    id = Column(INTEGER(11), primary_key=True, comment='voi终端性能表')
    uuid = Column(String(64), nullable=False, comment='uuid')
    terminal_uuid = Column(String(64), nullable=False, comment='终端uuid')
    terminal_mac = Column(String(32), comment='终端mac地址')
    cpu_ratio = Column(Float(4), comment='运行cpu速率')
    network_ratio = Column(Float(4), comment='网络速率')
    memory_ratio = Column(Float(4), comment='内存占有率')
    cpu_temperature = Column(Float(4), comment='cpu温度')
    hard_disk = Column(Float(4), comment='硬盘占有率')
    cpu = Column(TEXT, comment='cpu信息')
    memory = Column(TEXT, comment='内存信息')
    network = Column(TEXT, comment='网络信息')
    hard = Column(TEXT, comment='硬盘信息')
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='删除标记')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, comment='创建时间')
    updated_at = Column(DateTime, comment='更新时间')


class YzyVoiTerminalHardWare(Base, BaseModelCtrl):
    __tablename__ = "yzy_voi_terminal_hard_ware"

    id = Column(INTEGER(11), primary_key=True, comment='voi终硬件记录表')
    uuid = Column(String(64), nullable=False, comment='uuid')
    terminal_uuid = Column(String(64), nullable=False, comment='终端uuid')
    terminal_mac = Column(String(32), comment='终端mac地址')
    content = Column(TEXT, comment='硬件变更详情')
    deleted = Column(INTEGER(11), nullable=False, server_default=text("0"), comment='删除标记')
    deleted_at = Column(DateTime, comment='删除时间')
    created_at = Column(DateTime, comment='创建时间')
    updated_at = Column(DateTime, comment='更新时间')