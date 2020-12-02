from yzy_server.database.models import *
from yzy_server.database import model_query, many_update, many_update_by_in
from common import constants


def create_instance_template(values):
    template = YzyInstanceTemplate()
    template.update(values)
    db.session.add(template)
    db.session.flush()
    return template


def create_group(values):
    group = YzyGroup()
    group.update(values)
    db.session.add(group)
    db.session.flush()


def create_group_user(values):
    user = YzyGroupUser()
    user.update(values)
    db.session.add(user)
    db.session.flush()


def create_desktop(values):
    desktop = YzyDesktop()
    desktop.update(values)
    db.session.add(desktop)
    db.session.flush()


def create_personal_desktop(values):
    desktop = YzyPersonalDesktop()
    desktop.update(values)
    db.session.add(desktop)
    db.session.flush()


def create_random_desktop(values):
    desktop = YzyRandomDesktop()
    desktop.update(values)
    db.session.add(desktop)
    db.session.flush()


def create_instance(values):
    desktop = YzyInstances()
    desktop.update(values)
    db.session.add(desktop)
    db.session.flush()


def create_device(values):
    desktop = YzyInstanceDeviceInfo()
    desktop.update(values)
    db.session.add(desktop)
    db.session.flush()


def create_group_user_session(values):
    session = YzyGroupUserSession()
    session.update(values)
    db.session.add(session)
    db.session.flush()


def insert_with_many(orm, values):
    db.session.execute(orm.__table__.insert(), values)
    db.session.flush()


def get_instance_template(template_uuid):
    instance_template = model_query(YzyInstanceTemplate).filter_by(uuid=template_uuid).first()
    return instance_template


def get_voi_instance_template(template_uuid):
    instance_template = model_query(YzyVoiTemplate).filter_by(uuid=template_uuid).first()
    return instance_template


def get_voi_devices_with_all(item):
    device = model_query(YzyVoiDeviceInfo).filter_by(**item).all()
    return device

def get_voi_operate_with_all(item):
    return model_query(YzyVoiTemplateOperate).filter_by(**item).all()

def get_template_version(template_uuid):
    version = model_query(YzyInstanceTemplate.version).filter_by(uuid=template_uuid).first()
    if version:
        return version[0]


def get_template_mac():
    macs = list()
    items = model_query(YzyInstanceTemplate.mac).all()
    for item in items:
        macs.append(item[0])
    return macs


def get_voi_template_mac():
    macs = list()
    items = model_query(YzyVoiTemplate.mac).all()
    for item in items:
        macs.append(item[0])
    return macs


def get_instance_mac():
    macs = list()
    items = model_query(YzyInstances.mac).all()
    for item in items:
        macs.append(item[0])
    return macs


def get_template_ipaddr():
    ips = list()
    items = model_query(YzyInstanceTemplate.bind_ip).all()
    for item in items:
        if item[0] and item[0] not in ips:
            ips.append(item[0])
    return ips


def get_voi_template_ipaddr():
    ips = list()
    items = model_query(YzyVoiTemplate.bind_ip).all()
    for item in items:
        if item[0] and item[0] not in ips:
            ips.append(item[0])
    return ips


def get_personal_ipaddr(subnet_uuid):
    ips = list()
    personal_desktops = model_query(YzyPersonalDesktop).filter_by(subnet_uuid=subnet_uuid).all()
    for desktop in personal_desktops:
        instances = model_query(YzyInstances).filter_by(desktop_uuid=desktop.uuid).all()
        for instance in instances:
            if instance.ipaddr and instance.ipaddr not in ips:
                ips.append(instance.ipaddr)
    return ips


def get_education_ipaddr(subnet_uuid):
    ips = list()
    education_desktops = model_query(YzyDesktop).filter_by(subnet_uuid=subnet_uuid).all()
    for desktop in education_desktops:
        instances = model_query(YzyInstances).filter_by(desktop_uuid=desktop.uuid).all()
        for instance in instances:
            if instance.ipaddr and instance.ipaddr not in ips:
                ips.append(instance.ipaddr)
    return ips


def get_desktop_by_uuid(desktop_uuid):
    desktop = model_query(YzyDesktop).filter_by(uuid=desktop_uuid).first()
    return desktop


def get_instance_by_desktop(desktop_uuid):
    instances = model_query(YzyInstances).filter_by(desktop_uuid=desktop_uuid).all()
    return instances

def get_instance_by_desktop_and_node(desktop_uuid, host_uuid):
    instances = model_query(YzyInstances).filter_by(desktop_uuid=desktop_uuid, host_uuid=host_uuid, status=constants.STATUS_ACTIVE).all()
    return instances


