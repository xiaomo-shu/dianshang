import logging
from common import constants
from yzy_terminal_agent.database.models import *
from yzy_terminal_agent.database import BaseTableCtrl

logger = logging.getLogger(__name__)


class YzyVoiTerminalTableCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyVoiTerminalTableCtrl, self).__init__(db)

    def add_terminal(self, values):
        terminal = YzyVoiTerminal()
        terminal.update(values)
        self.db.session.add(terminal)
        self.db.session.commit()

    def delete_terminal_by_mac(self, mac):
        qry = self.model_query(YzyVoiTerminal).filter_by(mac=mac, deleted=False).first()
        if qry:
            terminal_uuid = qry.uuid
            qry.delete()
            self.db.session.commit()
            return terminal_uuid

    def update_terminal_by_mac(self, **kwargs):
        kwargs['updated_at'] = datetime.datetime.utcnow()
        self.model_query(YzyVoiTerminal).filter_by(mac=kwargs['mac'], deleted=False).update(kwargs)
        self.db.session.commit()

    def update_terminal_status_by_mac(self, **kwargs):
        terminal = self.model_query(YzyVoiTerminal).filter_by(mac=kwargs['mac']).first()
        status = kwargs.get("status", 0)
        if terminal and terminal.status != status:
            kwargs['updated_at'] = datetime.datetime.utcnow()
            terminal.update(kwargs)
            self.db.session.commit()

    def reset_group_uuid(self, group_uuid):
        update_data = {
            'updated_at': datetime.datetime.utcnow(),
            'group_uuid': None
        }
        self.model_query(YzyVoiTerminal).filter_by(group_uuid=group_uuid).update(update_data)
        self.db.session.commit()

    def select_terminal_by_mac(self, mac):
        qry = self.model_query(YzyVoiTerminal).filter_by(mac=mac, deleted=False)
        return qry.first()

    def select_terminal_by_group_uuid(self, group_uuid):
        return self.model_query(YzyVoiTerminal).filter_by(group_uuid=group_uuid, deleted=False)

    def select_all_terminal(self):
        return self.model_query(YzyVoiTerminal).filter_by()

    def reset_all_terminal_offline(self):
        self.model_query(YzyVoiTerminal).update({'status': '0'})
        self.db.session.commit()

    def add_torrent_task(self, values):
        pass

    def update_terminal_status(self, terminal, status):
        terminal.status = status
        self.db.session.add(terminal)
        self.db.session.commit()


class YzyAdminUserTableCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyAdminUserTableCtrl, self).__init__(db)

    def select_by_username(self, username):
        qry = self.model_query(YzyAdminUser).filter_by(username=username)
        return qry.first()


class YzyNetworkIpCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyNetworkIpCtrl, self).__init__(db)

    def select_controller_image_ip(self):
        # 1. get controller uuid
        qry_node = self.model_query(YzyNode).filter(YzyNode.type.in_((1, 3))).first()
        if qry_node and qry_node.uuid:
            controller_uuid = qry_node.uuid
        else:
            return None
        qry_node_network_info = self.model_query(YzyNodeNetworkInfo).filter_by(node_uuid=controller_uuid).all()
        if qry_node_network_info:
            uuid_tuple = tuple([x.uuid for x in qry_node_network_info])
            qry_interface_ip = self.model_query(YzyInterfaceIp).filter(YzyInterfaceIp.nic_uuid.in_(uuid_tuple))\
                .filter_by(is_image=1).filter_by(deleted=0)
            if qry_interface_ip:
                return qry_interface_ip.first()
            else:
                return None
        else:
            return None

# yzy_voi_torrent_task


class YzyVoiTorrentTaskTableCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyVoiTorrentTaskTableCtrl, self).__init__(db)

    def add_task(self, values):
        task = YzyVoiTorrentTask()
        task.update(values)
        self.db.session.add(task)
        self.db.session.commit()

    def select_task_by_torrent_id(self, torrent_id):
        qry = self.model_query(YzyVoiTorrentTask).filter_by(torrent_id=torrent_id, deleted=False)
        return qry.first()

    def select_all_task(self):
        return self.model_query(YzyVoiTorrentTask).filter(YzyVoiTorrentTask.status.in_([0,1]),
                                                          YzyVoiTorrentTask.deleted==False).all()

    def select_upload_task_all(self):
        return self.model_query(YzyVoiTorrentTask).filter(YzyVoiTorrentTask.type==constants.BT_UPLOAD_TASK,
                                                            YzyVoiTorrentTask.deleted==False).all()

    def select_terminal_bt_task(self, terminal_mac, torrent_name):
        return self.model_query(YzyVoiTorrentTask).filter_by(terminal_mac=terminal_mac,torrent_name=torrent_name,
                                                            deleted=False).all()

    def select_terminal_bt_upload_task(self, terminal_mac, torrent_name):
        return self.model_query(YzyVoiTorrentTask).filter_by(
                terminal_mac=terminal_mac,torrent_name=torrent_name,type=constants.BT_UPLOAD_TASK)\
                .order_by(YzyVoiTorrentTask.id.desc()).first()

    def select_terminal_all_task(self, terminal_mac):
        return self.model_query(YzyVoiTorrentTask).filter_by(terminal_mac=terminal_mac, deleted=False).all()

    def delete_tasks(self, tasks):
        for task in tasks:
            task.delete()
            self.db.session.commit()

    def update_task_values(self, task, values):
        task.update(values)
        self.db.session.add(task)
        self.db.session.commit()


class YzyVoiTerminalToDesktopsCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyVoiTerminalToDesktopsCtrl, self).__init__(db)

    def get_terminal_to_desktop(self, terminal_uuid, desktop_uuid):
        qry = self.model_query(YzyVoiTerminalToDesktops).filter_by(terminal_uuid=terminal_uuid,
                                                                   desktop_group_uuid=desktop_uuid, deleted=False).first()
        return qry

    def get_desktop_by_terminal_mac(self, terminal_mac):
        qry = self.model_query(YzyVoiTerminalToDesktops).filter_by(terminal_mac=terminal_mac).all()
        return qry

    def delete_all_bind_by_terminal(self, terminal_uuid):
        qry = self.model_query(YzyVoiTerminalToDesktops).filter_by(terminal_uuid=terminal_uuid, deleted=False)
        qry.delete()
        self.db.session.commit()

    def delete_all_bind_by_terminal_mac(self, terminal_mac):
        qry = self.model_query(YzyVoiTerminalToDesktops).filter_by(terminal_mac=terminal_mac, deleted=False)
        qry.delete()
        self.db.session.commit()

    def update_task_values(self, task, values):
        task.update(values)
        self.db.session.add(task)
        self.db.session.commit()


class YzyVoiDeviceInfoTableCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyVoiDeviceInfoTableCtrl, self).__init__(db)

    def get_device_by_uuid(self, disk_uuid):
        qry = self.model_query(YzyVoiDeviceInfo).filter_by(uuid=disk_uuid,deleted=False).first()
        return qry

    def delete_all_bind_by_terminal(self, terminal_uuid):
        qry = self.model_query(YzyVoiTerminalToDesktops).filter_by(terminal_uuid=terminal_uuid, deleted=False)
        qry.delete()
        self.db.session.commit()

    def update_task_values(self, task, values):
        task.update(values)
        self.db.session.add(task)
        self.db.session.commit()


class YzyVoiDesktopGroupTableCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyVoiDesktopGroupTableCtrl, self).__init__(db)

    def get_desktop_group_by_template(self, template_uuid):
        qry = self.model_query(YzyVoiDesktopGroup).filter_by(template_uuid=template_uuid, deleted=False).first()
        return qry


class YzyHaInfoTableCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyHaInfoTableCtrl, self).__init__(db)

    def get_ha_info_first(self):
        qry = self.model_query(YzyHaInfo).filter_by(deleted=False).first()
        return qry


class YzyTerminalPerformanceCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyTerminalPerformanceCtrl, self).__init__(db)

    def select_performance_to_uuid(self, terminal_uuid):
        qry = self.model_query(YzyVoiTerminalPerformance).filter_by(deleted=False, terminal_uuid=terminal_uuid).first()
        return qry

    def add_performance(self, values):
        performance = YzyVoiTerminalPerformance()
        performance.update(values)
        self.db.session.add(performance)
        self.db.session.commit()

    def update_performance_info(self, task, values):
        task.update(values)
        self.db.session.add(task)
        self.db.session.commit()


class YzyTerminalHardwareCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyTerminalHardwareCtrl, self).__init__(db)

    def add_hard_ware(self, values):
        hard_ware = YzyVoiTerminalHardWare
        hard_ware.update(values)
        self.db.session.add(hard_ware)
        self.db.session.commit()