import datetime
import logging
# from flask_sqlalchemy.
from yzy_server.extensions import db
from flask_login import UserMixin
from common.utils import create_md5
from werkzeug.security import generate_password_hash, check_password_hash


logger = logging.getLogger(__name__)


class TimestampMixin(object):
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class SoftDeleteMixin(object):
    deleted_at = db.Column(db.DateTime)
    deleted = db.Column(db.Integer, default=0)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    @property
    def is_deleted(self):
        return self.deleted

    def soft_delete(self):
        """Mark this object as deleted."""
        self.deleted = True
        self.deleted_at = datetime.datetime.utcnow()
        try:
            # 如果有db.session.add会导致报错， 'xx' is already attached to session 'xx'
            # db.session.add(self)
            db.session.flush()
        except Exception as e:
            logger.error("soft delete error:%s", e)

    def soft_update(self):
        try:
            db.session.flush()
        except Exception as e:
            logger.error("flush error:%s", e)
            raise e

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in values.items():
            setattr(self, k, v)
        self.soft_update()

    def dict(self):
        item_list = []
        for k, v in self.__dict__.items():
            if not k[0] == '_':
                if type(v) == datetime.datetime:
                    v = datetime.datetime.strftime(v, '%Y-%m-%d %H:%M:%S')
                item_list.append((k, v))

        joined = dict(item_list)
        return joined


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    locale = db.Column(db.String(20))
    # items = database.relationship('Item', back_populates='author', cascade='all')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_json(self):
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "locale": self.locale
        }

# CREATE TABLE `yzy_admin_user` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '管理员用户id',
#   `username` varchar(32) NOT NULL COMMENT '账号',
#   `password` varchar(64) NOT NULL COMMENT '密码',
#   `last_login` datetime NOT NULL COMMENT '上次登录时间',
#   `login_ip` varchar(20) NOT NULL DEFAULT '' COMMENT '登录ip',
#   `real_name` varchar(64) NOT NULL DEFAULT '' COMMENT '真实姓名',
#   `role_id` bigint(11) NOT NULL COMMENT '角色id',
#   `email` varchar(100) NOT NULL DEFAULT '' COMMENT 'email',
#   `is_superuser` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否为超级管理员，0-否，1-是',
#   `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否激活，0-否，1-是',
#   `desc` varchar(200) DEFAULT NULL COMMENT '备注',
#   `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标志',
#   `deleted_at` datetime DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   `created_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`) USING BTREE
# ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC


class YzyAdminUser(db.Model, SoftDeleteMixin, TimestampMixin):

    __tablename__ = "yzy_admin_user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32))
    password = db.Column(db.String(64), nullable=False)
    last_login = db.Column(db.DateTime)
    login_ip = db.Column(db.String(20))
    real_name = db.Column(db.String(64))
    role_id = db.Column(db.Integer)
    email = db.Column(db.String(128))
    is_superuser = db.Column(db.Boolean, default=0)
    is_active = db.Column(db.Boolean, default=1)
    desc = db.Column(db.String(200))
    # online = db.Column(db.Boolean, default=0)
    # mac = db.Column(db.String(32))

    def validate_password(self, _password):
        # print(create_md5(_password))
        return self.passwd == _password

    def change_password(self, password):
        self.passwd = create_md5(password)


class YzyResourcePool(db.Model, TimestampMixin, SoftDeleteMixin):

    __tablename__ = 'yzy_resource_pools'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    name = db.Column(db.String(32))
    desc = db.Column(db.String(500))
    default = db.Column(db.Boolean, default=0)
    nodes = db.relationship("YzyNodes", backref="resource_pool_of_node")

    def to_json(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "desc": self.desc,
            "default": self.default,
            "created_at": str(self.created_at)
        }