def get_instance_by_desktop_first_alloc(desktop_uuid):
    instance = model_query(YzyInstances).filter_by(desktop_uuid=desktop_uuid, allocated=0).order_by("id").first()
    return instance


def get_devices_by_instance(instance_uuid):
    devices = model_query(YzyInstanceDeviceInfo).filter_by(instance_uuid=instance_uuid).all()
    return devices


def get_devices_with_first(item):
    device = model_query(YzyInstanceDeviceInfo).filter_by(**item).first()
    return device


def get_devices_modify_with_first(item):
    device = model_query(YzyDeviceModify).filter_by(**item).first()
    return device


def get_devices_with_all(item):
    device = model_query(YzyInstanceDeviceInfo).filter_by(**item).all()
    return device


def get_devices_modify_with_all(item):
    device = model_query(YzyDeviceModify).filter_by(**item).all()
    return device


def get_desktop_with_all(item):
    desktops = model_query(YzyDesktop).filter_by(**item).all()
    return desktops


def get_desktop_with_first(item):
    desktop = model_query(YzyDesktop).filter_by(**item).first()
    return desktop


def get_desktop_order_by_order_num(item):
    desktops = model_query(YzyDesktop).filter_by(**item).order_by(YzyDesktop.order_num.desc()).first()
    return desktops


def get_desktop_with_all_by_uuids(uuids):
    desktops = model_query(YzyDesktop).filter(YzyDesktop.uuid.in_(uuids)).all()
    return desktops


def get_desktop_with_all_by_groups(group_uuids):
    desktops = model_query(YzyDesktop).filter(YzyDesktop.group_uuid.in_(group_uuids)).all()
    return desktops


def get_group_with_first(item):
    group = model_query(YzyGroup).filter_by(**item).first()
    return group


def get_group_with_all(item):
    groups = model_query(YzyGroup).filter_by(**item).all()
    return groups


def get_group_user_with_first(item):
    user = model_query(YzyGroupUser).filter_by(**item).first()
    return user


def get_group_user_with_all(item):
    users = model_query(YzyGroupUser).filter_by(**item).all()
    return users


def get_group_user_session_first(item):
    session = model_query(YzyGroupUserSession).filter_by(**item).first()
    return session


def get_template_with_all(item):
    templates = model_query(YzyInstanceTemplate).filter_by(**item).all()
    return templates


def get_template_by_uuid_first(item):
    try:
        template = model_query(YzyInstanceTemplate).filter_by(**item).first()
        return template
    except Exception as e:
        return None


def get_voi_template_with_all(item):
    templates = model_query(YzyVoiTemplate).filter_by(**item).all()
    return templates


def get_voi_template_by_uuids(uuids):
    templates = model_query(YzyVoiTemplate).filter(YzyVoiTemplate.uuid.in_(uuids)).all()
    return templates


def get_instance_with_all(item):
    instances = model_query(YzyInstances).filter_by(**item).all()
    return instances


def get_instance_all_by_uuids(uuids):
    templates = model_query(YzyInstances).filter(YzyInstances.uuid.in_(uuids)).all()
    return templates


def get_instance_all_by_terminal_ips(ips):
    templates = model_query(YzyInstances).filter(YzyInstances.terminal_ip.in_(ips)).all()
    return templates


def get_instance_all(item, read_deleted='yes'):
    instances = model_query(YzyInstances, read_deleted=read_deleted).filter_by(**item).all()
    return instances


def get_instance_first(item):
    instance = model_query(YzyInstances).filter_by(**item).first()
    return instance


def get_delete_instance_with_first(item):
    instance = model_query(YzyInstances, read_deleted='only').filter_by(**item).first()
    return instance


def get_random_desktop_with_all(item):
    desktops = model_query(YzyRandomDesktop).filter_by(**item).all()
    return desktops


def get_random_desktop_with_first(item):
    desktop = model_query(YzyRandomDesktop).filter_by(**item).first()
    return desktop


def get_personal_desktop_with_first(item):
    desktop = model_query(YzyPersonalDesktop).filter_by(**item).first()
    return desktop


def get_personal_desktop_with_all(item):
    desktops = model_query(YzyPersonalDesktop).filter_by(**item).all()
    return desktops


def get_personal_desktop_order_by_order_num(item):
    desktops = model_query(YzyPersonalDesktop).filter_by(**item).order_by(YzyPersonalDesktop.order_num.desc()).first()
    return desktops


def get_personal_desktop_all_by_uuids(uuids):
    desktops = model_query(YzyPersonalDesktop).filter(YzyPersonalDesktop.uuid.in_(uuids)).all()
    return desktops


def get_instance_with_first(item):
    instance = model_query(YzyInstances).filter_by(**item).first()
    return instance


def get_instance_max_terminal_id(item):
    instance = model_query(YzyInstances.terminal_id).filter_by(**item).order_by(YzyInstances.terminal_id.desc()).first()
    if instance:
        return instance.terminal_id
    return 0


