from yzy_server.database.models import *
from yzy_server.database import model_query
from common import constants
import datetime as dt


def get_node_by_uuid(node_uuid):
    node = model_query(YzyNodes).filter_by(uuid=node_uuid).first()
    return node


def get_node_by_name(name):
    node = model_query(YzyNodes).filter_by(hostname=name).first()
    return node


def get_node_by_ip(ipaddr):
    node = model_query(YzyNodes).filter_by(ip=ipaddr).first()
    return node


def get_nodes_by_uuids(node_uuids):
    """
    :param node_uuids:
    :return:
    """
    _tmp = []
    for i in node_uuids:
        if i: _tmp.append(i)
    if _tmp:
        nodes = model_query(YzyNodes).filter(YzyNodes.uuid.in_(_tmp)).all()
    else:
        nodes = model_query(YzyNodes).all()
    return nodes


def get_node_by_pool_uuid(pool_uuid):
    nodes = model_query(YzyNodes).filter_by(resource_pool_uuid=pool_uuid).all()
    return nodes


def get_controller_node():
    node = model_query(YzyNodes).filter(YzyNodes.type.in_([constants.ROLE_MASTER_AND_COMPUTE,
                                                           constants.ROLE_MASTER])).first()
    return node


def get_controller_image():
    nic = model_query(YzyNodeNetworkInfo, YzyInterfaceIp.ip).join(YzyNodes).join(YzyInterfaceIp). \
        filter(YzyNodes.type.in_([constants.ROLE_MASTER_AND_COMPUTE, constants.ROLE_MASTER])). \
        filter(YzyInterfaceIp.is_image == 1).first()
    return nic


def get_template_sys_storage():
    storage = model_query(YzyNodeStorages).filter(YzyNodeStorages.role.contains(str(constants.TEMPLATE_SYS))).first()
    return storage


def get_template_data_storage():
    storage = model_query(YzyNodeStorages).filter(YzyNodeStorages.role.contains(str(constants.TEMPLATE_DATA))).first()
    return storage


def get_instance_sys_storage():
    storage = model_query(YzyNodeStorages).filter(YzyNodeStorages.role.contains(str(constants.INSTANCE_SYS))).first()
    return storage


def get_instance_data_storage():
    storage = model_query(YzyNodeStorages).filter(YzyNodeStorages.role.contains(str(constants.INSTANCE_DATA))).first()
    return storage


def add_server_node(values):
    if 'status' not in values:
        values['status'] = 'shutdown'
    node = YzyNodes()
    node.update(values)
    db.session.add(node)
    db.session.flush()


def get_node_with_all(item):
    nodes = model_query(YzyNodes).filter_by(**item).all()
    return nodes


def get_node_with_first(item):
    nodes = model_query(YzyNodes).filter_by(**item).first()
    return nodes


def get_node_storage_all(item):
    storages = model_query(YzyNodeStorages).filter_by(**item).all()
    return storages


def get_service_by_node_uuid(node_uuid):
    nodes = model_query(YzyNodeServices).filter_by(node_uuid=node_uuid).all()
    return nodes


def get_service_by_uuid(service_uuid):
    service = model_query(YzyNodeServices).filter_by(uuid=service_uuid).first()
    return service


def get_service_by_name(service_name):
    service = model_query(YzyNodeServices).filter_by(name=service_name).first()
    return service


def get_node_manage_nic_name(node_uuid):
    networks = model_query(YzyNodeNetworkInfo).filter_by(node_uuid=node_uuid).all()
    for nic in networks:
        interface = model_query(YzyInterfaceIp).filter_by(nic_uuid=nic.uuid).first()
        if interface and interface.is_manage:
            return interface.name
    return None


def add_monitor_half_min(values):
    node_monitor_data = YzyMonitorHalfMin()
    node_monitor_data.update(values)
    db.session.add(node_monitor_data)
    db.session.flush()


def clear_monitor_half_min(last_days):
    now_datatime = dt.datetime.now()
    model_query(YzyMonitorHalfMin).filter(
        YzyMonitorHalfMin.node_datetime < (now_datatime - dt.timedelta(days=last_days))).delete()
