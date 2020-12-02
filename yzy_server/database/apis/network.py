from yzy_server.database.models import *
from yzy_server.database import model_query


def get_networks():
    networks = model_query(YzyNetworks).all()
    return networks


def get_default_network():
    return model_query(YzyNetworks).filter_by(default=1).first()


def get_network_by_uuid(uuid, default=False):
    qry = model_query(YzyNetworks).filter_by(uuid=uuid)
    if default:
        qry = qry.filter_by(default=1)
    network = qry.first()
    return network


def get_network_by_name(network_name, default=False):
    qry = model_query(YzyNetworks).filter_by(name=network_name)
    if default:
        qry = qry.filter_by(default=1)
    network = qry.first()
    return network


def get_subnet_by_uuid(subnet_uuid):
    subnet = model_query(YzySubnets).filter_by(uuid=subnet_uuid).first()
    return subnet


def get_subnet_by_network(network_uuid):
    subnet = model_query(YzySubnets).filter_by(network_uuid=network_uuid).all()
    return subnet


def get_subnet_by_name(subnet_name, network_uuid):
    subnet = model_query(YzySubnets).filter_by(name=subnet_name, network_uuid=network_uuid).first()
    return subnet


def get_virtual_switch_list(item):
    virtual_switchs = model_query(YzyVirtualSwitch).filter_by(**item).all()
    return virtual_switchs


def get_default_virtual_switch():
    return model_query(YzyVirtualSwitch).filter_by(default=1).first()


def get_virtual_switch(uuid, default=False):
    qry = model_query(YzyVirtualSwitch).filter_by(uuid=uuid)
    if default:
        qry = qry.filter_by(default=1)
    virtual_switch = qry.first()
    return virtual_switch


def get_virtual_switch_by_name(name, default=False):
    qry = model_query(YzyVirtualSwitch).filter_by(name=name)
    if default:
        qry = qry.filter_by(default=1)
    virtual_switch = qry.first()
    return virtual_switch


def get_uplinks_all(item):
    uplinks = model_query(YzyVswitchUplink).filter_by(**item).all()
    return uplinks


def get_nics_all(item):
    nics = model_query(YzyNodeNetworkInfo).filter_by(**item).all()
    return nics


def get_nics_first(item):
    nic = model_query(YzyNodeNetworkInfo).filter_by(**item).first()
    return nic


def get_network_all(item):
    networks = model_query(YzyNetworks).filter_by(**item).all()
    return networks


def add_virtual_switch_uplink(values):
    virtual_switch = YzyVswitchUplink()
    virtual_switch.update(values)
    db.session.add(virtual_switch)
    db.session.flush()


def add_virtual_swtich(values):
    vs = YzyVirtualSwitch()
    vs.update(values)
    db.session.add(vs)
    db.session.flush()


def add_network(values):
    network = YzyNetworks()
    network.update(values)
    db.session.add(network)
    db.session.flush()


def add_subnet(values):
    subnet = YzySubnets()
    subnet.update(values)
    db.session.add(subnet)
    db.session.flush()
    return subnet


def get_nic_ips_all(item):
    nic_ips = model_query(YzyInterfaceIp).filter_by(**item).all()
    return nic_ips


def add_nic_ip(values):
    nic_ip = YzyInterfaceIp()
    nic_ip.update(values)
    db.session.add(nic_ip)
    db.session.flush()
    return nic_ip


def get_nic_ip_by_name(name, default=False):
    qry = model_query(YzyInterfaceIp).filter_by(name=name)
    if default:
        qry = qry.filter_by(default=1)
    nic_ip = qry.first()
    return nic_ip


def get_nic_ip_by_uuid(uuid, default=False):
    qry = model_query(YzyInterfaceIp).filter_by(uuid=uuid)
    if default:
        qry = qry.filter_by(default=1)
    nic_ip = qry.first()
    return nic_ip


def get_nic_ip_by_ip(ip):
    return model_query(YzyInterfaceIp).filter_by(ip=ip).first()


def get_interface_by_network(network_uuid, node_uuid):
    net = model_query(YzyNetworks, YzyNodeNetworkInfo.nic).\
        join(YzyVswitchUplink, YzyNetworks.switch_uuid == YzyVswitchUplink.vs_uuid).\
        join(YzyNodeNetworkInfo, YzyVswitchUplink.nic_uuid == YzyNodeNetworkInfo.uuid).\
        filter(YzyNetworks.uuid == network_uuid).\
        filter(YzyVswitchUplink.node_uuid == node_uuid).first()
    return net


def get_network_by_nic(nic_uuid, node_uuid):
    nets = model_query(YzyNetworks).\
        join(YzyVswitchUplink, YzyNetworks.switch_uuid == YzyVswitchUplink.vs_uuid).\
        join(YzyNodeNetworkInfo, YzyVswitchUplink.nic_uuid == YzyNodeNetworkInfo.uuid).\
        filter(YzyVswitchUplink.nic_uuid == nic_uuid). \
        filter(YzyVswitchUplink.node_uuid == node_uuid).all()
    return nets


def add_nic(values):
    nic = YzyNodeNetworkInfo()
    nic.update(values)
    db.session.add(nic)
    db.session.flush()


def add_bond_nics(values):
    bond_nics = YzyBondNics()
    bond_nics.update(values)
    db.session.add(bond_nics)
    db.session.flush()


def get_bond_nics_all(item):
    bond_nics = model_query(YzyBondNics).filter_by(**item).all()
    return bond_nics

def get_bond_nics_first(item):
    bond_nic = model_query(YzyBondNics).filter_by(**item).first()
    return bond_nic

def get_uplinks_first(item):
    uplink = model_query(YzyVswitchUplink).filter_by(**item).first()
    return uplink
