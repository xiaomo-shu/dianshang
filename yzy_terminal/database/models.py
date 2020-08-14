# coding: utf-8
import datetime
from sqlalchemy import CHAR, Column, DateTime, Index, String, text, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER
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


class YzyTerminal(Base, BaseModelCtrl):
    __tablename__ = 'yzy_terminal'
    __table_args__ = (
        Index('terminal_id_ip_index', 'terminal_id', 'ip'),
    )

    id = Column(INTEGER(11), primary_key=True, comment='记录的唯一编号')
    terminal_id = Column(INTEGER(11), nullable=False, comment='终端序号,不同组可以重复')
    mac = Column(CHAR(25), nullable=False, unique=True, comment='终端MAC地址')
    ip = Column(String(15), nullable=False, comment='终端IP地址')
    mask = Column(String(15), nullable=False, comment='子网掩码')
    gateway = Column(String(15), nullable=False, comment='网关地址')
    dns1 = Column(String(15), nullable=False)
    dns2 = Column(String(15))
    is_dhcp = Column(CHAR(1), nullable=False, server_default=text("'1'"), comment='dhcp: 1-自动 0-静态')
    name = Column(String(256), nullable=False, comment='终端名称')
    platform = Column(String(20), nullable=False, comment='终端CPU架构: arm/x86')
    soft_version = Column(String(50), nullable=False, comment='终端程序版本号: 16.3.8.0')
    status = Column(CHAR(1), nullable=False, server_default=text("'0'"), comment='终端状态: 0-离线 1-在线')
    register_time = Column(DateTime)
    conf_version = Column(String(20), nullable=False, comment='终端配置版本号')
    setup_info = Column(String(1024), comment='终端设置信息:模式、个性化、windows窗口')
    group_uuid = Column(CHAR(64), comment='组UUID，默认NULL表示未分组')
    reserve1 = Column(String(512))
    reserve2 = Column(String(512))
    reserve3 = Column(String(512))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    deleted_at = Column(DateTime)
    deleted = Column(INTEGER(11), default=0)
