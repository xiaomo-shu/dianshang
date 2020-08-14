from yzy_terminal_agent.database.models import *
from yzy_terminal_agent.database import BaseTableCtrl


class YzyVoiTerminalTableCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyVoiTerminalTableCtrl, self).__init__(db)

    def add_terminal(self, values):
        terminal = YzyVoiTerminal()
        terminal.update(values)
        self.db.session.add(terminal)
        self.db.session.commit()

    def delete_terminal_by_mac(self, mac):
        qry = self.model_query(YzyVoiTerminal).filter_by(mac=mac)
        terminal_uuid = qry.first().uuid
        qry.delete()
        self.db.session.commit()
        return terminal_uuid

    def update_terminal_by_mac(self, **kwargs):
        kwargs['updated_at'] = datetime.datetime.utcnow()
        self.model_query(YzyVoiTerminal).filter_by(mac=kwargs['mac']).update(kwargs)
        self.db.session.commit()

    def reset_group_uuid(self, group_uuid):
        update_data = {
            'updated_at': datetime.datetime.utcnow(),
            'group_uuid': None
        }
        self.model_query(YzyVoiTerminal).filter_by(group_uuid=group_uuid).update(update_data)
        self.db.session.commit()

    def select_terminal_by_mac(self, mac):
        qry = self.model_query(YzyVoiTerminal).filter_by(mac=mac)
        return qry.first()

    def select_terminal_by_group_uuid(self, group_uuid):
        return self.model_query(YzyVoiTerminal).filter_by(group_uuid=group_uuid)

    def select_all_terminal(self):
        return self.model_query(YzyVoiTerminal).filter_by()

    def reset_all_terminal_offline(self):
        self.model_query(YzyVoiTerminal).update({'status': '0'})
        self.db.session.commit()

    def add_torrent_task(self, values):
        pass


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
        qry_node = self.model_query(YzyNode).filter_by(type=1).first()
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
        qry = self.model_query(YzyVoiTorrentTask).filter_by(torrent_id=torrent_id)
        return qry.first()

    def select_all_task(self):
        return self.model_query(YzyVoiTorrentTask).filter(YzyVoiTorrentTask.status.in_([0,1]),
                                                          YzyVoiTorrentTask.deleted==False).all()

    def update_task_values(self, task, values):
        task.update(values)
        self.db.session.add(task)
        self.db.session.commit()


class YzyVoiTerminalToDesktopsCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyVoiTerminalToDesktopsCtrl, self).__init__(db)

    def get_terminal_to_desktop(self, terminal_uuid, desktop_uuid):
        qry = self.model_query(YzyVoiTerminalToDesktops).filter_by(terminal_uuid=terminal_uuid,
                                                                   desktop_group_uuid=desktop_uuid).first()
        return qry

    def delete_all_bind_by_terminal(self, terminal_uuid):
        qry = self.model_query(YzyVoiTerminalToDesktops).filter_by(terminal_uuid=terminal_uuid)
        qry.delete()
        self.db.session.commit()

    def update_task_values(self, task, values):
        task.update(values)
        self.db.session.add(task)
        self.db.session.commit()