class YzyVirtualSwitch(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_virtual_switch"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    # uplink = db.relationship("YzyVswitchUplink")
    network = db.relationship("YzyNetworks", backref="virtual_switch_of_network", uselist=False)
    uplinks = db.relationship("YzyVswitchUplink", backref="uplink_of_virtual_switch")

    name = db.Column(db.String(32))
    type = db.Column(db.String(10))
    default = db.Column(db.Integer, default=0)
    desc = db.Column(db.String(100))

    def to_json(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "type": self.type,
            "desc": self.desc
        }


class YzyNetworks(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_networks"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    name = db.Column(db.String(32))
    switch_name = db.Column(db.String(32))
    switch_uuid = db.Column(db.String(64), db.ForeignKey("yzy_virtual_switch.uuid"))
    # virtual_switch = db.relationship("YzyVirtualSwitch", backref="virtual_switch_of_network", uselist=False)
    # company_name = Column(String(32), ForeignKey("company.name"))
    # company = relationship("Company", backref="phone_of_company")
    switch_type = db.Column(db.String(10))
    vlan_id = db.Column(db.Integer)
    default = db.Column(db.Integer, default=0)

    def to_json(self):
        return {
            "uuid": self.uuid,
            "switch_name": self.switch_name,
            "switch_type": self.switch_type,
            "name": self.name,
            "vlan_id": self.vlan_id
        }


class YzySubnets(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_subnets"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    name = db.Column(db.String(32))
    network_uuid = db.Column(db.String(64), db.ForeignKey("yzy_networks.uuid"))
    network = db.relationship("YzyNetworks", backref="subnet_of_network")
    netmask = db.Column(db.String(20))
    gateway = db.Column(db.String(20))
    cidr = db.Column(db.String(20))
    start_ip = db.Column(db.String(20))
    end_ip = db.Column(db.String(20))
    enable_dhcp = db.Column(db.Integer, default=0)
    dns1 = db.Column(db.String(20), default="")
    dns2 = db.Column(db.String(20), default="")
    # deleted = db.Column(db.Integer, default=0)

    def to_json(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "netmask": self.netmask,
            "gateway": self.gateway,
            "start_ip": self.start_ip,
            "end_ip": self.end_ip,
            "dns1": self.dns1,
            "dns2": self.dns2
        }


class YzyNodes(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_nodes"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    ip = db.Column(db.String(20))
    name = db.Column(db.String(64))
    hostname = db.Column(db.String(64))
    server_version_info = db.Column(db.String(64))
    gpu_info = db.Column(db.String(100))
    cpu_info = db.Column(db.String(100))
    mem_info = db.Column(db.String(100))
    resource_pool_uuid = db.Column(db.String(64), db.ForeignKey("yzy_resource_pools.uuid"), default="")
    total_mem = db.Column(db.Float, default=0)
    running_mem = db.Column(db.Float, default=0)
    cpu_utilization = db.Column(db.Float, default=0)
    mem_utilization = db.Column(db.Float, default=0)
    single_reserve_mem = db.Column(db.Integer, default=0)
    total_vcpus = db.Column(db.Integer, default=0)
    running_vcpus = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="shutdown")
    type = db.Column(db.Integer, default=5)
    # uplinks = db.relationship("YzyVswitchUplink", backref="uplink_of_node")

    instance_templates = db.relationship("YzyInstanceTemplate", backref="instance_template_of_node")

    def to_json(self):
        return {
            "uuid": self.uuid,
            "ip": self.ip,
            "hostname": self.hostname,
            "resource_pool_uuid": self.resource_pool_uuid,
            "total_mem": self.total_mem,
            "running_men": self.running_mem,
            "total_vcpus": self.total_vcpus,
            "running_vcpus": self.running_vcpus,
            "status": self.status
        }


class YzyVswitchUplink(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_vswitch_uplink"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    vs_uuid = db.Column(db.String(64), db.ForeignKey("yzy_virtual_switch.uuid"))
    node_uuid = db.Column(db.String(64))
    # virtual_switch = db.relationship("YzyVirtualSwitch", backref="uplink_of_virtual_switch")
    nic_uuid = db.Column(db.String(64))


# class YzyInstanceFlavor(db.Model, SoftDeleteMixin, TimestampMixin):
#     __tablename__ = "yzy_instance_flavor"
#
#     id = db.Column(db.Integer, primary_key=True)
#     uuid = db.Column(db.String(64))
#     name = db.Column(db.String(32))
#     memory = db.Column(db.Integer)
#     cpu = db.Column(db.Integer)
#     system_disk = db.Column(db.Integer)
#     data_disks = db.Column(db.String(200), default='')
#
#     def to_json(self):
#         return {
#             "id": self.id,
#             "uuid": self.uuid,
#             "name": self.name,
#             "memory": self.memory,
#             "cpu": self.cpu,
#             "system_disk": self.system_disk,
#             "data_disks": json.loads(self.data_disks)
#         }


class YzyGroup(db.Model, SoftDeleteMixin, TimestampMixin):

    __tablename__ = "yzy_group"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    group_type = db.Column(db.Integer, nullable=False, default=1)
    enabled = db.Column(db.Boolean, default=1)
    network_uuid = db.Column(db.String(64))
    subnet_uuid = db.Column(db.String(64))
    desc = db.Column(db.String(200))
    start_ip = db.Column(db.String(20))
    end_ip = db.Column(db.String(20))

    def to_json(self):
        return {
            "uuid": self.uuid,
            "name": self.name
        }


class YzyVoiGroup(db.Model, SoftDeleteMixin, TimestampMixin):

    __tablename__ = "yzy_voi_group"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    group_type = db.Column(db.Integer, nullable=False, default=1)
    enabled = db.Column(db.Boolean, default=1)
    dhcp = db.Column(db.Text)
    desc = db.Column(db.String(255))
    start_ip = db.Column(db.String(20))
    end_ip = db.Column(db.String(20))


class YzyGroupUser(db.Model, SoftDeleteMixin, TimestampMixin):

    __tablename__ = "yzy_group_user"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    group_uuid = db.Column(db.String(64), db.ForeignKey("yzy_group.uuid"), nullable=False)
    group = db.relationship("YzyGroup", backref="user_of_group")
    user_name = db.Column(db.String(128), nullable=False)
    passwd = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(255))
    phone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    enabled = db.Column(db.Boolean, default=1)
    online = db.Column(db.Boolean, default=0)
    mac = db.Column(db.String(32))

    def validate_password(self, _password):
        # print(create_md5(_password))
        return self.passwd == create_md5(_password)

    def change_password(self, password):
        self.passwd = create_md5(password)

    def to_json(self):
        return {
            "group_uuid": self.group_uuid,
            "uuid": self.uuid,
            "user_name": self.name,
            "phone": self.phone,
            "email": self.email
        }


class YzyGroupUserSession(db.Model, SoftDeleteMixin, TimestampMixin):

    __tablename__ = "yzy_group_user_session"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64))
    user_uuid = db.Column(db.String(64))
    expire_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class YzyInstanceTemplate(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_template"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    name = db.Column(db.String(32))
    os_type = db.Column(db.String(20))
    owner_id = db.Column(db.String(64))
    pool_uuid = db.Column(db.String(64), db.ForeignKey("yzy_resource_pools.uuid"))
    host_uuid = db.Column(db.String(64), db.ForeignKey("yzy_nodes.uuid"))
    host = db.relationship('YzyNodes', backref=db.backref('host_of_template'))
    network_uuid = db.Column(db.String(64))
    subnet_uuid = db.Column(db.String(64))
    sys_storage = db.Column(db.String(64), db.ForeignKey("yzy_node_storages.uuid"))
    data_storage = db.Column(db.String(64), db.ForeignKey("yzy_node_storages.uuid"))
    bind_ip = db.Column(db.String(20))
    vcpu = db.Column(db.Integer)
    ram = db.Column(db.Float)
    mac = db.Column(db.String(64))
    port_uuid = db.Column(db.String(64))
    # system_disk = db.Column(db.String(254), default='')
    # data_disks = db.Column(db.String(254), default='')
    version = db.Column(db.Integer, default=0)
    classify = db.Column(db.Integer, default=1)
    attach = db.Column(db.String(128), nullable=True)
    desc = db.Column(db.String(200))
    status = db.Column(db.String(20))
    updated_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_json(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "os_type": self.os_type,
            "vcpu": self.vcpus,
            "ram": self.ram,
            "version": self.version,
            "classify": self.classify,
            "desc": self.desc,
            "status": self.status,
            "created_at": str(self.created_at)
        }


class YzyVoiTemplate(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_voi_template"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    name = db.Column(db.String(32))
    desc = db.Column(db.Text)
    os_type = db.Column(db.String(20), default="windows_7_x64")
    owner_id = db.Column(db.Integer, default=1)
    terminal_mac = db.Column(db.String(64), default="")
    host_uuid = db.Column(db.String(64), db.ForeignKey("yzy_nodes.uuid"))
    host = db.relationship('YzyNodes', backref=db.backref('host_of_voi_template'))
    network_uuid = db.Column(db.String(64))
    subnet_uuid = db.Column(db.String(64))
    sys_storage = db.Column(db.String(64), db.ForeignKey("yzy_node_storages.uuid"))
    data_storage = db.Column(db.String(64), db.ForeignKey("yzy_node_storages.uuid"))
    bind_ip = db.Column(db.String(20))
    vcpu = db.Column(db.Integer)
    ram = db.Column(db.Float)
    classify = db.Column(db.Integer, default=1)
    mac = db.Column(db.String(64))
    port_uuid = db.Column(db.String(64))
    version = db.Column(db.Integer, default=0)
    operate_id = db.Column(db.Integer, default=0)
    all_group = db.Column(db.Boolean, default=0)
    attach = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(32))
    updated_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_json(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "os_type": self.os_type,
            "vcpu": self.vcpus,
            "ram": self.ram,
            "version": self.version,
            "classify": self.classify,
            "desc": self.desc,
            "status": self.status,
            "created_at": str(self.created_at)
        }


class YzyVoiTemplateGroups(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_voi_template_to_groups"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    template_uuid = db.Column(db.String(64), nullable=False)
    group_uuid = db.Column(db.String(64), nullable=False)


class YzyVoiTemplateOperate(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_voi_template_operate"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    template_uuid = db.Column(db.String(64))
    op_type = db.Column(db.Integer, default=1)
    remark = db.Column(db.Text)
    exist = db.Column(db.Boolean, default=False)
    version = db.Column(db.Integer, default=0)


class YzyDesktop(db.Model, SoftDeleteMixin, TimestampMixin):

    __tablename__ = "yzy_desktop"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    owner_id = db.Column(db.Integer, default=0)
    group_uuid = db.Column(db.String(64), nullable=False)
    pool_uuid = db.Column(db.String(64), nullable=False)
    template_uuid = db.Column(db.String(64), db.ForeignKey("yzy_template.uuid"), nullable=False)
    template = db.relationship("YzyInstanceTemplate", backref="desktop_of_template")
    network_uuid = db.Column(db.String(64), nullable=False)
    subnet_uuid = db.Column(db.String(64), nullable=False)
    vcpu = db.Column(db.Integer, nullable=False)
    ram = db.Column(db.Float, nullable=False)
    os_type = db.Column(db.String(64), default='windows')
    sys_restore = db.Column(db.Integer, nullable=False, default=True)
    data_restore = db.Column(db.Integer, nullable=False, default=True)
    instance_num = db.Column(db.Integer, default=1)
    prefix = db.Column(db.String(128), default='PC')
    postfix = db.Column(db.Integer, default=1)
    postfix_start = db.Column(db.Integer, default=1)
    order_num = db.Column(db.Integer, default=99)
    active = db.Column(db.Boolean, default=0)


class YzyVoiDesktop(db.Model, SoftDeleteMixin, TimestampMixin):

    __tablename__ = "yzy_voi_desktop_group"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    owner_id = db.Column(db.Integer, default=0)
    group_uuid = db.Column(db.String(64), nullable=False)
    template_uuid = db.Column(db.String(64), db.ForeignKey("yzy_voi_template.uuid"), nullable=False)
    template = db.relationship("YzyVoiTemplate", backref="desktop_of_voi_template")
    os_type = db.Column(db.String(64), default='windows_7_x64')
    sys_restore = db.Column(db.Integer, nullable=False, default=True)
    data_restore = db.Column(db.Integer, nullable=False, default=True)
    sys_reserve_size = db.Column(db.Integer, nullable=False, default=0)
    data_reserve_size = db.Column(db.Integer, nullable=False, default=0)
    prefix = db.Column(db.String(128), default='PC')
    use_bottom_ip = db.Column(db.Boolean, default=1)
    ip_detail = db.Column(db.Text)
    # postfix = db.Column(db.Integer, default=1)
    # postfix_start = db.Column(db.Integer, default=1)
    # order_num = db.Column(db.Integer, default=99)
    active = db.Column(db.Boolean, default=0)
    default = db.Column(db.Boolean, default=0)
    show_info = db.Column(db.Boolean, default=0)
    auto_update = db.Column(db.Boolean, default=0)
    diff_mode = db.Column(db.Integer, default=1)
    # data_disk = db.Column(db.Boolean, default=0)
    # data_disk_size = db.Column(db.Integer, default=0)
    # data_disk_type = db.Column(db.Integer, default=0)


class YzyPersonalDesktop(db.Model, SoftDeleteMixin, TimestampMixin):

    __tablename__ = "yzy_personal_desktop"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    owner_id = db.Column(db.Integer, default=0)
    pool_uuid = db.Column(db.String(64), nullable=False)
    template_uuid = db.Column(db.String(64), db.ForeignKey("yzy_template.uuid"), nullable=False)
    template = db.relationship("YzyInstanceTemplate", backref="personal_desktop_of_template")
    network_uuid = db.Column(db.String(64))
    subnet_uuid = db.Column(db.String(64))
    allocate_type = db.Column(db.Integer, default=1)
    allocate_start = db.Column(db.String(32))
    vcpu = db.Column(db.Integer, nullable=False)
    ram = db.Column(db.Float, nullable=False)
    os_type = db.Column(db.String(64), default='windows')
    sys_restore = db.Column(db.Integer, nullable=False, default=False)
    data_restore = db.Column(db.Integer, nullable=False, default=False)
    instance_num = db.Column(db.Integer, default=1)
    prefix = db.Column(db.String(128), default='PC')
    postfix = db.Column(db.Integer, default=1)
    postfix_start = db.Column(db.Integer, default=1)
    desktop_type = db.Column(db.Integer, default=1)
    group_uuid = db.Column(db.String(64), nullable=True)
    order_num = db.Column(db.Integer, default=99)
    maintenance = db.Column(db.Boolean, nullable=False, default=True)


class YzyRandomDesktop(db.Model, SoftDeleteMixin, TimestampMixin):

    __tablename__ = "yzy_random_desktop"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    desktop_uuid = db.Column(db.String(64), nullable=False)
    group_uuid = db.Column(db.String(64), nullable=False)


# class YzyStaticDesktop(db.Model, SoftDeleteMixin, timestampMixin):
#
#     __tablename__ = "yzy_static_desktop"
#
#     id = db.Column(db.Integer, primary_key=True)
#     uuid = db.Column(db.String(64), nullable=False)
#     desktop_uuid = db.Column(db.String(64), nullable=False)
#     instance_uuid = db.Column(db.String(64), db.ForeignKey("yzy_instances.uuid"), nullable=False)
#     instance = db.relationship('YzyInstances', backref=db.backref('static_of_instance'))
#     user_uuid = db.Column(db.String(64), nullable=False)


class YzyInstances(db.Model, SoftDeleteMixin, TimestampMixin):

    __tablename__ = "yzy_instances"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    # hostname = db.Column(db.String(64), nullable=False)
    # desktop_uuid = db.Column(db.String(64), db.ForeignKey("yzy_desktop.uuid"), nullable=False)
    host_uuid = db.Column(db.String(64), db.ForeignKey("yzy_nodes.uuid"), nullable=False)
    host = db.relationship('YzyNodes', backref=db.backref('host_of_instance'))
    desktop_uuid = db.Column(db.String(64), nullable=False)
    sys_storage = db.Column(db.String(64), db.ForeignKey("yzy_node_storages.uuid"))
    data_storage = db.Column(db.String(64), db.ForeignKey("yzy_node_storages.uuid"))
    classify = db.Column(db.Integer, default=1)
    terminal_id = db.Column(db.Integer, nullable=True)
    terminal_mac = db.Column(db.String(32), nullable=True)
    terminal_ip = db.Column(db.String(32), nullable=True)
    ipaddr = db.Column(db.String(20))
    mac = db.Column(db.String(64), default='00:00:00:00:00:00')
    status = db.Column(db.String(32), default='active')
    port_uuid = db.Column(db.String(64))
    allocated = db.Column(db.Boolean, default=0)
    user_uuid = db.Column(db.String(64), default='')
    spice_token = db.Column(db.String(64))
    spice_port = db.Column(db.String(5))
    spice_link = db.Column(db.Boolean, default=0)
    link_time = db.Column(db.DateTime)
    message = db.Column(db.String(255), default='')
    up_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    # devices = db.relationship("YzyInstanceDeviceInfo", backref="devices")

    def instance_base_info(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "spice_host": self.host.ip if self.host else "",
            "spice_token": self.spice_token,
            "spice_port": self.spice_port
        }


class YzyInstanceDeviceInfo(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_device_info'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(32), nullable=False, default='data')
    device_name = db.Column(db.String(32), nullable=False, default='')
    image_id = db.Column(db.String(64))
    instance_uuid = db.Column(db.String(64), db.ForeignKey("yzy_instances.uuid"), nullable=False)
    boot_index = db.Column(db.Integer, nullable=False, default=-1)
    disk_bus = db.Column(db.String(32), default='virtio')
    source_type = db.Column(db.String(32), default='file')
    source_device = db.Column(db.String(32), default='disk')
    size = db.Column(db.Integer, default=0)
    used = db.Column(db.Float, default=0)


class YzyDeviceModify(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_device_modify'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    template_uuid = db.Column(db.String(64), nullable=False)
    device_name = db.Column(db.String(32))
    boot_index = db.Column(db.Integer)
    origin = db.Column(db.Integer, nullable=False, default='0')
    size = db.Column(db.Integer, default=0)
    used = db.Column(db.Float, default=0)
    state = db.Column(db.Integer, default=0)


class YzyVoiDeviceInfo(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_voi_device_info'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(32), nullable=False, default='data')
    device_name = db.Column(db.String(32), nullable=False, default='')
    image_id = db.Column(db.String(64))
    instance_uuid = db.Column(db.String(64), db.ForeignKey("yzy_voi_template.uuid"), nullable=False)
    boot_index = db.Column(db.Integer, nullable=False, default=-1)
    disk_bus = db.Column(db.String(32), default='virtio')
    source_type = db.Column(db.String(32), default='file')
    source_device = db.Column(db.String(32), default='disk')
    size = db.Column(db.Integer, default=0)
    section = db.Column(db.BigInteger, default=0)
    used = db.Column(db.Float, default=0)
    diff1_ver = db.Column(db.Integer, default=0)
    diff2_ver = db.Column(db.Integer, default=0)
    progress = db.Column(db.Integer, default=0)
    upload_path = db.Column(db.String(255), default='')


# class YzyVoiDeviceModify(db.Model, SoftDeleteMixin, TimestampMixin):
#     __tablename__ = 'yzy_voi_device_modify'
#     id = db.Column(db.Integer, primary_key=True)
#     uuid = db.Column(db.String(64), nullable=False)
#     template_uuid = db.Column(db.String(64), nullable=False)
#     device_name = db.Column(db.String(32))
#     boot_index = db.Column(db.Integer)
#     origin = db.Column(db.Integer, nullable=False, default='0')
#     size = db.Column(db.Integer, default=0)
#     used = db.Column(db.Float, default=0)
#     state = db.Column(db.Integer, default=0)


class YzyOperationLog(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_operation_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    user_name = db.Column(db.String(255), nullable=False)
    user_ip = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text)
    result = db.Column(db.Text)
    module = db.Column(db.String(255), default='default')


class YzyTaskInfo(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_task_info'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(64), nullable=False)
    image_id = db.Column(db.String(64))
    version = db.Column(db.Integer)
    host_uuid = db.Column(db.String(64), nullable=False)
    context = db.Column(db.String(512), nullable=False)
    progress = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(32), nullable=False)
    step = db.Column(db.Integer, default=0)


class YzyBaseImage(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_base_images'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    path = db.Column(db.String(64), nullable=False)
    md5_sum = db.Column(db.String(64), nullable=False)
    os_type = db.Column(db.String(64), nullable=False)
    os_bit = db.Column(db.String(10))
    pool_uuid = db.Column(db.String(64), nullable=False)
    vcpu = db.Column(db.Integer)
    ram = db.Column(db.Float)
    disk = db.Column(db.Integer)
    size = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.Integer, nullable=False, default=0)


class YzyNodeServices(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_node_services'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    node_uuid = db.Column(db.String(64), db.ForeignKey("yzy_nodes.uuid"), nullable=False)


class YzyNodeNetworkInfo(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_node_network_info'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    nic = db.Column(db.String(32), nullable=False)
    mac = db.Column(db.String(32), nullable=False)
    node_uuid = db.Column(db.String(64), db.ForeignKey("yzy_nodes.uuid"), nullable=False)
    speed = db.Column(db.Integer)
    type = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=0)


class YzyInterfaceIp(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_interface_ip'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    nic_uuid = db.Column(db.String(64), db.ForeignKey("yzy_node_network_info.uuid"), nullable=False)
    nic = db.relationship('YzyNodeNetworkInfo', backref=db.backref('ip_infos'))
    ip = db.Column(db.String(32))
    netmask = db.Column(db.String(32))
    gateway = db.Column(db.String(32), default=0)
    dns1 = db.Column(db.String(32), default=0)
    dns2 = db.Column(db.String(32), default=0)
    is_image = db.Column(db.Boolean, default=0)
    is_manage = db.Column(db.Boolean, default=0)


class YzyNodeStorages(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_node_storages'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    node_uuid = db.Column(db.String(64), db.ForeignKey("yzy_nodes.uuid"), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    # mountpoint = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(64), default='')
    used = db.Column(db.BigInteger, nullable=False)
    free = db.Column(db.BigInteger, nullable=False)
    total = db.Column(db.BigInteger, nullable=False)
    type = db.Column(db.Integer, default=2)


class YzyIso(db.Model, SoftDeleteMixin, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    md5_sum = db.Column(db.String(64))
    desc = db.Column(db.String(64))
    path = db.Column(db.String(200))
    type = db.Column(db.Integer)
    os_type = db.Column(db.String(64), default='other')
    size = db.Column(db.Float)
    status = db.Column(db.Integer)

# CREATE TABLE `yzy_database_back` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '数据库备份记录id',
#   `name` varchar(64) NOT NULL COMMENT '备份文件名称',
#   `node_uuid` varchar(64) NOT NULL COMMENT '文件备份的节点',
#   `path` varchar(200) NOT NULL COMMENT '备份文件路径',
#   `size` float NOT NULL COMMENT '备份文件大小，单位：MB',
#   `type` tinyint(1) NOT NULL DEFAULT '0' COMMENT '备份类型，0-自动备份，1-手动备份',
#   `deleted` bigint(11) NOT NULL DEFAULT '0' COMMENT '删除标记',
#   `deleted_at` datetime DEFAULT NULL,
#   `created_at` datetime DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8
#


class YzyDatabaseBack(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_database_back'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    node_uuid = db.Column(db.String(64), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    # mountpoint = db.Column(db.String(128), nullable=False)
    size = db.Column(db.Float, nullable=False)
    type = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=0)
    md5_sum = db.Column(db.String(64), nullable=False)
    # total = db.Column(db.BigInteger, nullable=False)
    # type = db.Column(db.Integer, default=2)


# CREATE TABLE `yzy_crontab_task` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '定时任务id',
#   `uuid` varchar(64) NOT NULL COMMENT 'uuid',
#   `name` varchar(32) NOT NULL COMMENT '定时任务名称',
#   `desc` varchar(200) NOT NULL COMMENT '描述',
#   `type` tinyint(1) NOT NULL COMMENT '类型(0-数据库自动备份，1-桌面定时开机，2-桌面定时关机，3-主机定时关机，4-终端定时关机)',
#   `exec_time` varchar(10) NOT NULL COMMENT '执行时间 xx:xx:00 (时:分)',
#   `cycle` varchar(10) NOT NULL COMMENT '周期，day/week/month',
#   `kwargs` text COMMENT '执行参数',
#   `status` tinyint(1) NOT NULL DEFAULT '0' COMMENT '状态 0 -未启用，1-启用',
#   `deleted` bigint(11) NOT NULL,
#   `deleted_at` datetime DEFAULT NULL,
#   `created_at` datetime DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8

class YzyCrontabTask(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_crontab_task'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    desc = db.Column(db.String(200), default='')
    type = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, default=0)


class YzyCrontabDetail(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_crontab_detail'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    task_uuid = db.Column(db.String(64), nullable=False)
    hour = db.Column(db.Integer, nullable=True)
    minute = db.Column(db.Integer, nullable=True)
    cycle = db.Column(db.String(10), nullable=True)
    values = db.Column(db.Text, nullable=True)
    func = db.Column(db.String(255), nullable=False)
    params = db.Column(db.Text, nullable=True)

# CREATE TABLE `yzy_user_random_instance` (
#   `id` bigint(11) NOT NULL AUTO_INCREMENT COMMENT '终端与随机桌面分配表',
#   `uuid` varchar(64) NOT NULL COMMENT '绑定关系uuid',
#   `user_uuid` varchar(64) NOT NULL COMMENT '用户uuid',
#   `instance_uuid` varchar(64) NOT NULL COMMENT '桌面uuid',
#   `deleted` bigint(11) NOT NULL DEFAULT 0 COMMENT '删除标志',
#   `deleted_at` datetime DEFAULT NULL,
#   `created_at` datetime DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8


class YzyUserRandomInstance(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_user_random_instance'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), unique=True,  nullable=False)
    desktop_uuid = db.Column(db.String(64), db.ForeignKey("yzy_personal_desktop.uuid"), nullable=False)
    desktop = db.relationship('YzyPersonalDesktop', backref=db.backref('random_instance_of_desktop'))
    user_uuid = db.Column(db.String(64), nullable=False)
    instance_uuid = db.Column(db.String(64), db.ForeignKey("yzy_instances.uuid"), nullable=False)
    instance = db.relationship('YzyInstances', backref=db.backref('random_of_instance'))


class YzyTerminal(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_terminal'
    id = db.Column(db.Integer, primary_key=True)
    terminal_id = db.Column(db.Integer, nullable=False)
    mac = db.Column(db.String(25), unique=True,nullable=False)
    ip = db.Column(db.String(15), nullable=False)
    mask = db.Column(db.String(15), nullable=False)
    gateway = db.Column(db.String(15), nullable=False)
    dns1 = db.Column(db.String(15), nullable=False)
    dns2 = db.Column(db.String(15))
    is_dhcp = db.Column(db.Integer, default=0, nullable=False)
    name = db.Column(db.String(256), nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    soft_version = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Integer, default=0, nullable=False)
    register_time = db.Column(db.DateTime)
    conf_version = db.Column(db.String(20), nullable=False)
    setup_info = db.Column(db.String(1024))
    group_uuid = db.Column(db.String(64))
    reserve1 = db.Column(db.String(512))
    reserve2 = db.Column(db.String(512))
    reserve3 = db.Column(db.String(512))


# CREATE TABLE `yzy_voi_desktop_group` (
#   `id` int(11) NOT NULL AUTO_INCREMENT,
#   `uuid` varchar(64) NOT NULL COMMENT '桌面组的uuid',
#   `name` varchar(128) NOT NULL COMMENT '桌面组的名称',
#   `owner_id` int(11) NOT NULL DEFAULT 0 COMMENT '创建者ID',
#   `group_uuid` varchar(64) NOT NULL COMMENT '所属分组',
#   `template_uuid` varchar(64) NOT NULL COMMENT '模板uuid',
#   `os_type` varchar(64) DEFAULT 'windows_7_x64',
#   `sys_restore` tinyint(4) DEFAULT 1 COMMENT '系统盘是否重启还原',
#   `data_restore` tinyint(4) DEFAULT 1 COMMENT '数据盘是否重启还原，大于1代表没有数据盘',
#   `prefix` varchar(128) DEFAULT 'PC' COMMENT '桌面名称的前缀',
#   `postfix` int(11) DEFAULT 1 COMMENT '桌面名称的后缀数字个数',
#   `postfix_start` int(11) DEFAULT 1 COMMENT '桌面名称后缀的起始数字',
#   `active` tinyint(1) DEFAULT 0 COMMENT '是否激活，0-未激活，1-激活',
#   `default` tinyint(1) DEFAULT 0 COMMENT '是否为默认',
#   `show_info` tinyint(1) DEFAULT 0 COMMENT '是否显示桌面信息，0-不显示，1-显示',
#   `auto_update` tinyint(1) DEFAULT 0 COMMENT '是否自动更新桌面，0-否，1-是',
#   `deleted` int(11) NOT NULL DEFAULT 0 COMMENT '删除标记',
#   `deleted_at` datetime DEFAULT NULL COMMENT '删除时间',
#   `created_at` datetime DEFAULT NULL COMMENT '创建时间',
#   `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
#   PRIMARY KEY (`id`) USING BTREE
# ) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC COMMENT='教学桌面组表'

# class YzyVoiDesktopGroup(db.Model, SoftDeleteMixin, TimestampMixin):
#
#     __tablename__ = "yzy_voi_desktop_group"
#
#     id = db.Column(db.Integer, primary_key=True)
#     uuid = db.Column(db.String(64), nullable=False)
#     name = db.Column(db.String(32), nullable=False)
#     owner_id = db.Column(db.Integer, default=0)
#     group_uuid = db.Column(db.String(64), nullable=False)
#     template_uuid = db.Column(db.String(64),nullable=False)
#     os_type = db.Column(db.String(64), default='windows')
#     sys_restore = db.Column(db.Integer, nullable=False, default=True)
#     data_restore = db.Column(db.Integer, nullable=False, default=True)
#     instance_num = db.Column(db.Integer, default=1)
#     prefix = db.Column(db.String(128), default='PC')
#     postfix = db.Column(db.Integer, default=1)
#     postfix_start = db.Column(db.Integer, default=1)
#     active = db.Column(db.Boolean, default=0)
#     default = db.Column(db.Boolean, default=0)
#     show_info = db.Column(db.Boolean, default=0)
#     auto_update = db.Column(db.Boolean, default=0)


class YzyWarningLog(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_warning_log"

    id = db.Column(db.Integer, primary_key=True)
    number_id = db.Column(db.Integer, nullable=False)
    option = db.Column(db.Integer, nullable=False)
    ip = db.Column(db.String(32), nullable=False)
    content = db.Column(db.String(64), nullable=False)


class YzyAuth(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_auth"

    id = db.Column(db.Integer, primary_key=True)
    sn = db.Column(db.String(64), nullable=False)
    organization = db.Column(db.String(255), default='')
    remark = db.Column(db.String(255), default='')


class YzyWarnSetup(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_warn_setup"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer, default=0)
    option = db.Column(db.String(1024), nullable=False)


class YzyVoiTerminalToDesktops(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_voi_terminal_to_desktops'

    id = db.Column(db.Integer, primary_key=True, comment='终端与桌面组的关联表')
    uuid = db.Column(db.String(64), nullable=False)
    terminal_uuid = db.Column(db.String(64), nullable=False, comment='终端uuid')
    group_uuid = db.Column(db.String(64), nullable=False, comment='分组uuid')
    desktop_group_uuid = db.Column(db.String(64), nullable=False, comment='桌面组uuid')
    terminal_mac = db.Column(db.String(20), nullable=False, comment='终端MAC地址')
    desktop_is_dhcp = db.Column(db.Integer, nullable=False, default=0, comment='dhcp: 1-自动 0-静态')
    desktop_ip = db.Column(db.String(16), nullable=False, comment='桌面IP')
    desktop_mask = db.Column(db.String(16), nullable=False, comment='桌面IP子网掩码')
    desktop_gateway = db.Column(db.String(16), nullable=False, comment='桌面IP网关')
    desktop_dns1 = db.Column(db.String(16), nullable=False, comment='桌面DNS1')
    desktop_dns2 = db.Column(db.String(16), default="", comment='桌面DNS2')
    desktop_status = db.Column(db.Integer, nullable=False, default=0, comment='0-离线 1-在线')
    desktop_is_sent = db.Column(db.Integer, nullable=False, default=0, comment='桌面是否已经下发标志 0-未下发 1-已下发')


class YzyVoiTerminalShareDisk(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_voi_terminal_share_disk"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    group_uuid = db.Column(db.String(64), nullable=False)
    disk_size = db.Column(db.Integer, nullable=False)
    restore = db.Column(db.Integer, nullable=False, default=0)
    enable = db.Column(db.Integer, nullable=False, default=0)
    version = db.Column(db.Integer, nullable=False, default=0)


# CREATE TABLE `yzy_voi_share_to_desktops` (
#   `id` BIGINT(11) NOT NULL AUTO_INCREMENT COMMENT '共享盘与桌面组的绑定',
#   `uuid` VARCHAR(64) NOT NULL COMMENT 'uuid',
#   `disk_uuid` VARCHAR(64) NOT NULL COMMENT '共享数据盘uuid',
#   `desktop_uuid` VARCHAR(64) NOT NULL COMMENT '桌面组uuid',
#   `desktop_name` VARCHAR(64) NOT NULL COMMENT '桌面组name',
#   `deleted` BIGINT(11) NOT NULL COMMENT '删除标志',
#   `deleted_at` DATETIME DEFAULT NULL,
#   `created_at` DATETIME DEFAULT NULL,
#   `updated_at` DATETIME DEFAULT NULL,
#   PRIMARY KEY (`id`)
# ) ENGINE=INNODB DEFAULT CHARSET=utf8;


class YzyVoiShareToDesktops(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_voi_share_to_desktops"
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    group_uuid = db.Column(db.String(64), nullable=False)
    disk_uuid = db.Column(db.String(64), nullable=False)
    desktop_uuid = db.Column(db.Integer, nullable=False)
    desktop_name = db.Column(db.Integer, nullable=False)


class YzyVoiTorrentTask(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'yzy_voi_torrent_task'

    id = db.Column(db.Integer, primary_key=True, comment='任务')
    uuid = db.Column(db.String(64), nullable=False, comment='任务uuid')
    torrent_id = db.Column(db.String(64), nullable=False, comment='种子id')
    torrent_name = db.Column(db.String(64), nullable=False, comment='种子名称')
    torrent_path = db.Column(db.String(200), nullable=False, comment='种子路径')
    torrent_size = db.Column(db.Integer, nullable=False, default=0, comment='种子文件大小')
    desktop_name = db.Column(db.String(32), nullable=False, comment='桌面组名称')
    template_uuid = db.Column(db.String(64), nullable=False, comment='对应模板uuid')
    disk_uuid = db.Column(db.String(64), nullable=False, comment='磁盘uuid')
    disk_name = db.Column(db.String(64), nullable=False, comment='磁盘名称')
    disk_size = db.Column(db.Float, nullable=False, comment='磁盘文件大小，单位G')
    terminal_mac = db.Column(db.String(32), nullable=False, comment='终端mac')
    terminal_ip = db.Column(db.String(32), nullable=False, comment='终端ip')
    type = db.Column(db.Integer, nullable=False, comment='任务类型，0-上传，1-下载')
    status = db.Column(db.Integer, nullable=False, default=0, comment='任务状态，0-初始状态，1-进行中，2-完成')
    state = db.Column(db.String(32), nullable=False, default="", comment='任务状态')
    process = db.Column(db.Integer, nullable=False, default=0, comment='任务进度')
    batch_no = db.Column(db.Integer, nullable=False, default=0, comment='任务批次号')
    sum = db.Column(db.Integer, nullable=False, default=1, comment='批次任务总数')
    download_rate = db.Column(db.Integer, nullable=False, default=0, comment='下载速率')
    deleted = db.Column(db.Integer, nullable=False, default=0, comment='删除标志')


class YzyBondNics(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_bond_nics"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    mode = db.Column(db.Integer, nullable=False)
    master_uuid = db.Column(db.String(64), db.ForeignKey("yzy_node_network_info.uuid"), nullable=False)
    master_name = db.Column(db.String(32), nullable=False)
    slave_uuid = db.Column(db.String(64), db.ForeignKey("yzy_node_network_info.uuid"), nullable=False)
    slave_name = db.Column(db.String(32), nullable=False)
    # vs_uplink_uuid = db.Column(db.String(64), nullable=True, default=None)
    node_uuid = db.Column(db.String(64), db.ForeignKey("yzy_nodes.uuid"), nullable=False)


class YzyMonitorHalfMin(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'yzy_monitor_half_min'
    __table_args__ = (
        db.Index('node_uuid_index', 'node_uuid', 'node_datetime', unique=True),
        {'comment': '节点30s监控信息表'}
    )

    id = db.Column(db.Integer, primary_key=True, comment='id')
    node_uuid = db.Column(db.String(64), nullable=False, comment='节点uuid')
    node_datetime = db.Column(db.DateTime, nullable=False, comment='节点监控时间')
    monitor_info = db.Column(db.Text, comment='监控信息json')
    auto = db.Column(db.Integer, default="0", comment='是否为自动补齐，默认补齐为前一条数据')


class YzyHaInfo(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_ha_info"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    vip = db.Column(db.String(20), nullable=False)
    netmask = db.Column(db.String(20), nullable=False)
    quorum_ip = db.Column(db.String(20), nullable=False)
    sensitivity = db.Column(db.Integer, nullable=False)
    master_ip = db.Column(db.String(20), nullable=False)
    backup_ip = db.Column(db.String(20), nullable=False)
    master_nic = db.Column(db.String(32), nullable=False)
    backup_nic = db.Column(db.String(32), nullable=False)
    master_nic_uuid = db.Column(db.String(64), nullable=False)
    backup_nic_uuid = db.Column(db.String(64), nullable=False)
    master_uuid = db.Column(db.String(64), nullable=False)
    backup_uuid = db.Column(db.String(64), nullable=False)
    # ha_enable_status = db.Column(db.Integer, nullable=False)
    # ha_running_status = db.Column(db.Integer, nullable=False)
    # data_sync_status = db.Column(db.Integer, nullable=False)
    # master_net_status = db.Column(db.Integer, nullable=False)
    # backup_net_status = db.Column(db.Integer, nullable=False)
    # master_heartbeat_ip = db.Column(db.String(20), nullable=False)
    # backup_heartbeat_ip = db.Column(db.String(20), nullable=False)
    # heartbeat_netmask = db.Column(db.String(20), nullable=False)


class YzyCourseSchedule(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_course_schedule"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    term_uuid = db.Column(db.String(64), nullable=False)
    group_uuid = db.Column(db.String(64), nullable=False)
    course_template_uuid = db.Column(db.String(64), nullable=False)
    week_num = db.Column(db.Integer, nullable=False)
    course_md5 = db.Column(db.String(64), nullable=False)
    status = db.Column(db.Integer, nullable=False)


class YzyCourseTemplate(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_course_template"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    desktops = db.Column(db.Text, nullable=False)


class YzyCourse(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_course"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    course_template_uuid = db.Column(db.String(64), nullable=False)
    desktop_uuid = db.Column(db.String(64), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)
    course_num = db.Column(db.Integer, nullable=False)


class YzyTerm(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_term"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    start = db.Column(db.String(10), nullable=False)
    end = db.Column(db.String(10), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    break_time = db.Column(db.Integer, nullable=False)
    morning = db.Column(db.String(5), nullable=False)
    afternoon = db.Column(db.String(5), nullable=False)
    evening = db.Column(db.String(5), nullable=False)
    morning_count = db.Column(db.Integer, nullable=False)
    afternoon_count = db.Column(db.Integer, nullable=False)
    evening_count = db.Column(db.Integer, nullable=False)
    course_num_map = db.Column(db.Text, nullable=False)
    weeks_num_map = db.Column(db.Text, nullable=False)
    crontab_task_uuid = db.Column(db.String(64), nullable=False)
    group_status_map = db.Column(db.Text, nullable=False)


class YzyTask(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_task"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    task_uuid = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    type = db.Column(db.Integer, default=0)


class YzyRemoteStorage(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "yzy_remote_storages"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    name = db.Column(db.String(32))
    type = db.Column(db.Integer, default=0)
    server = db.Column(db.String(100))
    used = db.Column(db.BigInteger, nullable=True)
    free = db.Column(db.BigInteger, nullable=True)
    total = db.Column(db.BigInteger, nullable=True)
    allocated = db.Column(db.Boolean, default=0)
    allocated_to = db.Column(db.String(64), db.ForeignKey("yzy_resource_pools.uuid"), nullable=True)
    role = db.Column(db.String(64), default='')


class YzyVoiTerminalPerformance(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_voi_terminal_performance"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    terminal_uuid = db.Column(db.String(64), nullable=False)
    terminal_mac = db.Column(db.String(32))
    cpu_ratio = db.Column(db.Float(4))
    network_ratio = db.Column(db.Float(4))
    memory_ratio = db.Column(db.Float(4))
    cpu_temperature = db.Column(db.Float(4))
    hard_disk = db.Column(db.Float(4))
    cpu = db.Column(db.TEXT)
    memory = db.Column(db.TEXT)
    network = db.Column(db.TEXT)
    hard = db.Column(db.TEXT)


class YzyVoiTerminalHardWare(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = "yzy_voi_terminal_hard_ware"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), nullable=False)
    terminal_uuid = db.Column(db.String(64), nullable=False)
    terminal_mac = db.Column(db.String(32))
    content = db.Column(db.TEXT)