def get_user_random_instance_with_all(item):
    desktops = model_query(YzyUserRandomInstance).filter_by(**item).all()
    return desktops


def create_user_random_instance(values):
    random_instance = YzyUserRandomInstance()
    random_instance.update(values)
    db.session.add(random_instance)
    db.session.flush()


def get_terminal_with_all(item):
    terminals = model_query(YzyTerminal).filter_by(**item).all()
    return terminals


def create_course_schedule_many(values_list):
    for values in values_list:
        course_schedule = YzyCourseSchedule()
        course_schedule.update(values)
        db.session.add(course_schedule)
    db.session.flush()


def create_course_template(values):
    course_template = YzyCourseTemplate()
    course_template.update(values)
    db.session.add(course_template)
    db.session.flush()


def create_course_many(values_list):
    for values in values_list:
        course = YzyCourse()
        course.update(values)
        db.session.add(course)
    db.session.flush()


def create_term(values):
    term = YzyTerm()
    term.update(values)
    db.session.add(term)
    db.session.flush()


def get_course_schedule_with_all(item):
    return model_query(YzyCourseSchedule).filter_by(**item).all()


def get_course_schedule_with_first(item):
    return model_query(YzyCourseSchedule).filter_by(**item).first()


def get_course_template_with_first(item):
    return model_query(YzyCourseTemplate).filter_by(**item).first()


def get_course_template_with_all(item):
    return model_query(YzyCourseTemplate).filter_by(**item).all()


def get_course_with_all(item):
    return model_query(YzyCourse).filter_by(**item).all()


def get_course_with_first(item):
    return model_query(YzyCourse).filter_by(**item).first()


def get_term_with_first(item):
    return model_query(YzyTerm).filter_by(**item).first()


def get_term_with_all(item):
    return model_query(YzyTerm).filter_by(**item).all()


def update_course_schedule_many(value_dict, item):
    """
    批量更新yzy_course_schedule
    :param value_dict: 更新内容字典
    :param item: 对哪些记录进行批量更新的过滤条件
    :return: 批量更新成功的数量
    """
    return many_update(value_dict, YzyCourseSchedule, **item)


def get_distinct_course_template_uuids_by_course_schedule(item):
    """
    查询yzy_course_schedule表中不同的course_template_uuid值
    :param item: 查询yzy_course_schedule的过滤条件
    :return: [("0d86933a-b3d0-42ef-83b0-d0aad7ca1a7f", ), ("2f3f0d3e-aaed-480e-aa4c-7dc6b91d025f", ), ...]
    """
    return model_query(YzyCourseSchedule.course_template_uuid).filter_by(**item).distinct().all()


def get_distinct_course_template_uuids_by_course(item):
    """
    查询yzy_course表中不同的course_template_uuid值
    :param item: 查询yzy_course的过滤条件
    :return: [("0d86933a-b3d0-42ef-83b0-d0aad7ca1a7f", ), ("2f3f0d3e-aaed-480e-aa4c-7dc6b91d025f", ), ...]
    """
    return model_query(YzyCourse.course_template_uuid).filter_by(**item).distinct().all()


def get_distinct_course_schedule_week_nums(item):
    """
    查询yzy_course_schedule表中不同的week_num值
    :param item: 查询yzy_course_schedule的过滤条件
    :return: [(1, ), (2, ), ...]
    """
    return model_query(YzyCourseSchedule.week_num).filter_by(**item).distinct().all()


def delete_course_schedule_many(item):
    """
    批量删除yzy_course_schedule
    :param item: 对哪些记录进行批量删除的过滤条件
    :return: 批量删除成功的数量
    """
    return many_update({"deleted": True, "deleted_at": datetime.datetime.utcnow()}, YzyCourseSchedule, **item)


def delete_course_template_many_by_uuids(in_list):
    """
    批量删除yzy_course_template
    :param in_list: 对uuid在in_list范围内的记录进行批量删除
    :return: 批量删除成功的数量
    """
    return many_update_by_in(
        value_dict={"deleted": True, "deleted_at": datetime.datetime.utcnow()},
        model=YzyCourseTemplate,
        field_obj=YzyCourseTemplate.uuid,
        in_list=in_list
    )


def delete_course_many_by_course_template_uuids(in_list):
    """
    批量删除yzy_course
    :param in_list: 对course_template_uuid在in_list范围内的记录进行批量删除
    :return: 批量删除成功的数量
    """
    return many_update_by_in(
        value_dict={"deleted": True, "deleted_at": datetime.datetime.utcnow()},
        model=YzyCourse,
        field_obj=YzyCourse.course_template_uuid,
        in_list=in_list
    )
