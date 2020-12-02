from yzy_server.database.models import *
from yzy_server.database import model_query
import datetime as dt


def create_voi_template(values):
    template = YzyVoiTemplate()
    template.update(values)
    db.session.add(template)
    db.session.flush()
    return template


def create_voi_group(values):
    group = YzyVoiGroup()
    group.update(values)
    db.session.add(group)
    db.session.flush()


def create_voi_desktop(values):
    group = YzyVoiDesktop()
    group.update(values)
    db.session.add(group)
    db.session.flush()


def create_template_operate(values):
    operate = YzyVoiTemplateOperate()
    operate.update(values)
    db.session.add(operate)
    db.session.flush()


def create_voi_device(values):
    desktop = YzyVoiDeviceInfo()
    desktop.update(values)
    db.session.add(desktop)
    db.session.flush()


def create_voi_terminal_desktop_bind(values):
    bind = YzyVoiTerminalToDesktops()
    bind.update(values)
    db.session.add(bind)
    db.session.flush()


def delete_voi_terminal_desktops(group_uuid, terminal_mac):
    results = model_query(YzyVoiTerminalToDesktops).filter(YzyVoiTerminalToDesktops.terminal_mac == terminal_mac)\
        .filter(YzyVoiTerminalToDesktops.group_uuid != group_uuid).all()
    for result in results:
        result.soft_delete()


def update_voi_terminal_desktop_info(values):
    update_data = {
        'updated_at': datetime.datetime.utcnow(),
    }
    update_data.update(values)
    desktop_group_uuid = values.get('desktop_group_uuid', None)
    if desktop_group_uuid:
        model_query(YzyVoiTerminalToDesktops).filter_by(desktop_group_uuid=values['desktop_group_uuid'],
                                                        terminal_mac=values['terminal_mac']).update(update_data)
    else:
        model_query(YzyVoiTerminalToDesktops).filter_by(terminal_mac=values['terminal_mac']).update(update_data)


def update_voi_terminal_desktop_bind(desktop_group_uuid, terminal_mac, info):
    update_data = {
        'updated_at': datetime.datetime.utcnow(),
    }
    update_data.update(info)
    model_query(YzyVoiTerminalToDesktops).filter_by(desktop_group_uuid=desktop_group_uuid,
                                                    terminal_mac=terminal_mac).update(update_data)


def create_voi_terminal_share(values):
    share_disk = YzyVoiTerminalShareDisk()
    share_disk.update(values)
    db.session.add(share_disk)
    db.session.flush()


def get_item_with_all(orm, item):
    result = model_query(orm).filter_by(**item).all()
    return result


def get_item_with_first(orm, item):
    result = model_query(orm).filter_by(**item).first()
    return result


def get_monitor_info(node_uuid, hours):
    end_datetime = dt.datetime.now()
    start_datetime = end_datetime - dt.timedelta(hours=hours)
    results = model_query(YzyMonitorHalfMin).filter(
        YzyMonitorHalfMin.node_uuid == node_uuid,
        start_datetime <= YzyMonitorHalfMin.node_datetime <= end_datetime).all()
    return results

