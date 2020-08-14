from web_manage.yzy_edu_desktop_mgr import models as education_model
from web_manage.yzy_voi_edu_desktop_mgr import models as voi_education_model
from web_manage.yzy_user_desktop_mgr import models as personal_model


def get_template_ipaddr():
    ips = list()
    items = education_model.YzyInstanceTemplate.objects.filter(deleted=False)
    for item in items:
        if item.bind_ip and item.bind_ip not in ips:
            ips.append(item.bind_ip)
    return ips


def get_voi_template_ipaddr():
    ips = list()
    items = voi_education_model.YzyVoiTemplate.objects.filter(deleted=False)
    for item in items:
        if item.bind_ip and item.bind_ip not in ips:
            ips.append(item.bind_ip)
    return ips


def get_personal_ipaddr(subnet_uuid):
    ips = list()
    personal_desktops = personal_model.YzyPersonalDesktop.objects.filter(subnet_uuid=subnet_uuid, deleted=False)
    for desktop in personal_desktops:
        instances = education_model.YzyInstances.objects.filter(desktop_uuid=desktop.uuid, deleted=False)
        for instance in instances:
            if instance.ipaddr and instance.ipaddr not in ips:
                ips.append(instance.ipaddr)
    return ips


def get_education_ipaddr(subnet_uuid):
    ips = list()
    education_desktops = education_model.YzyDesktop.objects.filter(subnet_uuid=subnet_uuid, deleted=False)
    for desktop in education_desktops:
        instances = education_model.YzyInstances.objects.filter(desktop_uuid=desktop.uuid)
        for instance in instances:
            if instance.ipaddr and instance.ipaddr not in ips:
                ips.append(instance.ipaddr)
    return ips


def get_personal_used_ipaddr(subnet_uuid):
    template_ips = get_template_ipaddr()
    voi_ips = get_voi_template_ipaddr()
    education_ips = get_education_ipaddr(subnet_uuid)
    personal_ips = get_personal_ipaddr(subnet_uuid)
    used_ips = template_ips + education_ips + personal_ips + voi_ips
    return list(set(used_ips))
