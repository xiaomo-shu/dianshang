import os
from threading import RLock
from configparser import ConfigParser
from . import constants

DEFAULT_CONFIG = [
    # Section: [addresses]
    ('addresses', [
        ('server_bind', '0.0.0.0:50000', 'the server bind host and port'),
        ('compute_bind', '0.0.0.0:50001', 'the compute bind host and port'),
        ('monitor_bind', '0.0.0.0:50002', 'the monitor bind host and port'),
        ('workers', '8', 'the default workers')
    ],
     ),

    # Section: [libvirt]
    ('libvirt', [
        ('instances_path', '/var/lib/yzy_kvm/instances/', 'The path for instance storage'),
        ('data_path', '/var/lib/yzy_kvm/datas/', 'The path for data disk storage'),
        ('virt_type', 'kvm', 'the hypervisor type'),
        ('connection_uri', 'qemu:///system', 'the libvirt connect host address')
    ],
     ),

    # Section: [vnc]
    ('vnc', [
        ('enabled', 'False', 'enable vnc or not'),
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
    _section_objs = {}

    def __init__(self):
        ConfigParser.__init__(self)

        self._lock = RLock()
        self.cfg_file = constants.CONFIG_PATH
        # if not os.path.exists(self.cfg_file):
        #     self.create_default_file()
        # else:
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


SERVER_CONF = MemConfig()
