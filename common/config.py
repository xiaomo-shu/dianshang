import os
from threading import RLock
from configparser import ConfigParser
from . import constants

# CONF_PATH = os.path.join(constants.CONFIG_PATH, "{name}", "{name}.ini")

DEFAULT_CONFIG = [
    # Section: [addresses]
    ('addresses', [
        ('server_bind', '0.0.0.0:50000', 'the server bind host and port'),
        ('compute_bind', '0.0.0.0:50001', 'the compute bind host and port'),
        ('monitor_bind', '0.0.0.0:50002', 'the monitor bind host and port'),
        ('terminal_bind', '0.0.0.0:50003', 'the terminal bind host and port'),
        ('voi_terminal_bind', '0.0.0.0:50005', 'the voi terminal bind host and port'),
        ('upgrade_bind', '0.0.0.0:50008', 'the upgrade bind host and port'),
        ('workers', '12', 'the default workers'),
        ('sqlalchemy_database_uri', 'mysql+mysqlconnector://root:123qwe,.@localhost:3306/yzy_kvm_db?charset=utf8',
         'the db connect info')
    ],
     ),

    # Section: [libvirt]
    ('libvirt', [
        # ('instances_path', '/var/lib/yzy_kvm/instances/', 'The path for instance storage'),
        # ('data_path', '/var/lib/yzy_kvm/datas/', 'The path for data disk storage'),
        ('virt_type', 'kvm', 'the hypervisor type'),
        ('connection_uri', 'qemu:///system', 'the libvirt connect host address')
    ],
     ),

    # Section: [vnc]
    ('vnc', [
        ('enabled', 'True', 'enable vnc or not'),
        ('keymap', 'en-us', 'the keymap'),
        ('server_listen', '0.0.0.0', '')
    ],
     ),

    # Section: [spice]
    ('spice', [
        ('enabled', 'True', 'enable spice or not'),
        ('agent_enabled', 'True', 'enable spice agent or not'),
        ('keymap', 'en-us', 'the keymap'),
        ('server_listen', "0.0.0.0", '')
    ],
     ),

    # Section: [terminal]
    ('terminal', [
        ('soft_dir', '/opt/terminal/soft/', 'terminal soft directory'),
        ('log_dir', '/opt/terminal/log/', 'terminal log directory'),
        ('patch_dir', '/opt/terminal/patch/', 'terminal patch directory')
    ],
     ),

    # Section: [license]
    ('license', [
        ('sn', '', 'the license sn number'),
        ('org_name', '', 'the license company')
    ],
     ),

    ('company', [
        ('name', '湖南云之翼云管理平台', '平台名称'),
        ('title', '湖南云之翼云管理平台', '平台标题'),
        ('logo', '/opt/logo.png', 'the logo of the company')
    ],
     )
]


class Section(object):
    cfg = None
    section = None
    _opts = {}

    def __init__(self, cfg, section, opts=None):
        self.cfg = cfg
        self.section = section
        opts = opts or []
        for opt, value in opts:
            self._opts[opt] = value

    def __getattr__(self, name):
        if name in self._opts:
            return self._opts[name]
        with self.cfg._lock:
            self.cfg.read_from_file()
            return self.cfg.get(self.section, name)

        # raise AttributeError("Illegal attribute %s" % name)

    def __setattr__(self, name, value):
        if name in self._opts:
            self._opts[name] = value
            self.cfg.set(self.section, name, value)
            return
        if hasattr(self, name):
            object.__setattr__(self, name, value)
            return

    def get_by_default(self, name, default=None):
        if name in self._opts:
            return self._opts[name]
        else:
            self._opts[name] = default
            return default


class MemConfig(ConfigParser):
    """
    缓存在内存中的配置文件
    修改实时写入文件与内存
    为减少文件读写次数
    """
    #创建字典接受数据
    _section_objs = {}

    def __init__(self, default_config):
        ConfigParser.__init__(self)

        self._lock = RLock()
        self.cfg_file = constants.CONFIG_PATH
        self.default_config = default_config
        if not os.path.exists(self.cfg_file):
            self.create_default_file()
        else:
            self.read_from_file()

    def __getattr__(self, name):
        if name in self._section_objs:
            return self._section_objs[name]
        elif name in self._sections:
            self._section_objs[name] = Section(self, name,
                                               self._sections[name].items())
            return self._section_objs[name]

        raise AttributeError("Illegal attribute %s" % name)

    def create_default_file(self):
        dir_name = os.path.dirname(self.cfg_file)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        for s_name, opts in self.default_config:
            self.add_section(s_name)
            for o_name, value, _ in opts:
                self.set(s_name, o_name, value)

        self.write_to_file()

    def write_to_file(self):
        """
        不要改实现方式，需要执行fsync函数防止关机时丢失写入
        """
        fd = open(self.cfg_file, "w")
        self.write(fd)
        fd.flush()
        os.fsync(fd.fileno())
        fd.close()

    def read_from_file(self):
        self.read(self.cfg_file)

    def merger(self, default):
        for section, options in default.items():
            if not self.has_section(section):
                self.add_section(section)

            for option in options:
                if not self.has_option(section, option[0]):
                    self.set(section, option[0], option[1])

    def update_config(self):
        """
        更新配置文件
        将默认配置文件与现有配置文件合并
        """
        params = dict(DEFAULT_CONFIG)
        self.merger(params)
        self.write_to_file()


class FileOp(object):

    def __init__(self, file_path, open_mode=''):
        self.file_path = file_path
        self.open_mode = open_mode

    def exist_file(self):
        if not os.path.exists(self.file_path):
            return False

        ret = os.path.isfile(self.file_path)
        return ret

    def read(self):
        if self.open_mode == '':
            self.open_mode = 'r'
        with open(self.file_path, self.open_mode) as fid:
            content = fid.read()
        return content

    def write(self, content):
        if self.open_mode == '':
            self.open_mode = 'w'
        with open(self.file_path, self.open_mode) as fid:
            fid.write(content)
            fid.flush()
            os.fsync(fid.fileno())
            fid.close()

    def readlines(self):
        if self.open_mode == '':
            self.open_mode = 'r'
        with open(self.file_path, self.open_mode) as fid:
            content_lines = fid.readlines()
        return content_lines

    def write_with_endline(self, content):
        with open(self.file_path, self.open_mode) as fid:
            fid.write(content)
            fid.write('\n')
            fid.flush()
            os.fsync(fid.fileno())
            fid.close()


SERVER_CONF = MemConfig(DEFAULT_CONFIG)
