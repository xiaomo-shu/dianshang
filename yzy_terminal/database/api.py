from yzy_terminal.database.models import *
from yzy_terminal.database import BaseTableCtrl


class TerminalStatus:
    ONLINE = '1'
    OFFLINE = '0'


class YzyTerminalTableCtrl(BaseTableCtrl):
    def __init__(self, db):
        super(YzyTerminalTableCtrl, self).__init__(db)

    def add_terminal(self, values):
        terminal = YzyTerminal()
        terminal.update(values)
        self.db.session.add(terminal)
        self.db.session.commit()

    def delete_terminal_by_mac(self, mac):
        qry = self.model_query(YzyTerminal).filter_by(mac=mac)
        qry.delete()
        self.db.session.commit()

    def update_terminal_by_mac(self, **kwargs):
        kwargs['updated_at'] = datetime.datetime.utcnow()
        self.model_query(YzyTerminal).filter_by(mac=kwargs['mac']).update(kwargs)
        self.db.session.commit()

    def reset_group_uuid(self, group_uuid):
        update_data = {
            'updated_at': datetime.datetime.utcnow(),
            'group_uuid': None
        }
        self.model_query(YzyTerminal).filter_by(group_uuid=group_uuid).update(update_data)
        self.db.session.commit()

    def select_terminal_by_mac(self, mac):
        qry = self.model_query(YzyTerminal).filter_by(mac=mac)
        return qry.first()

    def select_terminal_by_group_uuid(self, group_uuid):
        return self.model_query(YzyTerminal).filter_by(group_uuid=group_uuid)

    def select_all_terminal(self):
        qry = self.model_query(YzyTerminal).filter_by()
        return qry.all()

    def reset_all_terminal_offline(self):
        self.model_query(YzyTerminal).update({'status': TerminalStatus.OFFLINE})
        self.db.session.commit()

    def select_all_online_terminal(self):
        qry = self.model_query(YzyTerminal).filter_by(status=TerminalStatus.ONLINE)
        self.db.session.commit()
        return qry.all()

    def update_terminal_by_macs(self, mac_list, status):
        updated_at = datetime.datetime.utcnow()
        for mac in mac_list:
            self.model_query(YzyTerminal).filter_by(mac=mac).update(
                {'updated_at': updated_at, 'status': status}
            )
        self.db.session.commit()
